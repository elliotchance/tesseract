from tesseract.engine.statements.statement import Statement
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import CreateNotificationStatement, \
    DropNotificationStatement


class CreateNotification(Statement):
    def notification_already_exists(self, notification_name):
        message = "Notification '%s' already exists." % notification_name
        return Protocol.failed_response(message)

    def execute(self, result, instance):
        assert isinstance(result.statement, CreateNotificationStatement)
        assert isinstance(instance, Instance)

        notification_name = str(result.statement.notification_name)
        if notification_name in instance.notifications:
            return self.notification_already_exists(notification_name)

        instance.notifications[notification_name] = result.statement

        return Protocol.successful_response()

class DropNotification(Statement):
    def __no_such_notification(self, notification_name):
        error = "No such notification '%s'." % notification_name
        return Protocol.failed_response(error)

    def execute(self, result, instance):
        assert isinstance(result.statement, DropNotificationStatement)
        assert isinstance(instance, Instance)

        notification_name = str(result.statement.notification_name)

        # A notification must exist.
        if notification_name not in instance.notifications:
            return self.__no_such_notification(notification_name)

        # Remove the notification.
        instance.notifications.pop(notification_name, None)

        return Protocol.successful_response()
