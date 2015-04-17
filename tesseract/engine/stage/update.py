from tesseract.engine.stage.where import WhereStage


class UpdateStage(WhereStage):
    def __init__(self, input_page, offset, column, value, where):
        WhereStage.__init__(self, input_page, offset, where)
        self.column = column
        self.value = value

    def action_on_match(self):
        lua = (
            "row['%s'] = %s" % (self.column, self.value.compile_lua(0)[0]),
            "data = cjson.encode(row)",
            "redis.call('HSET', '%s', rowid, data)" % self.input_page,
        )
        return '\n'.join(lua)
