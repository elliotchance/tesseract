import json
import os
from tesseract.server_result import ServerResult


class Statement:
    def run(self, redis, table_name, warnings, lua, args, result):
        # Lua dependencies. It is important we load the base before anything
        # else otherwise Lua will throw an error about base stuff missing.
        base_lua = self.load_lua_dependency('base')
        for requirement in result.lua_requirements:
            base_lua += self.load_lua_dependency(requirement)

        lua = base_lua + lua

        try:
            run = redis.eval(lua, 0, table_name, *args)

            records = []

            # The value returns will be the name of the key that can be scanned
            # for results.
            for record in redis.hvals(run):
                records.append(json.loads(record.decode()))

            return ServerResult(True, records, warnings=warnings)
        except Exception as e:
            # The actual exception message from Lua contains stuff we don't need
            # to report on like the SHA1 of the program, thqe line number of the
            # error, etc. So we need to trim down to what the actual usable
            # message is.
            message = str(e)
            message = message[message.rfind(':') + 1:].strip()

            return ServerResult(False, error=message)


    def load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/../../lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())
