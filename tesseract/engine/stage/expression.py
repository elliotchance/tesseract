from tesseract.sql.expressions import Identifier


class ExpressionStage:
    def __init__(self, input_page, offset, columns):
        self.input_page = input_page
        self.columns = columns
        self.offset = offset

    def compile_lua(self):
        lua = []

        # Clean out buffer.
        lua.append(
            "redis.call('DEL', 'expression')"
        )

        name = "col1"
        if isinstance(self.columns, Identifier):
            name = str(self.columns)

        expression, offset, new_args = self.columns.compile_lua(self.offset)

        # Iterate the page.
        lua.extend([
            "local records = redis.call('LRANGE', '%s', '0', '-1')" % self.input_page,
            "for i, data in ipairs(records) do",
            "    local row = cjson.decode(data)",
            "    local tuple = {}",
            "    tuple['%s'] = %s" % (name, expression),
            "    redis.call('RPUSH', 'expression', cjson.encode(tuple))",
            "end",
        ])

        return ('expression', '\n'.join(lua), offset)
