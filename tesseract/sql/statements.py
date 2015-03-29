from tesseract.sql.expressions import Expression, Identifier

# Objects
# =======

class Statement:
    """
    Represents a SQL statement.
    """

    def __eq__(self, other):
        """
        Compare objects based on their attributes.

            :param other: object
            :return: boolean
        """
        assert isinstance(other, object)

        return cmp(self.__dict__, other.__dict__)


class InsertStatement(Statement):
    """
    Represents an `INSERT` statement.
    """

    def __init__(self, table_name, fields):
        """
            :param table_name: Identifier
            :param fields: dict
        """
        assert isinstance(table_name, Identifier)
        assert isinstance(fields, dict)

        self.table_name = table_name
        self.fields = fields

    def __str__(self):
        return "INSERT INTO %s %s" % (
            self.table_name,
            Expression.to_sql(self.fields)
        )


class SelectStatement(Statement):
    """
    Represents an `SELECT` statement.
    """

    NO_TABLE = Identifier('__no_table')

    def __init__(self, table_name, columns, where=None):
        """
            :param table_name: Identifier
            :param columns: Expression
            :param where: None|Expression
        """
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, Expression) or columns == '*'
        assert where is None or isinstance(where, Expression)

        self.table_name = table_name
        self.where = where
        self.columns = columns
        self.order = None

    def __str__(self):
        r = "SELECT %s" % self.columns
        if self.table_name != SelectStatement.NO_TABLE:
            r += " FROM %s" % self.table_name
        if self.where:
            r += ' WHERE %s' % self.where
        if self.order:
            r += ' ORDER BY %s' % self.order
        return r


class DeleteStatement(Statement):
    """
    Represents an `DELETE` statement.
    """

    def __init__(self, table_name):
        """
            :param table_name: Identifier
        """
        assert isinstance(table_name, Identifier)

        self.table_name = table_name

    def __str__(self):
        return "DELETE FROM %s" % self.table_name
