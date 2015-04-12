from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.update import UpdateStage
from tesseract.engine.statements.statement import Statement
from tesseract.sql.statements.update import UpdateStatement


class Update(Statement):
    def execute(self, result, redis):
        assert isinstance(result.statement, UpdateStatement)

        stages = StageManager()
        stages.add(UpdateStage, (result.statement.column, result.statement.expression))
        lua = stages.compile_lua(2, result.statement.table_name)

        return self.run(redis, result.statement.table_name, [], lua, [], result)
