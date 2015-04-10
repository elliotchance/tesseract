from tesseract.sql.expressions import Expression, Identifier
from tesseract.sql.statements import Statement


class InsertStatement(Statement):
    """
    Represents an `INSERT` statement.
    """

    def __init__(self, table_name, fields):
        assert isinstance(table_name, Identifier)
        assert isinstance(fields, dict)

        self.table_name = table_name
        self.fields = fields

    def __str__(self):
        return "INSERT INTO %s %s" % (
            self.table_name,
            Expression.to_sql(self.fields)
        )
