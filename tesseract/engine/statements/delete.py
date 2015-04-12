from tesseract.engine.stage.delete import DeleteStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.statements.statement import Statement
from tesseract.server.protocol import Protocol
from tesseract.sql.statements.delete import DeleteStatement


class Delete(Statement):
    def execute(self, result, redis):
        assert isinstance(result.statement, DeleteStatement)

        # If there is no WHERE clause we just drop the whole table.
        if not result.statement.where:
            # Delete the whole table.
            redis.delete(result.statement.table_name)

            # Remove the row counter.
            row_id_key = '%s_rowid' % result.statement.table_name
            redis.delete(row_id_key)

            return Protocol.successful_response()

        stages = StageManager()
        stages.add(DeleteStage, (result.statement.where,))
        lua = stages.compile_lua(2, result.statement.table_name)

        return self.run(redis, result.statement.table_name, [], lua, [], result)
