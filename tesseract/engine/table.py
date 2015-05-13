import json
import random
from redis import StrictRedis

"""A table represents a permanent or temporary set of records. Table are not
always public, they can also be intermediately steps during a query. This module
provides ways to manipulate tables - abstracted away from Redis.

Tables are stored in Redis as a sorted set. Where the score is an integer
representing the record ID. This presents two problems:

1. Scores in Redis are not required to be unique so it's possible to add a
   record with the same score making it very difficult to remove or manipulate
   a single record.

2. Values (the raw JSON records) must be unique in Redis. It is quite possible
   for records to contain the same data.

To get around both of those issues we set some basic rules for how tables are
stored:

1. Each table has a separate associated key in Redis that acts as a incrementer
   to provide guaranteed unique scores for each row. This is incremented as it's
   needed. However, the table does not need to have a continuous set of IDs
   (such as when records are removed the IDs will also be removed forever.)

2. Each of the records includes a secret key that contains the record ID. For
   example the following record:

   123 -> {"foo": "bar"}

   Is actually stored internally as:

   123 -> {":id": 123, "foo": "bar"}

   This guarantees that the records are unique and also means that the scores do
   not need to be retrieved when records are iterated.

"""

class Table:
    """The base functionality of a table.

    Methods with the `lua_` prefix do not actually perform anything on the
    table, but rather return a Lua string that can be used in a larger Lua
    program.

    Attributes:
      table_name (str): The name of the table. This is used to locate the Redis
        key - but the `table_name` is *not* exactly the Redis key.
      redis (StrictRedis): The Redis connection.

    """
    def __init__(self, redis, table_name):
        assert isinstance(redis, StrictRedis)
        assert isinstance(table_name, str)

        self.redis = redis
        self.table_name = table_name

    def lua_delete_record(self, lua):
        """Generate the Lua to delete a record based on a Lua expression. This
        Lua expression could be a variable.

        """
        assert isinstance(lua, str)

        return "redis.call('ZREMRANGEBYSCORE', '%s', %s, %s)" % (
            self._redis_key(),
            lua,
            lua
        )

    def lua_add_lua_record(self, lua_variable):
        return '\n'.join((
            "%s[':id'] = %s" % (lua_variable, self.lua_get_next_record_id()),
            "redis.call('ZADD', '%s', tostring(%s[':id']), cjson.encode(%s)) " % (
                self._redis_key(),
                lua_variable,
                lua_variable
            )
        ))

    def lua_add_record(self, record):
        """Generate the Lua required to add a new record to the table. Redis
        does not require all the scores to be unique - however to be able to
        delete or retrieve a singe row we need all the scores to be unique so we
        keep a separate atomic counter.

        Arguments:
          record (dict): The record.

        Returns:
          str Lua code.

        """
        assert isinstance(record, dict)

        record[':id'] = self.get_next_record_id()

        return "redis.call('ZADD', '%s', '%s', '%s') " % (
            self._redis_key(),
            record[':id'],
            json.dumps(record)
        )

    def add_record(self, record):
        assert isinstance(record, dict)

        record[':id'] = self.get_next_record_id()
        self.redis.zadd(self._redis_key(), record[':id'], json.dumps(record))

    def lua_iterate(self, decode=False):
        """Generate the Lua required to iterate the records in a table.

        NOTE: This will open the loop, but you must provide the Lua `end`.

        For each record read from the page there will be several initialized Lua
        variables:

          * `data` - The raw JSON (as a string) that is the record.
          * `row` - The decoded row (also containing special keys like ':id')
            only if `decode` is `True`.

        Arguments:
          lua (str): Lua code to be executed for each page.
          decode (bool, optional): If `True` the row will be parsed and a new
            variable `row` will be available.

        """
        zrange = "redis.call('ZRANGE', '%s', '0', '-1')" % self._redis_key()
        lua = "for _, data in ipairs(%s) do " % zrange

        if decode:
            lua += "local row = cjson.decode(data) "

        return lua

    def lua_get_next_record_id(self):
        return "redis.call('INCR', '%s')" % self._redis_record_id_key()

    def get_next_record_id(self):
        return self.redis.incr(self._redis_record_id_key())

    def _redis_key(self):
        """Get the name of the Redis key.

        Returns:
          str

        """
        return 'table:%s' % self.table_name

    def _redis_record_id_key(self):
        """Get the name of the key that holds the incrementer for the next
        record ID. This may not exist.

        """
        return 'table:%s:rowid' % self.table_name

    def __drop_all_indexes(self):
        for index_name in self.redis.hkeys('indexes'):
            prefix = '%s.' % self.table_name
            if str(self.redis.hget('indexes', index_name).decode()).startswith(prefix):
                self.redis.hdel('indexes', index_name)
                self.redis.delete('index:%s' % index_name)

    def drop(self):
        self.__drop_all_indexes()
        self.redis.delete(self._redis_key())
        self.redis.delete(self._redis_record_id_key())

class PermanentTable(Table):
    """Permanent tables must act like SQL tables where changes are always
    consistent.

    """

    def __init__(self, redis, table_name):
        Table.__init__(self, redis, table_name)


class TransientTable(Table):
    """Transient tables are used in the stages of a query and so have these
    restrictions:

    1. They will be automatically deleted when this object is cleaned up (since
       no more references to the table exist).

    2. They can only be used by a single thread (never shared) so there is no
       risk of race conditions.

    3. The name of the table is not required because a random name will be
       generated for the table. You will want to retrieve the table name (to
       pass to future stages) with the `table_name` attribute.

    Since these tables are effectively private for the process that's using them
    and their contents is to be thrown away the the record IDs they generate are
    useful only to themselves. And we do no need to maintain a separate key with
    the next record ID. It is generated and maintained in this instance of the
    class.

    Attributes:
      next_record_id (int): The next record ID to be used. This will increment
        automatically.

    """
    def __init__(self, redis):
        Table.__init__(self, redis, self.__random_table_name())

    def __random_table_name(self):
        """Generate a random table name."""
        return ''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz')
            for _ in range(8)
        )

    def __del__(self):
        self.drop()
