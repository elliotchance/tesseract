from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.update import UpdateStage
from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.sql.ast import UpdateStatement


class Update(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, UpdateStatement)
        assert isinstance(instance, Instance)

        statement = result.statement

        stages = StageManager(instance.redis)
        stages.add(UpdateStage, (statement.columns, statement.where))
        lua = stages.compile_lua(2, statement.table_name)

        return self.run(instance.redis, statement.table_name, [], lua, [], result)
