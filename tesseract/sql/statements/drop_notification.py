from tesseract.sql.expressions import Identifier, Expression
from tesseract.sql.statements import Statement


class DropNotificationStatement(Statement):
    """
    Represents an `DROP NOTIFICATION` statement.
    """

    def __init__(self, notification_name):
        assert isinstance(notification_name, Identifier)

        self.notification_name = notification_name

    def __str__(self):
        return "DROP NOTIFICATION %s" % self.notification_name
