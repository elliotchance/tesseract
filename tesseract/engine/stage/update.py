from tesseract.engine.stage.where import WhereStage


class UpdateStage(WhereStage):
    def __init__(self, input_page, offset, columns, where):
        WhereStage.__init__(self, input_page, offset, where)

        assert isinstance(columns, list)

        self.columns = columns

    def action_on_match(self):
        lua = []

        for column in self.columns:
            lua.append(
                "row['%s'] = %s" % (column[0], column[1].compile_lua(0)[0])
            )

        lua.extend((
            "data = cjson.encode(row)",
            "redis.call('HSET', '%s', rowid, data)" % self.input_page,
        ))

        return '\n'.join(lua)
