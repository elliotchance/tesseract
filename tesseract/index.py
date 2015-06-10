"""An index is used to speed up lookup operations. You can expect that these
work exactly the same as any other RDBMS.

Lets run through an example with a table called "mytable". The preceding number
is the record ID which the index references and is non-linear on purpose so that
we don't get confused later::

    10. {"x": 123}
    11. {"x": true}
    15. {"x": "foo"}
    17. {}
    20. {"x": 123}
    23. {"x": 57}

The index is created like::

    CREATE INDEX myindex ON mytable (x)

Unlike most other database systems we need to index different data types in the
same index. To achieve this we need to separate numbers from non-numbers and
maintain a separate index for each respectively.

Lets look at the numbers first. The numbers index is sorted set that uses the
score as the value (could be an integer or float) and value as the record ID::

    57  -> "23"
    123 -> "10"
    123 -> "20"

For the non-numbers index which could contain NULLs, booleans, strings or even
arrays and objects (more on arrays and objects later) we also use a sorted set
but the roles are reversed with the score containing the record ID and the value
is a string.

Now we run into the first minor problem. Redis requires all values in a sorted
set to be unique. This is not an issue for the numbers index since the record ID
is unique in all cases but is is a problem for the non-numbers index.

To get around this we add the record ID to the end of the string::

    11 -> "T:11"
    15 -> "Sfoo:15"
    17 -> "N:17"

The first character is the type::

    N null
    T true
    F false
    S string (followed by the actual string)

The indexes are named with as ``index:mytable:myindex:number`` and
``index:mytable:myindex:nonnumber``. The table name is kept in the key because
an index can only apply to a single table.

Now that we know how indexes are stored we can request back records. The first
and most important step is to determine if the value we are looking up is a
number or a non-number then use the appropriate index.

In the case of a number we can use the Redis ZRANGEBYSCORE command, and for
non-numbers we can use the ZRANGEBYLEX on the non-number index.
"""

import json
import redis
from tesseract import ast
from tesseract import instance
from tesseract import protocol
from tesseract import stage
from tesseract import statement
from tesseract import table


class IndexManager(object):
    """The IndexManager handles the creation, deletion and fetching of indexes
    for tables.

    Attributes:
      _redis (StrictRedis): This is the Redis connection.
      INDEXES_KEY (str): The Redis key that contains all the information about
        all indexes.
    """
    INDEXES_KEY = 'indexes'

    @staticmethod
    def get_instance(redis_connection):
        """This is the correct way to get the instance of the IndexManager. It
        is not guaranteed to be a singleton but it may hold some state that
        allows caching to be more effective.

        Arguments:
          redis_connection (redis.StrictRedis): The Redis connection.

        Returns:
          A new or existing instance of IndexManager.
        """
        assert isinstance(redis_connection, redis.StrictRedis)
        return IndexManager(redis_connection)

    def __init__(self, redis_connection):
        """Internal use only. Use the static method get_instance() to get the
        IndexManager instance.

        Arguments:
          redis_connection (redis.StrictRedis): The Redis connection.
        """
        assert isinstance(redis_connection, redis.StrictRedis)
        self._redis = redis_connection

    def get_indexes_for_table(self, table_name):
        """Fetch all the indexes for a single table.

        Arguments:
          table_name (str): The name of the table to fetch indexes for. This
            table does not need to exist - in this case it will return the same
            thing as a table with no indexes.

        Returns:
          An dictionary of Index objects where the key is the name of the index.
        """
        assert isinstance(table_name, str)

        found_indexes = {}
        for index_name in self._redis.hkeys(self.INDEXES_KEY):
            field = str(self._redis.hget(self.INDEXES_KEY, index_name).decode())
            if field.startswith('%s.' % table_name):
                safe_index_name = str(index_name.decode())
                parts = field.split('.')
                found_indexes[safe_index_name] = Index(
                    self._redis,
                    table_name,
                    safe_index_name,
                    parts[1]
                )

        return found_indexes

    def get_index(self, index_name):
        """Fetch a single index by name.

        Arguments:
          index_name (str): The name of the index.

        Returns:
          An Index object if the index exists, otherwise False.
        """
        assert isinstance(index_name, str)

        index = self._redis.hget(self.INDEXES_KEY, index_name)
        if not index:
            return False

        parts = str(index.decode()).split('.')
        return Index(self._redis, parts[0], index_name, parts[1])

    def create_index(self, index_name, table_name, field):
        """Create an index on a table.

        This will generate the index which may take some time if the table
        contains a lot of data. However, you can guarantee than then this method
        returns the Index will be ready to use.

        Arguments:
          index_name (str): The name of the index must be globally unique across
            all tables and indexes.
          table_name (str): The name of the table to create the index on.
          field (str): The name of the field to index.

        Returns:
          An Index object with the newly created index.
        """
        assert isinstance(index_name, str)
        assert isinstance(table_name, str)
        assert isinstance(field, str)

        index = self.__build_index(field, index_name, table_name)
        self.__register_index(field, index_name, table_name)

        return index

    def drop_index(self, index_name):
        """Drop (delete) an index by name.

        Arguments:
          index_name (str): The name of the index.

        Returns:
          True if the index was dropped. False if the index did not exist.
        """
        assert isinstance(index_name, str)

        index = self.get_index(index_name)
        if index:
            index._drop()

        result = self._redis.hdel(self.INDEXES_KEY, index_name)
        return result == '1'

    def __register_index(self, field, index_name, table_name):
        """Make the index visible to the query planner."""
        value = '%s.%s' % (table_name, field)
        self._redis.hset(self.INDEXES_KEY, index_name, value)

    def __build_index(self, field, index_name, table_name):
        """Build the index now. This may take some time if there are a lot of
        values to index.
        """
        index = Index(self._redis, table_name, index_name, field)
        the_table = table.PermanentTable(self._redis, table_name)

        for data in self._redis.zrange(the_table.redis_key(), 0, -1):
            self.__index_value(data, field, index)

        return index

    def __index_value(self, data, field, index):
        row = json.loads(data.decode())

        try:
            row[field]
        except KeyError:
            # Missing values are to be treated as null.
            row[field] = None

        if row[field] is None or isinstance(row[field], (int, float, bool)):
            index.add_record(row[field], row[':id'])
        else:
            index.add_record(str(row[field]), row[':id'])


