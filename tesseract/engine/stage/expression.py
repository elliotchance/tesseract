from tesseract.sql.ast import Identifier
from tesseract.engine.stage.stage import Stage


class ExpressionStage(Stage):
    def __init__(self, input_page, offset, columns):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(columns, list)

        self.input_page = input_page
        self.columns = columns
        self.offset = offset

    def compile_lua(self):
        lua = []

        # Clean out buffer.
        lua.append("redis.call('DEL', 'expression')")

        # Iterate the page.
        lua.extend([
            "local records = hgetall('%s')" % self.input_page,
            "for rowid, data in pairs(records) do",
            "    local row = cjson.decode(data)",
            "    local tuple = {}",
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

            lua.append("    tuple['%s'] = %s" % (name, expression))

            index += 1

        lua.extend([
            "    redis.call('HSET', 'expression', tostring(rowid), cjson.encode(tuple))",
            "end",
        ])

        return ('expression', '\n'.join(lua), offset)
