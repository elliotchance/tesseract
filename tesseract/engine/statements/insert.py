import json
import random
from tesseract.engine.statements.statement import Statement
from tesseract.server.protocol import Protocol
from tesseract.sql.ast import Expression


class Insert(Statement):
    def __publish_notification(self, data, execute, notification, publish,
                               redis):
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
            redis.hset(test_table, 0, data)

            # Perform a select to test if the notification matches.
            select_sql = 'SELECT * FROM %s WHERE %s' % (
                test_table,
                str(notification.where)
            )
            select_result = execute(select_sql)

            assert select_result['success']

            if 'data' in select_result and len(select_result['data']):
                publish(notification_name, data)

            # Always cleanup.
            redis.delete(test_table)

    def __publish_notifications(self, redis, notifications, publish, execute,
                                data, result):
        for notification in notifications.values():
            # Ignore the notification if this does not apply to this table.
            if str(notification.table_name) != str(result.statement.table_name):
                continue

            self.__publish_notification(data, execute, notification, publish,
                                        redis)

    def execute(self, result, redis, notifications, publish, execute):
        # Make sure we have a incrementer for generating row IDs, but only set
        # it to zero if it has never been setup.
        row_id_key = '%s_rowid' % result.statement.table_name
        redis.setnx(row_id_key, 0)

        # Get the next record ID.
        row_id = redis.incr(row_id_key)

        # Serialize the row into the JSON we will store.
        data = Expression.to_sql(result.statement.fields)

        # Add to index.
        if 'x' in result.statement.fields:
            redis.hset('index:myindex2', result.statement.fields['x'], data)

        # Insert the row, making sure to fail if we try to override a row that
        # already exists.
        was_set = redis.hsetnx(result.statement.table_name, row_id, data)
        assert was_set == 1

        self.__publish_notifications(redis, notifications, publish, execute,
                                     data, result)

        return Protocol.successful_response()
