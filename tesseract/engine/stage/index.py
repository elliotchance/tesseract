from tesseract.engine.table import TransientTable
from tesseract.sql.ast import Value
from tesseract.engine.stage.stage import Stage


class IndexStage(Stage):
    def __init__(self, input_table, offset, redis, index_name, value):
        Stage.__init__(self, input_table, offset, redis)
        assert isinstance(index_name, str)
        assert isinstance(value, Value)

        self.index_name = index_name
        self.value = value

    def explain(self):
        return {
            "description": "Index lookup using %s for value %s" % (
                self.index_name,
                self.value
            )
        }

    def compile_lua(self):
        lua = []
        output_table = TransientTable(self.redis)

        lua.extend([
            "local data = redis.call('HGET', 'index:%s', '%s')" % (
                self.index_name,
                self.value
            ),
            "if data ~= false then",
            "local row = cjson.decode(data)",
            output_table.lua_add_lua_record('row'),
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)
