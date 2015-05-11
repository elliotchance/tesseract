from tesseract.engine.table import TransientTable
from tesseract.sql.ast import LimitClause
from tesseract.engine.stage.stage import Stage


class LimitStage(Stage):
    def __init__(self, input_table, offset, redis, limit):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(limit, LimitClause)
        self.limit = limit

    def explain(self):
        return {
            "description": str(self.limit)
        }

    def compile_lua(self):
        lua = []
        output_table = TransientTable(self.redis)

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
            "local counter = 0",
            self.input_table.lua_iterate(decode=True),
            "   if %s then" % filter,
            output_table.lua_add_lua_record('row'),
            "   end",
            "   counter = counter + 1",
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)
