from tesseract.sql.expressions import Identifier, Expression
from tesseract.sql.statements import Statement


class UpdateStatement(Statement):
    """
    Represents an `UPDATE` statement.
    """

    def __init__(self, table_name, set):
        assert isinstance(table_name, Identifier)
        assert isinstance(set, Expression)

        self.table_name = table_name
        self.set = set

    def __str__(self):
        return "UPDATE %s SET %s" % (self.table_name, self.set)
