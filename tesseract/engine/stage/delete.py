from tesseract.engine.stage.where import WhereStage


class DeleteStage(WhereStage):
    """The `DeleteStage` works much like the `WhereStage` except when it comes
    across a matching record (or all records if no `WHERE` clause is provided)
    then the record will be removed.

    """
    def action_on_match(self):
        return self.input_table.lua_delete_record("row[':id']")
