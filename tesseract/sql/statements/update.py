from tesseract.sql.expressions import Identifier, Value, Expression
from tesseract.sql.statements import Statement


class UpdateStatement(Statement):
    """
    Represents an `UPDATE` statement.
    """

    def __init__(self, table_name, columns, where):
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, Expression)

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
