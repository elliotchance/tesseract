from tesseract.sql.ast import Identifier, Expression, FunctionCall


class GroupStage(object):
    def __init__(self, input_page, offset, field, columns):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert field is None or isinstance(field, Identifier)
        assert isinstance(columns, list)

        self.input_page = input_page
        self.field = field
        self.offset = offset
        self.columns = columns

    def __group_value(self):
        if self.field is None:
            return "    local group = 'true'"
        return "    local group = cjson.encode(row['%s'])" % self.field

    def __lua_args(self):
        lua = ''
        for col in self.columns:
            assert isinstance(col, Expression)
            if col.is_aggregate():
                lua += col.compile_lua(0)[0]
        return lua

    def compile_lua(self):
        lua = []

        # Clean out group buffer.
        lua.append("redis.call('DEL', 'group', 'group_result')")

        lua.extend([
            "local records = hgetall('%s')" % self.input_page,

            # Iterate the page and start grouping.
            "for rowid, data in pairs(records) do",

            # Decode the record.
            "    local row = cjson.decode(data)",

            # The first thing we need to do it get the value that we will be
            # grouping by and encode that as a JSON string. This will guarantee
            # values are strings and unique.
            self.__group_value(),

            # Add that value to the hash.
            "    redis.call('HSET', 'group', group, 1)",

            self.__lua_args(),

            "end",
        ])

        # All the hash values will now be unique, we just need to put them into
        # an output list.
        lua.extend([
            "local records = redis.call('HKEYS', 'group')",
            "local rowid = 0",
            "for _, data in ipairs(records) do",
            "    local row = {}",
            "    row['%s'] = cjson.decode(data)" % self.field,
        ])

        for col in self.columns:
            lua.append("    row['count(*)'] = redis.call('HGET', 'count', tostring(data))")

        lua.extend([
            "    redis.call('HSET', 'group_result', tostring(rowid), cjson.encode(row))",
            "    rowid = rowid + 1",
            "end"
        ])

        # If there is no GROUP BY clause we must return one row, even if the
        # original set did not have any rows.
        lua.extend([
            "if rowid == 0 then",
            "    local row = {}",
            "    row['count(*)'] = 0",
            "    redis.call('HSET', 'group_result', tostring(rowid), cjson.encode(row))",
            "end"
        ])

        return ('group_result', '\n'.join(lua), self.offset)
