from tesseract import ast
from tesseract import instance
from tesseract import protocol
from tesseract import statement


class CreateNotificationStatement(statement.Statement):
    """`CREATE NOTIFICATION` statement."""

    def __init__(self, notification_name, table_name, where=None):
        assert isinstance(notification_name, ast.Identifier)
        assert isinstance(table_name, ast.Identifier)
        assert where is None or isinstance(where, ast.Expression)

        self.notification_name = notification_name
        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "CREATE NOTIFICATION %s ON %s" % (
            self.notification_name,
            self.table_name
        )

        if self.where:
            sql += ' WHERE %s' % str(self.where)

        return sql

    def notification_already_exists(self, notification_name):
        message = "Notification '%s' already exists." % notification_name
        return protocol.Protocol.failed_response(message)

    def execute(self, result, tesseract):
        assert isinstance(result.statement, CreateNotificationStatement)
        assert isinstance(tesseract, instance.Instance)

        notification_name = str(result.statement.notification_name)
        if notification_name in tesseract.notifications:
            return self.notification_already_exists(notification_name)

        tesseract.notifications[notification_name] = result.statement

        return protocol.Protocol.successful_response()

class DropNotificationStatement(statement.Statement):
    """`DROP NOTIFICATION` statement."""

    def __init__(self, notification_name):
        assert isinstance(notification_name, ast.Identifier)
        self.notification_name = notification_name

    def __str__(self):
        return "DROP NOTIFICATION %s" % self.notification_name

    def __no_such_notification(self, notification_name):
        error = "No such notification '%s'." % notification_name
        return protocol.Protocol.failed_response(error)

    def execute(self, result, tesseract):
        assert isinstance(result.statement, DropNotificationStatement)
        assert isinstance(tesseract, instance.Instance)

        notification_name = str(result.statement.notification_name)

        # A notification must exist.
        if notification_name not in tesseract.notifications:
            return self.__no_such_notification(notification_name)

        # Remove the notification.
        tesseract.notifications.pop(notification_name, None)

        return protocol.Protocol.successful_response()
