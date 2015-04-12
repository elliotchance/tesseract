from tesseract.server.protocol import Protocol


class DropNotification:
    def execute(self, result, notifications):
        notification_name = str(result.statement.notification_name)

        # A notification must exist.
        if notification_name not in notifications:
            error = "No such notification '%s'." % notification_name
            return Protocol.failed_response(error)

        # Remove the notification.
        notifications.pop(notification_name, None)

        return Protocol.successful_response()
