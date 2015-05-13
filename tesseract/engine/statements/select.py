from redis import StrictRedis
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.group import GroupStage
from tesseract.engine.stage.index import IndexStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.ast import SelectStatement
from tesseract.engine.stage.limit import LimitStage
from tesseract.server.protocol import Protocol


class Select(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(instance.redis, StrictRedis)

        instance.redis.delete('agg')

        select = result.statement
        lua, args, manager = self.compile_select(result, instance.redis)

        if select.explain:
            instance.redis.delete('explain')
            return Protocol.successful_response(manager.explain(select.table_name))

        return self.run(
            instance.redis,
            select.table_name,
            instance.warnings,
            lua,
            args,
            result,
            manager
        )

    def __find_index(self, expression, redis, result, stages):
        """Try and find an index that can be used for the WHERE expression. If
        and index is found it is added to the query plan.

        Returns:
          If an index was found True is returned, else False.

        """
        tn = result.statement.table_name
        rules = {
            'I=V': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': lambda e: [e.right],
            },
            'V=I': {
                'index_name': lambda e: '%s.%s' % (tn, e.right),
                'args': lambda e: [e.left],
            },
        }

        signature = expression.where.signature()
        if signature in rules:
            for index_name in redis.hkeys('indexes'):
                # noinspection PyCallingNonCallable
                looking_for = rules[signature]['index_name'](expression.where)
                if redis.hget('indexes', index_name).decode() == looking_for:
                    # noinspection PyCallingNonCallable
                    args = rules[signature]['args'](expression.where)
                    args.insert(0, str(index_name.decode()))
                    stages.add(IndexStage, args)
                    return True

        return False

    def __compile_where(self, expression, redis, result, stages):
        """WHen compiling the WHERE clause we need to see if there is an
        available index with `__find_index()` - hopefully there is. Otherwise we
        fall back to a full table scan.

        """
        if expression.where:
            index_found = self.__find_index(expression, redis, result, stages)
            if not index_found:
                stages.add(WhereStage, (expression.where,))

    def __compile_group(self, expression, stages):
        if expression.group or expression.contains_aggregate():
            stages.add(GroupStage, (expression.group, expression.columns))

    def __compile_order(self, expression, stages):
        if expression.order:
            stages.add(OrderStage, (expression.order,))

    def __compile_columns(self, expression, stages):
        """Compile the `SELECT` columns."""
        if len(expression.columns) > 1 or str(expression.columns[0]) != '*':
            stages.add(ExpressionStage, (expression.columns,))

    def __compile_limit(self, expression, stages):
        if expression.limit:
            stages.add(LimitStage, (expression.limit,))

    def compile_select(self, result, redis):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis, StrictRedis)

        expression = result.statement
        offset = 2
        args = []

        stages = StageManager(redis)

        self.__compile_where(expression, redis, result, stages)
        self.__compile_group(expression, stages)
        self.__compile_order(expression, stages)
        self.__compile_columns(expression, stages)
        self.__compile_limit(expression, stages)

        lua = """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        lua += stages.compile_lua(offset, expression.table_name)

        return (lua, args, stages)
