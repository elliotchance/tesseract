import json
import os
from ply.yacc import LRParser
from redis import StrictRedis
from tesseract.server.protocol import Protocol
from tesseract.sql.expressions import Identifier


class Statement(object):
    def __lua_error(self, e):
        """The actual exception message from Lua contains stuff we don't need
        to report on like the SHA1 of the program, the line number of the error,
        etc. So we need to trim down to what the actual usable message is.

        """
        assert isinstance(e, Exception)

        message = str(e)
        message = message[message.rfind(':') + 1:].strip()

        return Protocol.failed_response(message)

    def run(self, redis, table_name, warnings, lua, args, result):
        assert isinstance(redis, StrictRedis)
        assert isinstance(table_name, Identifier)
        assert isinstance(warnings, list)
        assert isinstance(lua, str)
        assert isinstance(args, list)

        # Lua dependencies. It is important we load the base before anything
        # else otherwise Lua will throw an error about base stuff missing.
        base_lua = self.__load_lua_dependency('base')
        for requirement in result.lua_requirements:
            base_lua += self.__load_lua_dependency(requirement)

        lua = base_lua + lua

        try:
            run = redis.eval(lua, 0, table_name, *args)

            records = []

            # The value returns will be the name of the key that can be scanned
            # for results.
            for record in redis.hvals(run):
                records.append(json.loads(record.decode()))

            return Protocol.successful_response(records, warnings)
        except Exception as e:
            return self.__lua_error(e)


    def __load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/../../lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())
