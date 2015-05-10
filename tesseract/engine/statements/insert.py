import json
import random
from tesseract.engine.statements.statement import Statement
from tesseract.engine.table import Table, TransientTable
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import Expression


class Insert(Statement):
    def __publish_notification(self, data, execute, notification, publish,
                               redis):
        notification_name = str(notification.notification_name)
        if notification.where is None:
            publish(notification_name, data)
        else:
            table = TransientTable(redis)
            table.add_record(json.loads(data))

            # Perform a select to test if the notification matches.
            select_sql = 'SELECT * FROM %s WHERE %s' % (
                table.table_name,
                str(notification.where)
            )
            select_result = execute(select_sql)

            assert select_result['success']

            if 'data' in select_result and len(select_result['data']):
                publish(notification_name, data)

    def __publish_notifications(self, redis, notifications, publish, execute,
                                data, result):
        for notification in notifications.values():
            # Ignore the notification if this does not apply to this table.
            if str(notification.table_name) != str(result.statement.table_name):
                continue

            self.__publish_notification(data, execute, notification, publish,
                                        redis)

    def execute(self, result, redis, notifications, publish, execute):
        table = Table(redis, str(result.statement.table_name))
        data = Expression.to_sql(result.statement.fields)
        table.add_record(json.loads(data))

        self.__publish_notifications(redis, notifications, publish, execute,
                                     data, result)

        return Protocol.successful_response()
