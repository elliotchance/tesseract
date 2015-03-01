from tesseract.sql.expressions import Expression, Value

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
        assert isinstance(other, object), \
            'other is not an object, got: %r' % object

        return self.__dict__ == other.__dict__

    def assert_type(self, field_name, expected_type):
        field = getattr(self, field_name)
        assert isinstance(field, expected_type), \
            '%s is not %s, got: %r' % (field_name, expected_type, field)


class InsertStatement(Statement):
    """
    Represents an `INSERT` statement.
    """

    def __init__(self, table_name, fields):
        """
            :param table_name: str
            :param fields: dict
        """
        self.table_name = table_name
        self.fields = fields

        self.assert_type('table_name', str)
        self.assert_type('fields', dict)

    def __str__(self):
        return "INSERT INTO %s %s" % (
            self.table_name,
            Expression.to_sql(self.fields)
        )


class SelectStatement(Statement):
    """
    Represents an `SELECT` statement.
    """

    NO_TABLE = '__no_table'

    def __init__(self, table_name, columns, where=None):
        """
            :param table_name: str
        """
        self.table_name = table_name
        self.where = where
        self.columns = columns

        self.assert_type('table_name', str)

    def __str__(self):
        r = "SELECT %s" % self.columns
        if self.table_name != SelectStatement.NO_TABLE:
            r += " FROM %s" % self.table_name
        if self.where:
            r += ' WHERE %s' % self.where
        return r


class DeleteStatement(Statement):
    """
    Represents an `DELETE` statement.
    """

    def __init__(self, table_name):
        """
            :param table_name: str
        """
        self.table_name = table_name

        self.assert_type('table_name', str)

    def __str__(self):
        return "DELETE FROM %s" % self.table_name
