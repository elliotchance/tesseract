import json
from tesseract.engine.statements.statement import Statement
from tesseract.engine.table import PermanentTable
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import CreateIndexStatement, DropIndexStatement


class CreateIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, CreateIndexStatement)
        assert isinstance(instance, Instance)

        table = PermanentTable(instance.redis, str(result.statement.table_name))
        for data in instance.redis.zrange(table._redis_key(), 0, -1):
            row = json.loads(data.decode())
            instance.redis.hset(
                'index:%s' % str(result.statement.index_name),
                row[str(result.statement.field)],
                data
            )

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
