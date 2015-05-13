from redis import StrictRedis
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.group import GroupStage
from tesseract.engine.stage.index import IndexStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.ast import EqualExpression, Identifier, Value
from tesseract.sql.ast import SelectStatement
from tesseract.engine.stage.limit import LimitStage
from tesseract.server.protocol import Protocol


class Select(Statement):
    def execute(self, result, redis, warnings):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis, StrictRedis)
        assert isinstance(warnings, list)

        redis.delete('agg')

        select = result.statement
        lua, args, manager = self.compile_select(result, redis)

        if select.explain:
            redis.delete('explain')
            return Protocol.successful_response(manager.explain(select.table_name))

        return self.run(redis, select.table_name, warnings, lua, args, result,
                        manager)

    def __compile_where(self, expression, redis, result, stages):
        if expression.where:
            index_found = False

            # Search for a possible index
            if isinstance(expression.where, EqualExpression) and isinstance(
                    expression.where.left, Identifier) and isinstance(
                    expression.where.right, Value):
                for index_name in redis.hkeys('indexes'):
                    looking_for = '%s.%s' % (
                        result.statement.table_name, expression.where.left
                    )
                    if redis.hget('indexes', index_name).decode() == looking_for:
                        stages.add(IndexStage,
                                   (str(index_name.decode()), expression.where.right))
                        index_found = True
                        break

            if isinstance(expression.where, EqualExpression) and isinstance(
                    expression.where.left, Value) and isinstance(
                    expression.where.right, Identifier):
                for index_name in redis.hkeys('indexes'):
                    looking_for = '%s.%s' % (
                        result.statement.table_name, expression.where.right
                    )
                    if redis.hget('indexes', index_name).decode() == looking_for:
                        stages.add(IndexStage,
                                   (str(index_name.decode()), expression.where.left))
                        index_found = True
                        break

            if not index_found:
                stages.add(WhereStage, (expression.where,))

    def compile_select(self, result, redis):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis, StrictRedis)

        expression = result.statement
        offset = 2
        args = []

        stages = StageManager(redis)

        self.__compile_where(expression, redis, result, stages)

        # Compile the GROUP BY clause.
        if expression.group or expression.contains_aggregate():
            stages.add(GroupStage, (expression.group, expression.columns))

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
        if len(expression.columns) > 1 or str(expression.columns[0]) != '*':
            stages.add(ExpressionStage, (expression.columns,))

        if expression.limit:
            stages.add(LimitStage, (expression.limit,))

        lua += stages.compile_lua(offset, expression.table_name)

        return (lua, args, stages)
