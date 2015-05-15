from tesseract.engine.index import IndexManager
from tesseract.engine.table import TransientTable, PermanentTable
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
        if self.value.value is None:
            description = 'null'
        else:
            description = 'value %s' % self.value

        return {
            "description": "Index lookup using %s for %s" % (
                self.index_name,
                description
            )
        }

    def compile_lua(self):
        lua = []
        output_table = TransientTable(self.redis)
        index_manager = IndexManager(self.redis)
        index = index_manager.get_index(self.index_name)
        table = PermanentTable(self.redis, index.table_name)

        lua.extend([
            "local records = %s" % index.lua_lookup_exact(self.value.value),
            "for _, data in ipairs(records) do",
            "local row = cjson.decode(%s[1])" % table.lua_get_lua_record('data'),
            output_table.lua_add_lua_record('row'),
            "end",
        ])

        return (output_table, '\n'.join(lua), self.offset)