class Index(object):
    """Attributes:
      TYPE_NULL (str): Used as the prefix for `null` values in the nonnumber
        index.
      TYPE_TRUE (str): Used as the prefix for `true` values in the nonnumber
        index.
      TYPE_FALSE (str): Used as the prefix for `false` values in the nonnumber
        index.
      TYPE_STRING (str): Used as the prefix for string values in the nonnumber
        index.
      table_name (str): The name of the table this index belongs to.
      index_name (str): The name of the index. This will be globally unique
        across all tables and indexes.
      field_name (str): The name of the field that is in the index.
      _redis (StrictRedis): The Redis connection.

    """
    TYPE_NULL = 'N'
    TYPE_TRUE = 'T'
    TYPE_FALSE = 'F'
    TYPE_STRING = 'S'

    def __init__(self, redis_connection, table_name, index_name, field_name):
        """Initialise a handle to an index. The index does not need to exist and
        can be manipulated in any case.

        Arguments:
          redis_connection (reids.StrictRedis): The Redis connection.
          table_name (str): The name of the table.
          index_name (str): The name of the index.
          field_name (str): The name of the field that is indexed.
        """
        assert isinstance(redis_connection, redis.StrictRedis)
        assert isinstance(table_name, str)
        assert isinstance(index_name, str)
        assert isinstance(field_name, str)

        self._redis = redis_connection
        self.table_name = table_name
        self.index_name = index_name
        self.field_name = field_name

    def add_record(self, value, record_id):
        """Add a record to the index.

        Arguments:
          value (None, int, float, bool or str): The value to be indexed.
          record_id (int): The record ID from the original record.
        """
        assert value is None or isinstance(value, (int, float, bool, str))
        assert isinstance(record_id, int)

        if self.__is_number(value):
            self.__add_number_value(value, record_id)
        else:
            self.__add_nonnumber_value(value, record_id)

    def lua_lookup_exact(self, value):
        """Generate the Lua code to lookup record based on an exact value.

        Arguments:
          value (int, float, bool or str): The value to lookup.

        Returns:
          Lua code that should be assigned to a variable and iterated like:

          >>> index = Index('a', 'b')
          >>> lua = "local records = %s" % index.lua_lookup_exact()
        """
        assert value is None or isinstance(value, (int, float, bool, str))

        if self.__is_number(value):
            return self.__lua_lookup_number_exact(value)

        return self.__lua_lookup_nonnumber_exact(value)

    def _drop(self):
        """This is an internal method and should never be called.

        If you want to drop an index use the IndexManager.drop_index() method.
        """
        self._redis.delete(self.__number_index_key())
        self._redis.delete(self.__nonnumber_index_key())

    def __is_number(self, value):
        """Test if a value should be considered for the "number" index.

        This is mainly to keep the repeating logic in one place and also a
        bool is a subclass of int so we have to be careful with that as well.

        Returns:
          True if this value should be in the number index, otherwise False.
        """
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def __lua_lookup_number_exact(self, value):
        assert isinstance(value, (int, float))
        return "redis.call('ZRANGEBYSCORE', '%s', '%s', '%s')" % (
            self.__number_index_key(),
            value,
            value,
        )

    def __lua_lookup_nonnumber_exact(self, value):
        type = self.__get_type_character(value)
        if type == self.TYPE_STRING:
            type += value

        return "redis.call('ZRANGEBYLEX', '%s', '[%s:', '[%s:Z')" % (
            self.__nonnumber_index_key(),
            type,
            type,
        )

    def __add_number_value(self, value, record_id):
        """Add a number value to the index."""
        self._redis.zadd(self.__number_index_key(), value, record_id)

    def __add_nonnumber_value(self, value, record_id):
        """Add a nonnumber value to the index.

        It is important that they all have the same score (in this case zero)
        otherwise when select the data back with ZRANGEBYLEX it does all sorts
        of crazy things. Fortunately the score is no use to use as we get the
        record ID from the value.
        """
        type = self.__get_type_character(value)
        if isinstance(value, str):
            redis_value = '%s%s:%s' % (type, value, record_id)
        else:
            redis_value = '%s:%s' % (type, record_id)

        self._redis.zadd(self.__nonnumber_index_key(), 0, redis_value)

    def __number_index_key(self):
        """This is the redis key that contains the sorted set of numbers for the
        index.

        Returns:
          A string key.
        """
        return 'index:%s:%s:number' % (self.table_name, self.index_name)

    def __nonnumber_index_key(self):
        """This is the redis key that contains the sorted set of nonnumbers for
        the index.

        Returns:
          A string key.
        """
        return 'index:%s:%s:nonnumber' % (self.table_name, self.index_name)

    def __get_type_character(self, value):
        """When indexing nonnumbers each indexed value must be prefixed with a
        single character for its type. This is explained in more detail in the
        class description.
        """
        if value is None:
            return self.TYPE_NULL

        if value is True:
            return self.TYPE_TRUE

        if value is False:
            return self.TYPE_FALSE

        return self.TYPE_STRING

