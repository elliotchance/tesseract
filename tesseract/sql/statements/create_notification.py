from tesseract.sql.expressions import Identifier, Expression
from tesseract.sql.statements import Statement


class CreateNotificationStatement(Statement):
    """
    Represents an `CREATE NOTIFICATION` statement.
    """

    def __init__(self, notification_name, table_name, where=None):
        assert isinstance(notification_name, Identifier)
        assert isinstance(table_name, Identifier)
        assert where is None or isinstance(where, Expression)

        self.notification_name = notification_name
        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "CREATE NOTIFICATION %s ON %s" % (self.notification_name, self.table_name)
        if self.where:
            sql += ' WHERE %s' % str(self.where)
        return sql
