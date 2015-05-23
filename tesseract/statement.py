import json
import os
import redis
from tesseract import ast
from tesseract import client
from tesseract import stage


class Statement(object):
    """Represents a SQL statement."""

    def run(self, redis_connection, table_name, warnings, lua, args, result,
            manager=None):
        assert manager is None or isinstance(manager, stage.StageManager)
        assert isinstance(redis_connection, redis.StrictRedis)
        assert isinstance(table_name, ast.Identifier)
        assert isinstance(warnings, list)
        assert isinstance(lua, str)
        assert isinstance(args, list)

        lua = self.__load_lua_dependencies(result) + lua

        try:
            run = redis_connection.eval(lua, 0, table_name, *args)
        except Exception as e:
            return self.__lua_error(e)

        records = self.__retrieve_records(manager, redis_connection, run)
        return client.Protocol.successful_response(records, warnings)

    def __load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/../lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())

    def __load_lua_dependencies(self, result):
        """Lua dependencies. It is important we load the base before anything
        else otherwise Lua will throw an error about base stuff missing.
        """
        base_lua = self.__load_lua_dependency('base')
        for requirement in result.lua_requirements:
            base_lua += self.__load_lua_dependency(requirement)

        return base_lua

    def __lua_error(self, e):
        """The actual exception message from Lua contains stuff we don't need
        to report on like the SHA1 of the program, the line number of the error,
        etc. So we need to trim down to what the actual usable message is.
        """
        assert isinstance(e, Exception)

        message = str(e)
        message = message[message.rfind(':') + 1:].strip()

        return client.Protocol.failed_response(message)

    def __retrieve_records(self, manager, redis, run):
        from tesseract import table
        from tesseract import transaction

        the_table = table.PermanentTable(redis, str(run.decode()))
        records = []
        manager = transaction.TransactionManager.get_instance(redis)

        for record in redis.zrange(the_table.redis_key(), 0, -1):
            record = json.loads(record.decode())

            if record[':xid'] in manager.active_transaction_ids():
                continue

            record.pop(':id', None)
            record.pop(':xid', None)
            record.pop(':xex', None)
            records.append(record)

        return records
