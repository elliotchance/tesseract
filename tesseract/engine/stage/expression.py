from tesseract.engine.table import TransientTable
from tesseract.sql.ast import Identifier
from tesseract.engine.stage.stage import Stage


class ExpressionStage(Stage):
    def __init__(self, input_table, offset, redis, columns):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(columns, list)
        self.columns = columns

    def compile_lua(self):
        lua = []
        table = TransientTable(self.redis)

        # Iterate the page.
        lua.extend([
            self.input_table.lua_iterate(decode=True),
            "local tuple = {}",
        ])

        index = 1
        offset = self.offset
        args = []
        for col in self.columns:
            name = "col%d" % index
            if isinstance(col, Identifier):
                name = str(col)

            expression, offset, new_args = col.compile_lua(offset)
            args.extend(new_args)

            if col.is_aggregate():
                lua.append("local temp = tonumber(row['%s'])" % str(col))
                lua.append("if temp == nil then")
                lua.append("    tuple['%s'] = cjson.null" % name)
                lua.append("else")
                lua.append("    tuple['%s'] = temp * 1" % name)
                lua.append("end")
            else:
                lua.append("tuple['%s'] = %s" % (name, expression))

            index += 1

        lua.extend([
            table.lua_add_lua_record('tuple'),
            "end",
        ])

        return (table, '\n'.join(lua), offset)
