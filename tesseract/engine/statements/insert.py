import random
from tesseract.server_result import ServerResult
from tesseract.sql.expressions import Expression


class Insert:
    def execute(self, result, redis, notifications, publish, execute):
        data = Expression.to_sql(result.statement.fields)
        redis.rpush(result.statement.table_name, data)

        for notification in notifications.values():
            # Ignore the notification if this does not apply to this table.
            if str(notification.table_name) != str(result.statement.table_name):
                continue

            notification_name = str(notification.notification_name)

            if notification.where is None:
                publish(notification_name, data)
            else:
                # Generate a random table name.
                test_table = ''.join(
                    random.choice('abcdefghijklmnopqrstuvwxyz')
                    for i in range(8)
                )

                # Insert the record into this random table.
                redis.lpush(test_table, data)

                # Perform a select to test if the notification matches.
                select_sql = 'SELECT * FROM %s WHERE %s' % (
                    test_table,
                    str(notification.where)
                )
                select_result = execute(select_sql)

                assert select_result.success

                if len(select_result.data):
                    publish(notification_name, data)

                # Always cleanup.
                redis.delete(test_table)

        return ServerResult(True)