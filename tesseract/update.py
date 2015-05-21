from tesseract import ast
from tesseract import instance
from tesseract import select
from tesseract import stage
from tesseract import statement


class UpdateStatement(statement.Statement):
    """`UPDATE` statement."""

    def __init__(self, table_name, columns, where):
        assert isinstance(table_name, ast.Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, ast.Expression)

        self.table_name = table_name
        self.columns = columns
        self.where = where

    def __str__(self):
        sql = "UPDATE %s SET " % self.table_name

        columns = []
        for column in self.columns:
            columns.append("%s = %s" % (column[0], column[1]))
        sql += ', '.join(columns)

        if self.where:
            sql += ' WHERE %s' % self.where

        return sql

    def execute(self, result, tesseract):
        assert isinstance(result.statement, UpdateStatement)
        assert isinstance(tesseract, instance.Instance)

        statement = result.statement

        stages = stage.StageManager(tesseract.redis)
        stages.add(UpdateStage, (statement.columns, statement.where))
        lua = stages.compile_lua(2, statement.table_name)

        return self.run(tesseract.redis, statement.table_name, [], lua, [],
                        result)

class UpdateStage(select.WhereStage):
    def __init__(self, input_page, offset, redis, columns, where):
        select.WhereStage.__init__(self, input_page, offset, redis, where)
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
