from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import CreateIndexStatement, DropIndexStatement


class CreateIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, CreateIndexStatement)
        assert isinstance(instance, Instance)

        instance.redis.hset(
            'indexes',
            result.statement.index_name,
            '%s.%s' % (result.statement.table_name, result.statement.field)
        )
        return Protocol.successful_response()

class DropIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropIndexStatement)
        assert isinstance(instance, Instance)

        instance.redis.hdel('indexes', result.statement.index_name)
        return Protocol.successful_response()
