from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.group import GroupStage, AfterGroupStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.ast import SelectStatement, FunctionCall


class Select(Statement):
    def execute(self, result, redis, warnings):
        redis.delete('count')
        redis.delete('aftergroup')

        select = result.statement
        lua, args, manager = self.compile_select(result)
        return self.run(redis, select.table_name, warnings, lua, args, result,
                        manager)


    def compile_select(self, result):
        expression = result.statement
        assert isinstance(expression, SelectStatement)

        offset = 2
        args = []

        stages = StageManager()

        # Compile WHERE stage.
        if expression.where:
            stages.add(WhereStage, (expression.where,))

        # Compile the GROUP BY clause.
        if expression.group:
            stages.add(GroupStage, (expression.group,))

        # Compile the ORDER BY clause.
        if expression.order:
            stages.add(OrderStage, (expression.order,))

        # Generate the full Lua program.
        lua = """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        # Compile the `SELECT` columns
        if str(expression.columns) != '*':
            stages.add(ExpressionStage, (expression.columns,))

        if isinstance(expression.columns,
                      FunctionCall) and expression.columns.is_aggregate():
            stages.add(AfterGroupStage, ())

        lua += stages.compile_lua(offset, expression.table_name)

        # Extract the values for the expression.
        return (lua, args, stages)
