from tesseract.engine.stage.delete import DeleteStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.engine.table import PermanentTable
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import DeleteStatement


class Delete(Statement):
    def __drop_table(self, redis, result):
        # Delete the whole table.
        table = PermanentTable(redis, str(result.statement.table_name))
        table.drop()

        return Protocol.successful_response()

    def execute(self, result, instance):
        assert isinstance(result.statement, DeleteStatement)
        assert isinstance(instance, Instance)

        # If there is no WHERE clause we just drop the whole table.
        if not result.statement.where:
            return self.__drop_table(instance.redis, result)

        stages = StageManager(instance.redis)
        stages.add(DeleteStage, (result.statement.where,))
        lua = stages.compile_lua(2, result.statement.table_name)

        return self.run(instance.redis, result.statement.table_name, [], lua, [], result)
