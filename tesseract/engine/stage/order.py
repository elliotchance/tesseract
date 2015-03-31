from tesseract.sql.clause.order_by import OrderByClause


class OrderStage:
    """
    This OrderStage represents the sorting of a set.

    """
    def __init__(self, input_page, offset, clause):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(clause, OrderByClause)

        self.input_page = input_page
        self.clause = clause
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
            "    local row = cjson.decode(data)" % self.clause.field_name,

            # The first thing we need to do it get the value that we will be
            # sorting by.
            "    local value = row['%s']" % self.clause.field_name,

            # If the value cannot be cast to a number then we have to fall back
            # to alpha sorting - unless the value was null to begin with, then
            # it takes on a very large value so that it will come out at the end
            # of the set.
            "    if value == cjson.null then",
            "        value = 10000"
            "    elseif tonumber(value) == nil and all_numbers then",
            "        all_numbers = false",
            "    end",

            "    if value == cjson.null then",
            "        value = 'null'",
            "    end",

            # There is one very important thing to note. The value must be
            # unique to represent the record. Since we cannot guarantee it's the
            # case (because you will often be sorting duplicate values) we need
            # to make it unique by appending an index.
            #
            # I'm sure there is a better way to do this, but this will do for
            # now.
            "    if redis.call('HEXISTS', 'order', value) then",
            "        value = tostring(value) .. tostring(duplicate_index)",
            "        duplicate_index = duplicate_index + 1",
            "    end",

            # Now add the unique value into a list.
            "    redis.call('RPUSH', 'order_index', value)" % self.clause.field_name,

            # And use it as a key for a hash that uses the full record as the
            # data.
            "    redis.call('HSET', 'order', value, data)" % self.clause.field_name,
            "end",
        ])

        sort_command = "'SORT', 'order_index'"
        if self.clause.ascending == False:
            sort_command += ", 'DESC'"

        # Sort the values.
        lua.extend([
            "if all_numbers then",
            "   redis.call(%s, 'STORE', 'order_index_sorted')" % sort_command,
            "else",
            "   redis.call(%s, 'ALPHA', 'STORE', 'order_index_sorted')" % sort_command,
            "end",
        ])

        # Now use the sorted data to construct the result.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % 'order_index_sorted',
            "for i, data in ipairs(records) do",
            "    local record = redis.call('HGET', 'order', data)",
            "    redis.call('RPUSH', 'order_result', record)" % self.clause.field_name,
            "end"
        ])

        return ('order_result', '\n'.join(lua), self.offset)
