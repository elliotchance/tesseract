from tesseract.sql.expressions import Identifier
from tesseract.sql.statements import Statement
from tesseract.sql.expressions import Expression
from tesseract.sql.clause.order_by import OrderByClause


class SelectStatement(Statement):
    """
    Represents an `SELECT` statement.
    """

    NO_TABLE = Identifier('__no_table')

    def __init__(self, table_name, columns, where=None, order=None):
        """
            :param table_name: Identifier
            :param columns: Expression
            :param where: None|Expression
            :param order: None|OrderByClause
        """
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, Expression) or columns == '*'
        assert where is None or isinstance(where, Expression)
        assert order is None or isinstance(order, OrderByClause)

        self.table_name = table_name
        self.where = where
        self.columns = columns
        self.order = order

    def __str__(self):
        r = "SELECT %s" % self.columns

        if self.table_name != SelectStatement.NO_TABLE:
            r += " FROM %s" % self.table_name

        if self.where:
            r += ' WHERE %s' % self.where

        if self.order:
            r += ' %s' % self.order

        return r
