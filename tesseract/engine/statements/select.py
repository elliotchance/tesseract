from redis import StrictRedis
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.group import GroupStage, AfterGroupStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.ast import SelectStatement


class Select(Statement):
    def execute(self, result, redis, warnings):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis, StrictRedis)
        assert isinstance(warnings, list)

        redis.delete('count')
        redis.delete('aftergroup')
        redis.hsetnx('count', 'col1', '0')

        select = result.statement
        lua, args, manager = self.compile_select(result)
        return self.run(redis, select.table_name, warnings, lua, args, result,
                        manager)


    def compile_select(self, result):
        assert isinstance(result.statement, SelectStatement)

        expression = result.statement
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
        if all([str(col) != '*' for col in expression.columns]):
            stages.add(ExpressionStage, (expression.columns,))

        if expression.contains_aggregate():
            stages.add(AfterGroupStage, ())

        lua += stages.compile_lua(offset, expression.table_name)

        # Extract the values for the expression.
        return (lua, args, stages)
