from tesseract.sql.ast import Identifier


class GroupStage(object):
    def __init__(self, input_page, offset, field):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(field, Identifier)

        self.input_page = input_page
        self.field = field
        self.offset = offset

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
            "    local value = cjson.encode(row['%s'])" % self.field,

            # Add that value to the hash.
            "    redis.call('HSET', 'group', value, 1)",

            "end",
        ])

        # Sort the unique values.
        #lua.extend([
        #    "redis.call('SORT', 'group')",
        #])

        # All the hash value will now be unique, we just need to put them into
        # an output list.
        lua.extend([
            "local records = redis.call('HKEYS', 'group')",
            "local rowid = 0",
            "for _, data in ipairs(records) do",
            "    local row = {}",
            "    row['%s'] = cjson.decode(data)" % self.field,
            "    redis.call('HSET', 'group_result', tostring(rowid), cjson.encode(row))",
            "    rowid = rowid + 1",
            "end"
        ])

        return ('group_result', '\n'.join(lua), self.offset)
