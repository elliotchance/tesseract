import json

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
        return "INSERT INTO %s %s" % (self.table_name, json.dumps(self.fields))


class SelectStatement(Statement):
    """
    Represents an `SELECT` statement.
    """

    def __init__(self, table_name):
        """
            :param table_name: str
        """
        self.table_name = table_name

        self.assert_type('table_name', str)

    def __str__(self):
        return "SELECT * FROM %s" % self.table_name