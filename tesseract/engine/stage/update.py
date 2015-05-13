from tesseract.engine.stage.where import WhereStage


class UpdateStage(WhereStage):
    def __init__(self, input_page, offset, redis, columns, where):
        WhereStage.__init__(self, input_page, offset, redis, where)
        assert isinstance(columns, list)
        self.columns = columns

    def action_on_match(self):
        lua = []

        for column in self.columns:
            lua.append(
                "row['%s'] = %s" % (column[0], column[1].compile_lua(0)[0])
            )

        lua.extend((
            self.input_table.lua_delete_record("row[':id']"),
            self.input_table.lua_add_lua_record('row'),
        ))

        return '\n'.join(lua)
