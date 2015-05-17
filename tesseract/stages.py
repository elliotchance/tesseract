import abc
from tesseract.index import IndexManager
from tesseract.table import *
from tesseract.ast import *


class Stage(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_table, offset, redis):
        assert isinstance(input_table, Table)
        assert isinstance(offset, int)
        assert isinstance(redis, StrictRedis)

        self.input_table = input_table
        self.offset = offset
        self.redis = redis

    @abc.abstractmethod
    def explain(self):
        pass

    def iterate_page(self, lua):
        """Iterate a page and run some lua against each record.

        For each record read from the page there will be several initialized lua
        variables:

          * `rowid` - A unique integer that is an ID for the record. You cannot
            rely on this value staying the same for the same records against
            multiple sets - for instance it may change once or more between each
            stage.
          * `data` - The raw JSON (as a string) that is the record.
          * `row` - The decoded JSON (as a Lua table).

        Arguments:
          lua (list of str): Lua code to be executed for each page.

        """
        assert isinstance(lua, list)

        self.lua.append(self.input_table.lua_iterate(decode=True))
        self.lua.extend(lua)
        self.lua.append("end")

class StageManager(object):
    """The `StageManager` is used to create the plan for the SQL query. This
    query does not have to be a `SELECT`. Once all the stages have been added
    to the manager it is then run which will cause each stage to run
    sequentially using the return value of the last stage as the input page for
    the next stage.

    The first stage must take an input page which in most cases is the input
    table and each of the stages must return a key that points to the location
    of another temporary table that will be fed into the subsequent stage.

    Attributes:
        stages (list of tesseract.engine.stage.stage.Stage): The stages to be
            run. This will be empty when you create a new `StageManager`.

    """
    def __init__(self, redis):
        assert isinstance(redis, StrictRedis)

        self.stages = []
        self.redis = redis

    def add(self, stage_class, args):
        assert isinstance(stage_class, object)
        assert isinstance(args, (list, tuple))

        self.stages.append({
            "class": stage_class,
            "args": args,
        })

    def compile_lua(self, offset, table_name):
        lua = ''
        input_table = PermanentTable(self.redis, str(table_name))
        for stage_details in self.stages:
            stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
            input_table, stage_lua, offset = stage.compile_lua()
            lua += stage_lua + "\n"

        lua += "return '%s'\n" % input_table.table_name
        return lua

    def explain(self, table_name):
        offset = 0
        steps = []

        if len(self.stages) == 0 or self.stages[0]['class'] != IndexStage and \
            self.stages[0]['class'] != ImpossibleWhereStage:
            steps.append({
                "description": "Full scan of table '%s'" % table_name
            })

        input_table = PermanentTable(self.redis, str(table_name))
        for stage_details in self.stages:
            stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
            steps.append(stage.explain())

        return steps

class ExpressionStage(Stage):
    def __init__(self, input_table, offset, redis, columns):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(columns, list)
        self.columns = columns

    def explain(self):
        return {
            "description": "Expressions: %s" % ', '.join([str(col) for col in self.columns])
        }

    def compile_lua(self):
        lua = []
        table = TransientTable(self.redis)

        # Iterate the page.
        lua.extend([
            self.input_table.lua_iterate(decode=True),
            "local tuple = {}",
        ])

        index = 1
        offset = self.offset
        args = []
        for col in self.columns:
            name = "col%d" % index
            if isinstance(col, Identifier):
                name = str(col)

            expression, offset, new_args = col.compile_lua(offset)
            args.extend(new_args)

            if col.is_aggregate():
                lua.append("local temp = tonumber(row['%s'])" % str(col))
                lua.append("if temp == nil then")
                lua.append("    tuple['%s'] = cjson.null" % name)
                lua.append("else")
                lua.append("    tuple['%s'] = temp * 1" % name)
                lua.append("end")
            else:
                lua.append("tuple['%s'] = %s" % (name, expression))

            index += 1

        lua.extend([
            table.lua_add_lua_record('tuple'),
            "end",
        ])

        return (table, '\n'.join(lua), offset)

