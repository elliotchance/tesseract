from tesseract.sql.expressions import Identifier, Expression
from tesseract.sql.statements import Statement


class DeleteStatement(Statement):
    """
    Represents an `DELETE` statement.
    """

    def __init__(self, table_name, where=None):
        assert isinstance(table_name, Identifier)
        assert where is None or isinstance(where, Expression)

        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "DELETE FROM %s" % self.table_name

        if self.where:
            sql += " WHERE %s" % str(self.where)

        return sql
