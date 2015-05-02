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

        # Iterate the page for the desired amount of rows.
        lua.extend([
            "local records = hgetall('%s')" % self.input_page,
            "local counter = 0",
            "for rowid, data in pairs(records) do",
            "   if counter < %s then" % self.limit.limit,
            "       redis.call('HSET', 'limit', tostring(rowid), data)",
            "       counter = counter + 1",
            "   end",
            "end",
        ])

        return ('limit', '\n'.join(lua), self.offset)