class GroupStage(Stage):
    def __init__(self, input_table, offset, redis, field, columns):
        Stage.__init__(self, input_table, offset, redis)
        assert field is None or isinstance(field, Identifier)
        assert isinstance(columns, list)

        self.field = field
        self.columns = columns
        self.lua = []
        self.output_table = TransientTable(redis)

    def explain(self):
        return {
            "description": "Grouping by %s" % self.field
        }

    def __unique_group_value(self):
        """The unique group value is a name for the group contain the same
        values.

        Since a query does not need to have a `GROUP BY` clause this effectively
        means that all the rows in the set belong to the same group. So we give
        this master group a `true` value to group on.

        In any case the value is encoded to JSON - this ensure the value is both
        a string and unique across values and equivalent values in different
        data types.

        Returns:
          Lua expression that will setup a variable called `unique_group`.

        """
        unique_group = "cjson.encode(row['%s'])" % self.field
        if self.field is None:
            unique_group = "'true'"

        return "local unique_group = %s" % unique_group

    def __group_name(self, value, expression):
        """Generate a unique key when a query contains multiple expressions.

        As explained in `__lua_args()` a query could contain multiple aggregate
        expressions and we want to keep them independent. Our two possible
        solutions is to maintain a different hash for each expression, or use a
        single hash but have a prefix/suffix to the keys. I chose to use the
        latter separated by a colon.

        Arguments:
          value (str): Must be raw Lua.
          expression (Expression): The expression.

        Returns:
          Lua code to generate the key.

        """
        assert isinstance(value, str)
        assert isinstance(expression, Expression)

        return '%s .. ":%s"' % (value, str(expression))

    def __lua_args(self):
        """Gather up all the aggregate columns in the query and make their
        expressions unique, for example:

            SELECT value, sum(a), sum(a + 2), sum(a) * 2
            FROM some_table

        The unique aggregates would be (in no particular order):

            sum(a)
            sum(a + 2)

        It is important they are unique because we don't want to calculate them
        twice. Even if we didn't care about the performance hit it is still
        critical they are unique because these expressions become the key as we
        aggregate and so multiple expressions would cause all values to be run
        twice through all the aggregate functions.

        """
        unique_aggregates = {}
        for col in self.columns:
            if not col.is_aggregate():
                continue

            aggregate = str(col)
            if aggregate not in unique_aggregates:
                unique_aggregates[aggregate] = col

        lua = []
        for col in unique_aggregates.values():
            lua.append("local group = %s" % self.__group_name('unique_group', col))
            lua.append(col.compile_lua(0)[0])

        return '\n'.join(lua)

    def __group_records(self):
        """Iterate the page and start grouping.

        As we iterate the records we maintain a Redis hash called `group` which
        contains keys that represent JSON strings and a value of `1`.

        """
        self.iterate_page([
            self.__unique_group_value(),
            "redis.call('HINCRBY', 'group', unique_group, 1)",
            self.__lua_args(),
        ])

    def __ensure_single_row(self):
        """If there is no `GROUP BY` clause we must return one row, even if the
        original set did not have any rows.

        """
        self.lua.extend([
            "if %s == 1 then" % self.output_table.lua_get_next_record_id(),
            "  local row = {}",
        ])

        for col in self.columns:
            if not col.is_aggregate():
                continue

            default_value = 0
            if col.function_name in ('min', 'max'):
                default_value = 'cjson.null'

            self.lua.append("row['%s'] = %s" % (str(col), default_value))

        self.lua.extend([
            self.output_table.lua_add_lua_record('row'),
            "end"
        ])

    def iterate_hash_keys(self, page, lua):
        """Iterate the keys of a hash.

        The keys are not guaranteed to come out in any particular order this
        method uses `HKEYS` to fetch the keys. For each key there will be
        several Lua variables exposed:

         * `rowid` - A simple counter (starting at 0) for each key.
         * `data` - The raw JSON string that is the record.

        Arguments:
          page (string): The name of the page to iterate.
          lua (list of str): Lua code to be executed for each page.

        """
        assert isinstance(page, str)
        assert isinstance(lua, list)

        self.lua.extend([
            "local records = redis.call('HKEYS', '%s')" % page,
            "local rowid = 0",
            "for _, data in ipairs(records) do",
        ])

        self.lua.extend(lua)

        self.lua.extend([
            "    rowid = rowid + 1",
            "end"
        ])

    def __extract_expressions(self):
        """Request all the results of the parsed group expressions.

        After all the records have been iterated and each of the expressions
        have been calculating their result along the way. Now we need to fetch
        back those results and put them into a result page.

        """
        lua = [
            "local row = {}",
            "row['%s'] = cjson.decode(data)" % self.field,
        ]

        for col in self.columns:
            if not col.is_aggregate():
                continue

            key = self.__group_name('tostring(data)', col)
            line = "row['%s'] = function_%s_post(tostring(data), %s)" % (
                str(col),
                col.function_name,
                key
            )
            lua.append(line)

        lua.append(self.output_table.lua_add_lua_record('row'))

        self.iterate_hash_keys('group', lua)

    def __clear_buffers(self):
        """Reset (delete) any buffers we will need to carry out this stage."""
        self.lua.append("redis.call('DEL', 'group')")

    def compile_lua(self):
        self.__clear_buffers()
        self.__group_records()
        self.__extract_expressions()
        self.__ensure_single_row()

        return (self.output_table, '\n'.join(self.lua), self.offset)

