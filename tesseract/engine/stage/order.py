class OrderStage:
    def __init__(self, input_page, offset, field):
        self.input_page = input_page
        self.field = field
        self.offset = offset

    def compile_lua(self):
        lua = []

        # Clean out sort buffer.
        lua.append(
            "redis.call('DEL', 'order', 'order_index', 'order_index_sorted', 'order_result')"
        )

        # Iterate the page.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % self.input_page,
            "for i, data in ipairs(records) do",
            "    local row = cjson.decode(data)",
            "    redis.call('HSET', 'order', row['%s'], data)" % self.field,
            "    redis.call('LPUSH', 'order_index', row['%s'])" % self.field,
            "end"
        ])

        # Sort the record.
        lua.append("redis.call('SORT', 'order_index', 'STORE', 'order_index_sorted')")

        # Now use the sorted data to construct the result.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % 'order_index_sorted',
            "for i, data in ipairs(records) do",

            # Fetch the original record from the hash.
            "    local record = redis.call('HGET', 'order', data)"

            "    redis.call('RPUSH', 'order_result', record)" % self.field,
            "end"
        ])

        return ('order_result', '\n'.join(lua), self.offset)