class CreateIndexStatement(statement.Statement):
    """`CREATE INDEX` statement."""

    def __init__(self, index_name, table_name, field):
        assert isinstance(index_name, ast.Identifier)
        assert isinstance(table_name, ast.Identifier)
        assert isinstance(field, ast.Identifier)

        self.index_name = index_name
        self.table_name = table_name
        self.field = field

    def __str__(self):
        return "CREATE INDEX %s ON %s (%s)" % (
            self.index_name,
            self.table_name,
            self.field
        )

    def execute(self, result, tesseract):
        assert isinstance(result.statement, CreateIndexStatement)
        assert isinstance(tesseract, instance.Instance)

        manager = IndexManager(tesseract.redis)
        manager.create_index(
            str(result.statement.index_name),
            str(result.statement.table_name),
            str(result.statement.field)
        )

        return protocol.Protocol.successful_response()

class DropIndexStatement(statement.Statement):
    """`DROP INDEX` statement."""

    def __init__(self, index_name):
        assert isinstance(index_name, ast.Identifier)
        self.index_name = index_name

    def __str__(self):
        return "DROP INDEX %s" % self.index_name

    def execute(self, result, tesseract):
        assert isinstance(result.statement, DropIndexStatement)
        assert isinstance(tesseract, instance.Instance)

        manager = IndexManager(tesseract.redis)
        manager.drop_index(str(result.statement.index_name))
        return protocol.Protocol.successful_response()

class IndexStage(stage.Stage):
    def __init__(self, input_table, offset, redis, index_name, value):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert isinstance(index_name, str)
        assert isinstance(value, ast.Value)

        self.index_name = index_name
        self.value = value

    def explain(self):
        if self.value.value is None:
            description = 'null'
        else:
            description = 'value %s' % self.value

        return {
            "description": "Index lookup using %s for %s" % (
                self.index_name,
                description
            )
        }

    def compile_lua(self):
        lua = []
        output_table = table.TransientTable(self.redis)
        index_manager = IndexManager(self.redis)
        index = index_manager.get_index(self.index_name)
        the_table = table.PermanentTable(self.redis, index.table_name)

        lua.extend([
            "local records = %s" % index.lua_lookup_exact(self.value.value),
            "for _, data in ipairs(records) do",
            the_table.lua_get_lua_record('data'),
            "local row = cjson.decode(irecords[1])",
            output_table.lua_add_lua_record('row'),
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)
