from tesseract.sql.ast import OrderByClause
from tesseract.engine.stage.stage import Stage


class OrderStage(Stage):
    """This OrderStage represents the sorting of a set.

    """
    def __init__(self, input_page, offset, clause):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(clause, OrderByClause)

        self.input_page = input_page
        self.clause = clause
        self.offset = offset

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

        # Clean out sort buffer.
        lua.append(
            "redis.call('DEL', 'order_null', 'order_boolean', 'order_number', 'order_string')"
            "redis.call('DEL', 'order_boolean_sorted', 'order_number_sorted', 'order_string_sorted')"
            "redis.call('DEL', 'order_result')"
            "redis.call('DEL', 'order_boolean_hash', 'order_number_hash', 'order_string_hash')"
        )

        lua.extend([
            "local records = hgetall('%s')" % self.input_page,

            # This is for making values unique.
            "local duplicate_number = 1",
            "local duplicate_string = 1",

            # Iterate the page and unroll the data into the three categories.
            "for rowid, data in pairs(records) do",

            # Decode the record.
            "    local row = cjson.decode(data)",

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
                "    local record = redis.call('HGET', 'order_boolean_hash', data)",
                "    redis.call('HSET', 'order_result', tostring(rowid), record)",
                "    rowid = rowid + 1",
                "end"
            ],

            # Now numbers.
            [
                "local records = redis.call('LRANGE', 'order_number_sorted', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = redis.call('HGET', 'order_number_hash', data)",
                "    redis.call('HSET', 'order_result', tostring(rowid), record)",
                "    rowid = rowid + 1",
                "end"
            ],

            # Now strings.
            [
                "local records = redis.call('LRANGE', 'order_string_sorted', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    local record = redis.call('HGET', 'order_string_hash', data)",
                "    redis.call('HSET', 'order_result', tostring(rowid), record)",
                "    rowid = rowid + 1",
                "end"
            ],

            # `null`s are greater than any non-`null` value so we can append all
            # the `null`s now.
            [
                "local records = redis.call('LRANGE', 'order_null', '0', '-1')",
                "for i, data in ipairs(records) do",
                "    redis.call('HSET', 'order_result', tostring(rowid), data)",
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

        return ('order_result', '\n'.join(lua), self.offset)
