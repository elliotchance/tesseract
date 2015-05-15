from tesseract.engine.table import TransientTable
from tesseract.sql.ast import Value, Expression
from tesseract.engine.stage.stage import Stage


class WhereStage(Stage):
    def __init__(self, input_table, offset, redis, where):
        Stage.__init__(self, input_table, offset, redis)
        assert where is None or isinstance(where, Expression)
        self.where = where
        self.output_table = TransientTable(redis)

    def explain(self):
        return {
            "description": "Filter: %s" % self.where
        }

    def compile_lua(self):
        lua = []

        # Compile the WHERE into a Lua expression.
        where_expression = self.where if self.where else Value(True)
        where_clause, self.offset, new_args = where_expression.compile_lua(self.offset)

        lua.extend([
            self.input_table.lua_iterate(decode=True),
            "    if %s then" % where_clause,
            "        %s" % self.action_on_match(),
            "    end",
            "end",
        ])

        return (self.output_table, '\n'.join(lua), self.offset)

    def action_on_match(self):
        return self.output_table.lua_add_lua_record('row')


class ImpossibleWhereStage(Stage):
    def explain(self):
        return {
            "description": "WHERE clause will never return records"
        }

    def compile_lua(self):
        return (TransientTable(self.redis), '', self.offset)
