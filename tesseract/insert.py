import json
import threading
from tesseract import ast
from tesseract import client
from tesseract import index
from tesseract import statement
from tesseract import table
from tesseract import transaction


class InsertStatement(statement.Statement):
    """`INSERT` statement."""

    def __init__(self, table_name, fields):
        assert isinstance(table_name, ast.Identifier)
        assert isinstance(fields, dict)

        self.table_name = table_name
        self.fields = fields

    def __str__(self):
        return "INSERT INTO %s %s" % (
            self.table_name,
            ast.Expression.to_sql(self.fields)
        )

    def execute(self, result, tesseract):
        output_table = table.PermanentTable(tesseract.redis, str(result.statement.table_name))
        data = ast.Expression.to_sql(result.statement.fields)

        record_id = output_table.add_record(json.loads(data))

        manager = transaction.TransactionManager.get_instance(tesseract.redis)
        if manager.in_transaction():
            rollback_action = "ZREMRANGEBYSCORE %s %s %s" % (
                output_table.redis_key(),
                record_id,
                record_id,
            )
            manager.record(rollback_action)

        manager = index.IndexManager.get_instance(tesseract.redis)
        indexes = manager.get_indexes_for_table(
            str(result.statement.table_name)
        )
        for i in indexes.values():
            i.add_record(result.statement.fields[i.field_name].value, record_id)

        self.__publish_notifications(
            tesseract.redis,
            tesseract.notifications,
            tesseract.publish,
            data,
            result
        )

        return client.Protocol.successful_response()

    def __publish_notification(self, data, notification, publish, redis):
        notification_name = str(notification.notification_name)
        if notification.where is None:
            publish(notification_name, data)
        else:
            outout_table = table.TransientTable(redis)
            outout_table.add_record(json.loads(data))

            # Perform a select to test if the notification matches.
            select_sql = 'SELECT * FROM %s WHERE %s' % (
                outout_table.table_name,
                str(notification.where)
            )

            from tesseract import connection

            c = connection.Connection.current_connection()
            select_result = c.execute(select_sql)

            assert select_result['success']

            if 'data' in select_result and len(select_result['data']):
                publish(notification_name, data)

    def __publish_notifications(self, redis, notifications, publish, data,
                                result):
        for notification in notifications.values():
            # Ignore the notification if this does not apply to this table.
            if str(notification.table_name) != str(result.statement.table_name):
                continue

            self.__publish_notification(data, notification, publish, redis)
