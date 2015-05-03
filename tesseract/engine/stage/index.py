from tesseract.sql.ast import Value, Expression
from tesseract.engine.stage.stage import Stage


class IndexStage(Stage):
    def __init__(self, input_page, offset, index_name, value):
        assert isinstance(input_page, str)
        assert isinstance(offset, int)
        assert isinstance(index_name, str)
        assert isinstance(value, Value)

        self.input_page = input_page
        self.offset = offset
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

        # Clean output buffer.
        lua.append("redis.call('DEL', 'index_result')")

        # Iterate the page.
        lua.extend([
            "local data = redis.call('HGET', 'index:myindex2', '%s')" % (
                #self.index_name,
                self.value
            ),
            "redis.call('HSET', 'index_result', '0', data)",
        ])

        return ('index_result', '\n'.join(lua), self.offset)
