from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import DropTableStatement


class DropTable(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropTableStatement)
        assert isinstance(instance, Instance)

        instance.redis.delete(result.statement.table_name)

        for index_name in instance.redis.hkeys('indexes'):
            prefix = '%s.' % result.statement.table_name
            if str(instance.redis.hget('indexes', index_name)).startswith(prefix):
                instance.redis.hdel('indexes', index_name)
                instance.redis.delete('index:%s' % index_name)

        return Protocol.successful_response()
