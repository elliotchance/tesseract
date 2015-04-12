import json
import os
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.server_result import ServerResult
from tesseract.sql.statements.select import SelectStatement


class Select:
    def execute(self, result, redis, warnings):
        """
        :type select: SelectExpression
        """
        select = result.statement
        lua, args = self.compile_select(result)
        try:
            run = redis.eval(lua, 0, select.table_name, *args)

            records = []

            # The value returns will be the name of the key that can be scanned
            # for results.
            for record in redis.hvals(run):
                records.append(json.loads(record.decode()))

            return ServerResult(True, records, warnings=warnings)
        except Exception as e:
            # The actual exception message from Lua contains stuff we don't need
            # to report on like the SHA1 of the program, thqe line number of the
            # error, etc. So we need to trim down to what the actual usable
            # message is.
            message = str(e)
            message = message[message.rfind(':') + 1:].strip()

            return ServerResult(False, error=message)


    def load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/../../lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())


    def compile_select(self, result):
        expression = result.statement
        assert isinstance(expression, SelectStatement)

        offset = 2
        args = []

        stages = StageManager()

        # Compile WHERE stage.
        if expression.where:
            stages.add(WhereStage, (expression.where))

        # Compile the ORDER BY clause.
        if expression.order:
            stages.add(OrderStage, (expression.order))

        # Lua dependencies. It is important we load the base before anything
        # else otherwise Lua will throw an error about base stuff missing.
        lua = self.load_lua_dependency('base')
        for requirement in result.lua_requirements:
            lua += self.load_lua_dependency(requirement)

        # Generate the full Lua program.
        lua += """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        # Compile the `SELECT` columns
        if expression.columns != '*':
            stages.add(ExpressionStage, (expression.columns))

        lua += stages.compile_lua(offset, expression.table_name)

        # Extract the values for the expression.
        return (lua, args)
