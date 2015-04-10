from tesseract.sql.expressions import Identifier
from tesseract.sql.statements import Statement


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
