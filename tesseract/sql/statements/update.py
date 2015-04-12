from tesseract.sql.expressions import Identifier, Value
from tesseract.sql.statements import Statement


class UpdateStatement(Statement):
    """
    Represents an `UPDATE` statement.
    """

    def __init__(self, table_name, column, expression):
        assert isinstance(table_name, Identifier)
        assert isinstance(column, Identifier)
        assert isinstance(expression, Value)

        self.table_name = table_name
        self.column = column
        self.expression = expression

    def __str__(self):
        return "UPDATE %s SET %s = %s" % (
            self.table_name,
            self.column,
            self.expression
        )
