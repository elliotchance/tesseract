import json
import os
import redis
from tesseract import ast
from tesseract import protocol
from tesseract import stage


class Statement(object):
    """Represents a SQL statement."""

    def run(self, redis_connection, table_name, warnings, lua, args, result,
            manager=None):
        assert manager is None or isinstance(manager, stage.StageManager)
        assert isinstance(redis_connection, redis.StrictRedis)
        assert isinstance(table_name, (ast.Identifier, ast.AliasExpression))
        assert isinstance(warnings, list)
        assert isinstance(lua, str)
        assert isinstance(args, list)

        lua = self.__load_lua_dependencies(result) + lua

        try:
            run = redis_connection.eval(lua, 0, table_name, *args)
        except Exception as e:
            from tesseract import transaction
            manager = transaction.TransactionManager.get_instance(redis_connection)
            manager.rollback()

            return self.__lua_error(e)

        records = self.__retrieve_records(manager, redis_connection, run)
        return protocol.Protocol.successful_response(records, warnings)

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

        return protocol.Protocol.failed_response(message)

    def __retrieve_records(self, manager, redis, run):
        from tesseract import table

        the_table = table.PermanentTable(redis, str(run.decode()))
        records = []

        for record in redis.zrange(the_table.redis_key(), 0, -1):
            record = json.loads(record.decode())

            # This should certainly be in here because all tables (permanent or
            # transient) need to be unique and so they are all entered with a
            # row ID. Even though this isn't actually used in almost all cases.
            record.pop(':id', None)

            # These are some cases where the statement plan is so small that the
            # transactional information makes it through. Rather than making the
            # plan more complicated to add extra steps to rip it out lets just
            # clean up these now.
            record.pop(':xid', None)
            record.pop(':xex', None)

            records.append(record)

        return records
