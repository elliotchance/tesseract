from tesseract.engine.statements.statement import Statement
from tesseract.server.protocol import Protocol
from tesseract.sql.statements.drop_notification import DropNotificationStatement


class DropNotification(Statement):
    def __no_such_notification(self, notification_name):
        error = "No such notification '%s'." % notification_name
        return Protocol.failed_response(error)

    def execute(self, result, notifications):
        assert isinstance(result.statement, DropNotificationStatement)
        assert isinstance(notifications, dict)

        notification_name = str(result.statement.notification_name)

        # A notification must exist.
        if notification_name not in notifications:
            return self.__no_such_notification(notification_name)

        # Remove the notification.
        notifications.pop(notification_name, None)

        return Protocol.successful_response()
