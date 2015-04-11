from tesseract.server_result import ServerResult


class CreateNotification:
    def execute(self, result, notifications):
        #assert isinstance(server, Server)

        notification_name = str(result.statement.notification_name)
        if notification_name in notifications:
            message = "Notification '%s' already exists." % notification_name
            return ServerResult(False, error=message)

        notifications[notification_name] = result.statement

        return ServerResult(True)
