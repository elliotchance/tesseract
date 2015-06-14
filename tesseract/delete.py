from tesseract import ast
from tesseract import client
from tesseract import instance
from tesseract import statement
from tesseract import table
from tesseract import select
from tesseract import stage

class DeleteStatement(statement.Statement):
    """`DELETE` statement."""

    def __init__(self, table_name, where=None):
        assert isinstance(table_name, ast.Identifier)
        assert where is None or isinstance(where, ast.Expression)

        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "DELETE FROM %s" % self.table_name

        if self.where:
            sql += " WHERE %s" % str(self.where)

        return sql

    def execute(self, result, tesseract):
        assert isinstance(result.statement, DeleteStatement)
        assert isinstance(tesseract, instance.Instance)

        stages = stage.StageManager(tesseract.redis)
        stages.add(DeleteStage, (result.statement.where,))
        lua = stages.compile_lua(2, str(result.statement.table_name))

        return self.run(tesseract.redis, result.statement.table_name, [], lua,
                        [], result)


class DeleteStage(select.WhereStage):
    """The `DeleteStage` works much like the `WhereStage` except when it comes
    across a matching record (or all records if no `WHERE` clause is provided)
    then the record will be removed.
    """

    def action_on_match(self):
        return self.input_table.lua_delete_record("row[':id']")
