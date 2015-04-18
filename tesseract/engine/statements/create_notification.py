from tesseract.engine.statements.statement import Statement
from tesseract.server.protocol import Protocol
from tesseract.sql.statements.create_notification import \
    CreateNotificationStatement


class CreateNotification(Statement):
    def notification_already_exists(self, notification_name):
        message = "Notification '%s' already exists." % notification_name
        return Protocol.failed_response(message)

    def execute(self, result, notifications):
        assert isinstance(result.statement, CreateNotificationStatement)
        assert isinstance(notifications, dict)

        notification_name = str(result.statement.notification_name)
        if notification_name in notifications:
            return self.notification_already_exists(notification_name)

        notifications[notification_name] = result.statement

        return Protocol.successful_response()
