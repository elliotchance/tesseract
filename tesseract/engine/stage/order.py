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
            "redis.call('DEL', 'order', 'order_index', 'order_index_sorted')"
            "redis.call('DEL', 'order_result', 'order_null')"
        )

        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % self.input_page,

            # This will be explained further down. It is used for making
            # duplicate values unique.
            "local duplicate_index = 1",

            # We will assume that all values to be sorted are numerical until we
            # come across one that is not; except for NULLs which are handled
            # separately. If any non-number value is encountered we will sort by
            # alpha.
            "local all_numbers = true",

            # Iterate the page and unroll the data into two new results.
            "for i, data in ipairs(records) do",
            "    local row = cjson.decode(data)" % self.clause.field_name,

            # The first thing we need to do it get the value that we will be
            # sorting by.
            "    local value = row['%s']" % self.clause.field_name,

            # When `value` is `nil` then there is no field or if the field
            # exists but has a value of `cjson.null` - in either case we treat
            # it as a NULL which must be stored separately.
            "    if value == nil or value == cjson.null then",
            "       redis.call('RPUSH', 'order_null', data)",
            "    else",

            # If the value cannot be cast to a number then we have to fall back
            # to alpha sorting.
            "        if tonumber(value) == nil then",
            "            all_numbers = false",
            "        end",

            # There is one very important thing to note. The value must be
            # unique to represent the record. Since we cannot guarantee it's the
            # case (because you will often be sorting duplicate values) we need
            # to make it unique by appending an index.
            #
            # I'm sure there is a better way to do this, but this will do for
            # now.
            "        if redis.call('HEXISTS', 'order', value) == 1 then",
            "            value = tostring(value) .. tostring(duplicate_index)",
            "            duplicate_index = duplicate_index + 1",
            "        end",

            # Now add the unique value into a list.
            "        redis.call('RPUSH', 'order_index', value)" % self.clause.field_name,

            # And use it as a key for a hash that uses the full record as the
            # data.
            "        redis.call('HSET', 'order', value, data)" % self.clause.field_name,
            "    end",
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
            "local records = redis.call('LRANGE', 'order_index_sorted', '0', '-1')",
            "for i, data in ipairs(records) do",
            "    local record = redis.call('HGET', 'order', data)",
            "    redis.call('RPUSH', 'order_result', record)",
            "end"
        ])

        # `null`s are greater than any non-`null` value so we can append all the
        # `null`s now.
        lua.extend([
            "local records = redis.call('LRANGE', 'order_null', '0', '-1')",
            "for i, data in ipairs(records) do",
            "    redis.call('RPUSH', 'order_result', data)",
            "end"
        ])

        return ('order_result', '\n'.join(lua), self.offset)
