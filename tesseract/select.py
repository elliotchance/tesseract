import redis
from tesseract import ast
from tesseract import protocol
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
        assert isinstance(table_name, (ast.Identifier, ast.AliasExpression))
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

        from tesseract import planner

        tesseract.redis.delete('agg')

        select = result.statement
        query_planner = planner.SelectPlanner(self, tesseract.redis)
        lua, args, manager = query_planner.compile_lua()

        if select.explain:
            tesseract.redis.delete('explain')
            explain = manager.explain(select.table_name)
            return protocol.Protocol.successful_response(explain)

        return self.run(
            tesseract.redis,
            select.table_name,
            tesseract.warnings,
            lua,
            args,
            result,
            manager
        )

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
            if isinstance(col, ast.AliasExpression):
                name = str(col.alias)
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


class NoTableStage(stage.Stage):
    def explain(self):
        return {
            "description": "No table used"
        }

    def compile_lua(self):
        output_table = table.TransientTable(self.redis)
        lua = "local dummy = {}\n" + output_table.lua_add_lua_record('dummy')

        return (output_table, lua, self.offset)


class SubqueryExpression(ast.Expression):
    def __init__(self, select):
        assert isinstance(select, SelectStatement)
        self.select = select

    def __str__(self):
        return '(%s)' % str(self.select)

    def compile_lua(self, offset):
        return ('cjson.null', offset, [])
