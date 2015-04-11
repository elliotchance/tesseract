from tesseract.server_result import ServerResult


class DropNotification:
    def execute(self, result, notifications):
        notification_name = str(result.statement.notification_name)

        # A notification must exist.
        if notification_name not in notifications:
            error = "No such notification '%s'." % notification_name
            return ServerResult(False, error=error)

        # Remove the notification.
        notifications.pop(notification_name, None)

        return ServerResult(True)
