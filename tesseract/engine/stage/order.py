class OrderStage:
    """
    This OrderStage represents the sorting of a set.

    """
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

        # Iterate the page and unroll the data into two new results.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % self.input_page,

            # This will be explained further down. It is used for making
            # duplicate values unique.
            "local duplicate_index = 1",

            # We will assume that all values to be sorted are numerical until we
            # come accross one that is not - this includes NULL - and sort by
            # alpha.
            "local all_numbers = true",

            "for i, data in ipairs(records) do",
            "    local row = cjson.decode(data)" % self.field,

            # The first thing we need to do it get the value that we will be
            # sorting by.
            "    local value = row['%s']" % self.field,

            "    if value == nil then",
            "        value = 'null'",
            "        all_numbers = false",
            "    end",

            # If the value cannot be cast to a number then we have to fall back
            # to alpha sorting.
            "    if tonumber(value) == nil then",
            "        all_numbers = false",
            "    end",

            # There is one very important thing to note. The value must be
            # unique to represent the record. Since we cannot guarantee it's the
            # case (because you will often be sorting duplicate values) we need
            # to make it unique by appending an index.
            #
            # I'm sure there is a better way to do this, but this will do for
            # now.
            "    if redis.call('HEXISTS', 'order', value) then",
            "        value = value .. duplicate_index",
            "        duplicate_index = duplicate_index + 1",
            "    end",

            # Now add the unique value into a list.
            "    redis.call('RPUSH', 'order_index', value)" % self.field,

            # And use it as a key for a hash that uses the full record as the
            # data.
            "    redis.call('HSET', 'order', value, data)" % self.field,
            "end",
        ])

        # Sort the values.
        lua.extend([
            "if all_numbers then",
            "   redis.call('SORT', 'order_index', 'STORE', 'order_index_sorted')",
            "else",
            "   redis.call('SORT', 'order_index', 'ALPHA', 'STORE', 'order_index_sorted')",
            "end",
        ])

        # Now use the sorted data to construct the result.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % 'order_index_sorted',
            "for i, data in ipairs(records) do",
            "    local record = redis.call('HGET', 'order', data)",
            "    redis.call('RPUSH', 'order_result', record)" % self.field,
            "end"
        ])

        return ('order_result', '\n'.join(lua), self.offset)
