from tesseract.server.protocol import Protocol


class CreateNotification:
    def execute(self, result, notifications):
        notification_name = str(result.statement.notification_name)
        if notification_name in notifications:
            message = "Notification '%s' already exists." % notification_name
            return Protocol.failed_response(message)

        notifications[notification_name] = result.statement

        return Protocol.successful_response()
