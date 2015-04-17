from tesseract.sql.expressions import Identifier, Value, Expression
from tesseract.sql.statements import Statement


class UpdateStatement(Statement):
    """
    Represents an `UPDATE` statement.
    """

    def __init__(self, table_name, column, expression, where):
        assert isinstance(table_name, Identifier)
        assert isinstance(column, Identifier)
        assert isinstance(expression, Value)
        assert where is None or isinstance(where, Expression)

        self.table_name = table_name
        self.column = column
        self.expression = expression
        self.where = where

    def __str__(self):
        sql = "UPDATE %s SET %s = %s" % (
            self.table_name,
            self.column,
            self.expression
        )

        if self.where:
            sql += ' WHERE %s' % self.where

        return sql
