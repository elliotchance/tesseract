from tesseract.engine.index import IndexManager
from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import CreateIndexStatement, DropIndexStatement


class CreateIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, CreateIndexStatement)
        assert isinstance(instance, Instance)

        manager = IndexManager(instance.redis)
        manager.create_index(
            str(result.statement.index_name),
            str(result.statement.table_name),
            str(result.statement.field)
        )

        return Protocol.successful_response()

class DropIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropIndexStatement)
        assert isinstance(instance, Instance)

        manager = IndexManager(instance.redis)
        manager.drop_index(str(result.statement.index_name))
        return Protocol.successful_response()
