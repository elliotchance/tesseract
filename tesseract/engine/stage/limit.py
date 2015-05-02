from tesseract.sql.ast import LimitClause
from tesseract.engine.stage.stage import Stage


class LimitStage(Stage):
    def __init__(self, input_page, offset, limit):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(limit, LimitClause)

        self.input_page = input_page
        self.offset = offset
        self.limit = limit

    def compile_lua(self):
        lua = []

        # Clean out buffer.
        lua.append("redis.call('DEL', 'limit')")

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
            "local records = hgetall('%s')" % self.input_page,
            "local counter = 0",
            "for rowid, data in pairs(records) do",
            "   if %s then" % filter,
            "       redis.call('HSET', 'limit', tostring(rowid - %d), data)" % skip,
            "   end",
            "   counter = counter + 1",
            "end",
        ])

        return ('limit', '\n'.join(lua), self.offset)
