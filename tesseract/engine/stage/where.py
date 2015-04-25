from tesseract.engine.stage.stage import Stage
from tesseract.sql.expressions import Value, Expression


class WhereStage(Stage):
    def __init__(self, input_page, offset, where):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert where is None or isinstance(where, Expression)

        self.input_page = input_page
        self.where = where
        self.offset = offset

    def compile_lua(self):
        lua = []

        # Compile the WHERE into a Lua expression.
        where_expression = self.where if self.where else Value(True)
        where_clause, self.offset, new_args = where_expression.compile_lua(self.offset)

        # Clean output buffer.
        lua.append("redis.call('DEL', 'where')")

        # Iterate the page.
        lua.extend([
            "local records = hgetall('%s')" % self.input_page,
            "for rowid, data in pairs(records) do",

            # Each row is stored as a JSON string and needs to be decoded before
            # we can use it.
            "    local row = cjson.decode(data)",

            # Test if the WHERE clause allows this record to be added to the
            # result.
            "    if %s then" % where_clause,
            "        %s" % self.action_on_match(),
            "    end",
            "end",
        ])

        return ('where', '\n'.join(lua), self.offset)

    def action_on_match(self):
        return "redis.call('HSET', 'where', rowid, data)"
