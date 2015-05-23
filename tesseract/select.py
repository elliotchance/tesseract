import re
import redis
from tesseract import ast
from tesseract import client
from tesseract import index
from tesseract import stage
from tesseract import statement
from tesseract import table


class SelectStatement(statement.Statement):
    """`SELECT` statement.

    Attributes:
      NO_TABLE (Identifier, static) - is used when no table is provided. So
        this:
          SELECT 1
        Is actually equivalent to:
          SELECT 1 FROM __no_table
    """

    NO_TABLE = ast.Identifier('__no_table')

    def __init__(self, table_name, columns, where=None, order=None, group=None,
                 explain=False, limit=None):
        assert isinstance(table_name, ast.Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, ast.Expression)
        assert order is None or isinstance(order, ast.OrderByClause)
        assert group is None or isinstance(group, ast.Identifier)
        assert limit is None or isinstance(limit, ast.LimitClause)
        assert group is None or isinstance(group, ast.Identifier)
        assert isinstance(explain, bool)

        self.table_name = table_name
        self.where = where
        self.columns = columns
        self.order = order
        self.group = group
        self.limit = limit
        self.explain = explain

    def __limit_to_sql(self):
        if self.limit:
            return ' %s' % self.limit

        return ''

    def __order_to_sql(self):
        if self.order:
            return ' %s' % self.order

        return ''

    def __group_to_sql(self):
        if self.group:
            return ' GROUP BY %s' % self.group

        return ''

    def __where_to_sql(self):
        if self.where:
            return ' WHERE %s' % self.where

        return ''

    def __table_to_sql(self):
        if self.table_name != SelectStatement.NO_TABLE:
            return " FROM %s" % self.table_name

        return ''

    def __str__(self):
        r = 'EXPLAIN ' if self.explain else ''
        r += "SELECT %s" % ', '.join([str(col) for col in self.columns])
        r += self.__table_to_sql()
        r += self.__where_to_sql()
        r += self.__group_to_sql()
        r += self.__order_to_sql()
        r += self.__limit_to_sql()

        return r

    def contains_aggregate(self):
        """Tests if any of the expressions in the `SELECT` clause contain
        aggregate expressions.

        """
        for col in self.columns:
            if col.is_aggregate():
                return True

        return False

    def execute(self, result, tesseract):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(tesseract.redis, redis.StrictRedis)

        tesseract.redis.delete('agg')

        select = result.statement
        lua, args, manager = self.compile_select(result, tesseract.redis)

        if select.explain:
            tesseract.redis.delete('explain')
            explain = manager.explain(select.table_name)
            return client.Protocol.successful_response(explain)

        return self.run(
            tesseract.redis,
            select.table_name,
            tesseract.warnings,
            lua,
            args,
            result,
            manager
        )

    def __find_index(self, expression, redis, result, stages):
        """Try and find an index that can be used for the WHERE expression. If
        and index is found it is added to the query plan.

        Returns:
          If an index was found True is returned, else False.
        """
        def is_to_value(e):
            if e.right.value == 'null':
                return [ast.Value(None)]
            if e.right.value == 'true':
                return [ast.Value(True)]
            if e.right.value == 'false':
                return [ast.Value(False)]

            return []

        tn = result.statement.table_name
        rules = {
            '^@I = @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': lambda e: [e.right],
            },
            '^@V. = @I$': {
                'index_name': lambda e: '%s.%s' % (tn, e.right),
                'args': lambda e: [e.left],
            },
            '^@I IS @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': is_to_value,
            },
        }

        signature = expression.where.signature()
        rule = None
        for r in rules.keys():
            if re.match(r, signature):
                rule = r
                break

        if rule:
            index_manager = index.IndexManager.get_instance(redis)
            indexes = index_manager.get_indexes_for_table(str(result.statement.table_name))
            for index_name in indexes:
                # noinspection PyCallingNonCallable
                looking_for = rules[rule]['index_name'](expression.where)
                if redis.hget('indexes', index_name).decode() == looking_for:
                    # noinspection PyCallingNonCallable
                    args = rules[rule]['args'](expression.where)
                    if len(args) > 0:
                        args.insert(0, index_name)
                        stages.add(index.IndexStage, args)
                        return True

        return False

    def __compile_where(self, expression, redis, result, stages):
        """When compiling the WHERE clause we need to do a few things:

        1. Verify the WHERE clause is not impossible. This is when the
           expression will always be false like 'x = null'.

        2. See if there is an available index with __find_index() - hopefully
           there is.

        3. Otherwise we fall back to a full table scan.

        """
        if expression.where:
            if expression.where.signature() == '@I = @Vn':
                stages.add(ImpossibleWhereStage, ())
                return

            index_found = self.__find_index(expression, redis, result, stages)
            if not index_found:
                stages.add(WhereStage, (expression.where,))

    def __compile_group(self, expression, stages):
        if expression.group or expression.contains_aggregate():
            stages.add(GroupStage, (expression.group, expression.columns))

    def __compile_order(self, expression, stages):
        if expression.order:
            stages.add(OrderStage, (expression.order,))

    def __compile_columns(self, expression, stages):
        """Compile the `SELECT` columns."""
        if len(expression.columns) > 1 or str(expression.columns[0]) != '*':
            stages.add(ExpressionStage, (expression.columns,))

    def __compile_limit(self, expression, stages):
        if expression.limit:
            stages.add(LimitStage, (expression.limit,))

    def compile_select(self, result, redis_connection):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis_connection, redis.StrictRedis)

        expression = result.statement
        offset = 2
        args = []

        stages = stage.StageManager(redis_connection)

        self.__compile_where(expression, redis_connection, result, stages)
        self.__compile_group(expression, stages)
        self.__compile_order(expression, stages)
        self.__compile_columns(expression, stages)
        self.__compile_limit(expression, stages)

        lua = """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        lua += stages.compile_lua(offset, expression.table_name)

        return (lua, args, stages)

class ExpressionStage(stage.Stage):
    def __init__(self, input_table, offset, redis, columns):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert isinstance(columns, list)
        self.columns = columns

    def explain(self):
        expressions = ', '.join([str(col) for col in self.columns])
        return {
            "description": "Expressions: %s" % expressions
        }

    def compile_lua(self):
        lua = []
        output_table = table.TransientTable(self.redis)

        # Iterate the page.
        lua.extend([
            self.input_table.lua_iterate(),
            "local tuple = {}",
        ])

        index = 1
        offset = self.offset
        args = []
        for col in self.columns:
            name = "col%d" % index
            if isinstance(col, ast.Identifier):
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
            output_table.lua_add_lua_record('tuple'),
            self.input_table.lua_end_iterate()
        ])

        return (output_table, '\n'.join(lua), offset)

class GroupStage(stage.Stage):
    def __init__(self, input_table, offset, redis, field, columns):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert field is None or isinstance(field, ast.Identifier)
        assert isinstance(columns, list)

        self.field = field
        self.columns = columns
        self.lua = []
        self.output_table = table.TransientTable(redis)

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
        assert isinstance(expression, ast.Expression)

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


class ImpossibleWhereStage(stage.Stage):
    def explain(self):
        return {
            "description": "WHERE clause will never return records"
        }

    def compile_lua(self):
        return (table.TransientTable(self.redis), '', self.offset)


class LimitStage(stage.Stage):
    def __init__(self, input_table, offset, redis, limit):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert isinstance(limit, ast.LimitClause)
        self.limit = limit

    def explain(self):
        return {
            "description": str(self.limit)
        }

    def compile_lua(self):
        lua = []
        output_table = table.TransientTable(self.redis)

        filter = "counter < %s" % self.limit.limit
        if self.limit.offset is not None:
            filter = "counter >= %s and counter <= %s" % (
                self.limit.offset,
                self.limit.offset.value + self.limit.offset.value
            )

        # Iterate the page for the desired amount of rows.
        lua.extend([
            "local counter = 0",
            self.input_table.lua_iterate(),
            "   if %s then" % filter,
            output_table.lua_add_lua_record('row'),
            "   end",
            "   counter = counter + 1",
            self.input_table.lua_end_iterate(),
        ])

        return (output_table, '\n'.join(lua), self.offset)

class OrderStage(stage.Stage):
    """This OrderStage represents the sorting of a set."""

    def __init__(self, input_table, offset, redis_connection, clause):
        stage.Stage.__init__(self, input_table, offset, redis_connection)
        assert isinstance(clause, ast.OrderByClause)
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
        output_table = table.TransientTable(self.redis)

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

            self.input_table.lua_iterate(),

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
            self.input_table.lua_end_iterate(),
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

class WhereStage(stage.Stage):
    def __init__(self, input_table, offset, redis, where):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert where is None or isinstance(where, ast.Expression)
        self.where = where
        self.output_table = table.TransientTable(redis)

    def explain(self):
        return {
            "description": "Filter: %s" % self.where
        }

    def compile_lua(self):
        lua = []

        # Compile the WHERE into a Lua expression.
        where_expression = self.where if self.where else ast.Value(True)
        where_clause, self.offset, new_args = where_expression.compile_lua(self.offset)

        lua.extend([
            self.input_table.lua_iterate(),
            "    if %s then" % where_clause,
            "        %s" % self.action_on_match(),
            "    end",
            self.input_table.lua_end_iterate(),
        ])

        return (self.output_table, '\n'.join(lua), self.offset)

    def action_on_match(self):
        return self.output_table.lua_add_lua_record('row')
