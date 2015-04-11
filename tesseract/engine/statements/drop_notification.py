from tesseract.server_result import ServerResult


class DropNotification:
    def execute(self, result, notifications):
        notification_name = str(result.statement.notification_name)
        notifications.pop(notification_name, None)
        return ServerResult(True)