class IndexStage(Stage):
    def __init__(self, input_table, offset, redis, index_name, value):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(index_name, str)
        assert isinstance(value, Value)

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
        output_table = TransientTable(self.redis)
        index_manager = IndexManager(self.redis)
        index = index_manager.get_index(self.index_name)
        table = PermanentTable(self.redis, index.table_name)

        lua.extend([
            "local records = %s" % index.lua_lookup_exact(self.value.value),
            "for _, data in ipairs(records) do",
            table.lua_get_lua_record('data'),
            "local row = cjson.decode(irecords[1])",
            output_table.lua_add_lua_record('row'),
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)

class LimitStage(Stage):
    def __init__(self, input_table, offset, redis, limit):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(limit, LimitClause)
        self.limit = limit

    def explain(self):
        return {
            "description": str(self.limit)
        }

    def compile_lua(self):
        lua = []
        output_table = TransientTable(self.redis)

        filter = "counter < %s" % self.limit.limit
        skip = 0
        if self.limit.offset is not None:
            filter = "counter >= %s and counter <= %s" % (
                self.limit.offset,
                self.limit.offset.value + self.limit.offset.value
            )
            skip = self.limit.offset.value

        # Iterate the page for the desired amount of rows.
        lua.extend([
            "local counter = 0",
            self.input_table.lua_iterate(decode=True),
            "   if %s then" % filter,
            output_table.lua_add_lua_record('row'),
            "   end",
            "   counter = counter + 1",
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)

class OrderStage(Stage):
    """This OrderStage represents the sorting of a set.

    """
    def __init__(self, input_table, offset, redis, clause):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(clause, OrderByClause)
        self.clause = clause

    def explain(self):
        direction = 'ASC'
        if self.clause.ascending is False:
            direction = 'DESC'
        return {
            'description': 'Sorting by %s (%s)' % (
                self.clause.field_name,
                direction
            )
        }

    def compile_lua(self):
        lua = []
        output_table = TransientTable(self.redis)

        # Clean out sort buffer.
        lua.append(
            "redis.call('DEL', 'order_null', 'order_boolean', 'order_number', 'order_string')"
            "redis.call('DEL', 'order_boolean_sorted', 'order_number_sorted', 'order_string_sorted')"
            "redis.call('DEL', 'order_result')"
            "redis.call('DEL', 'order_boolean_hash', 'order_number_hash', 'order_string_hash')"
        )

        lua.extend([
            # This is for making values unique.
            "local duplicate_number = 1",
            "local duplicate_string = 1",

            self.input_table.lua_iterate(decode=True),

            # The first thing we need to do it get the value that we will be
            # sorting by.
            "    local value = row['%s']" % self.clause.field_name,

            # For not ordering by an array or object is not supported.
            "    if type(value) == 'table' then",
            "       error('ORDER BY used on an array or object.')",

            # When `value` is `nil` then there is no field, or if the field
            # exists but has a value of `cjson.null` - this goes into first
            # category.
            "    elseif value == nil or value == cjson.null then",
            "       redis.call('RPUSH', 'order_null', data)",

            # The second category is for all booleans.
            "    elseif type(value) == 'boolean' then",
            "       if value then",
            "          value = 't'",
            "       else",
            "          value = 'f'",
            "       end",
            "       value = value .. duplicate_number",
            "       duplicate_number = duplicate_number + 1",
            "       redis.call('HSET', 'order_boolean_hash', value, data)",
            "       redis.call('RPUSH', 'order_boolean', value)",

            # The third category is for all numbers.
            "    elseif type(value) == 'number' then",
            "       value = value .. '.00000' .. duplicate_number"
            "       duplicate_number = duplicate_number + 1"
            "       redis.call('HSET', 'order_number_hash', value, data)",
            "       redis.call('RPUSH', 'order_number', value)",

            # The last category is for strings and everything else.
            "    else",
            "       value = value .. ' ' .. duplicate_string"
            "       duplicate_string = duplicate_string + 1"
            "       redis.call('HSET', 'order_string_hash', value, data)",
            "       redis.call('RPUSH', 'order_string', value)",
            "    end",
            "end",
        ])

        desc = ", 'DESC'" if self.clause.ascending is False else ''

        # Sort the values.
        lua.extend([
            "redis.call('SORT', 'order_boolean'%s, 'ALPHA', 'STORE', 'order_boolean_sorted')" % desc,
            "redis.call('SORT', 'order_number'%s, 'STORE', 'order_number_sorted')" % desc,
            "redis.call('SORT', 'order_string'%s, 'ALPHA', 'STORE', 'order_string_sorted')" % desc,
        ])

        lua.extend([
            "local rowid = 0",
        ])

        # Now use the sorted data to construct the result.
        reconstruct = [
            # Start with booleans.
            [
                "local records = redis.call('LRANGE', 'order_boolean_sorted', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = cjson.decode(redis.call('HGET', 'order_boolean_hash', data))",
                output_table.lua_add_lua_record('record'),
                "    rowid = rowid + 1",
                "end"
            ],

            # Now numbers.
            [
                "local records = redis.call('LRANGE', 'order_number_sorted', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = cjson.decode(redis.call('HGET', 'order_number_hash', data))",
                output_table.lua_add_lua_record('record'),
                "    rowid = rowid + 1",
                "end"
            ],

            # Now strings.
            [
                "local records = redis.call('LRANGE', 'order_string_sorted', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = cjson.decode(redis.call('HGET', 'order_string_hash', data))",
                output_table.lua_add_lua_record('record'),
                "    rowid = rowid + 1",
                "end"
            ],

            # `null`s are greater than any non-`null` value so we can append all
            # the `null`s now.
            [
                "local records = redis.call('LRANGE', 'order_null', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = cjson.decode(data)",
                output_table.lua_add_lua_record('record'),
                "    rowid = rowid + 1",
                "end"
            ]
        ]

        # For reverse sort we need to flip all the groups of data backwards as
        # well.
        for sorter in (reversed(reconstruct)
                       if self.clause.ascending is False
                       else reconstruct):
            lua.extend(sorter)

        return (output_table, '\n'.join(lua), self.offset)

class WhereStage(Stage):
    def __init__(self, input_table, offset, redis, where):
        Stage.__init__(self, input_table, offset, redis)
        assert where is None or isinstance(where, Expression)
        self.where = where
        self.output_table = TransientTable(redis)

    def explain(self):
        return {
            "description": "Filter: %s" % self.where
        }

    def compile_lua(self):
        lua = []

        # Compile the WHERE into a Lua expression.
        where_expression = self.where if self.where else Value(True)
        where_clause, self.offset, new_args = where_expression.compile_lua(self.offset)

        lua.extend([
            self.input_table.lua_iterate(decode=True),
            "    if %s then" % where_clause,
            "        %s" % self.action_on_match(),
            "    end",
            "end",
        ])

        return (self.output_table, '\n'.join(lua), self.offset)

    def action_on_match(self):
        return self.output_table.lua_add_lua_record('row')


class ImpossibleWhereStage(Stage):
    def explain(self):
        return {
            "description": "WHERE clause will never return records"
        }

    def compile_lua(self):
        return (TransientTable(self.redis), '', self.offset)

class DeleteStage(WhereStage):
    """The `DeleteStage` works much like the `WhereStage` except when it comes
    across a matching record (or all records if no `WHERE` clause is provided)
    then the record will be removed.

    """
    def action_on_match(self):
        return self.input_table.lua_delete_record("row[':id']")

class UpdateStage(WhereStage):
    def __init__(self, input_page, offset, redis, columns, where):
        WhereStage.__init__(self, input_page, offset, redis, where)
        assert isinstance(columns, list)
        self.columns = columns

    def action_on_match(self):
        lua = []

        for column in self.columns:
            lua.append(
                "row['%s'] = %s" % (column[0], column[1].compile_lua(0)[0])
            )

        lua.extend((
            self.input_table.lua_delete_record("row[':id']"),
            self.input_table.lua_add_lua_record('row'),
        ))

        return '\n'.join(lua)
