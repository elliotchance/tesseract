from tesseract.engine.statements.statement import Statement
from tesseract.engine.table import PermanentTable
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import DropTableStatement


class DropTable(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropTableStatement)
        assert isinstance(instance, Instance)

        table = PermanentTable(instance.redis, str(result.statement.table_name))
        table.drop()

        return Protocol.successful_response()
