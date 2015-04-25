from redis import StrictRedis
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.update import UpdateStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.ast import UpdateStatement


class Update(Statement):
    def execute(self, result, redis):
        assert isinstance(result.statement, UpdateStatement)
        assert isinstance(redis, StrictRedis)

        statement = result.statement

        stages = StageManager()
        stages.add(UpdateStage, (statement.columns, statement.where))
        lua = stages.compile_lua(2, statement.table_name)

        return self.run(redis, statement.table_name, [], lua, [], result)
