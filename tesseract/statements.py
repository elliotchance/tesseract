import os
import re
from tesseract.client import Protocol
from tesseract.stages import *
from tesseract.instance import Instance
from tesseract.table import PermanentTable
from tesseract.ast import *


class Statement(object):
    def run(self, redis, table_name, warnings, lua, args, result, manager=None):
        assert manager is None or isinstance(manager, StageManager)
        assert isinstance(redis, StrictRedis)
        assert isinstance(table_name, Identifier)
        assert isinstance(warnings, list)
        assert isinstance(lua, str)
        assert isinstance(args, list)

        lua = self.__load_lua_dependencies(result) + lua

        try:
            run = redis.eval(lua, 0, table_name, *args)
        except Exception as e:
            return self.__lua_error(e)

        records = self.__retrieve_records(manager, redis, run)
        return Protocol.successful_response(records, warnings)

    def __load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/../lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())

    def __load_lua_dependencies(self, result):
        """Lua dependencies. It is important we load the base before anything
        else otherwise Lua will throw an error about base stuff missing.

        """
        base_lua = self.__load_lua_dependency('base')
        for requirement in result.lua_requirements:
            base_lua += self.__load_lua_dependency(requirement)

        return base_lua

    def __lua_error(self, e):
        """The actual exception message from Lua contains stuff we don't need
        to report on like the SHA1 of the program, the line number of the error,
        etc. So we need to trim down to what the actual usable message is.

        """
        assert isinstance(e, Exception)

        message = str(e)
        message = message[message.rfind(':') + 1:].strip()

        return Protocol.failed_response(message)

    def __retrieve_records(self, manager, redis, run):
        table = PermanentTable(redis, str(run.decode()))
        records = []

        for record in redis.zrange(table.redis_key(), 0, -1):
            record = json.loads(record.decode())
            record.pop(':id', None)
            records.append(record)

        return records

class Delete(Statement):
    def __drop_table(self, redis, result):
        # Delete the whole table.
        table = PermanentTable(redis, str(result.statement.table_name))
        table.drop()

        return Protocol.successful_response()

    def execute(self, result, instance):
        assert isinstance(result.statement, DeleteStatement)
        assert isinstance(instance, Instance)

        # If there is no WHERE clause we just drop the whole table.
        if not result.statement.where:
            return self.__drop_table(instance.redis, result)

        stages = StageManager(instance.redis)
        stages.add(DeleteStage, (result.statement.where,))
        lua = stages.compile_lua(2, result.statement.table_name)

        return self.run(instance.redis, result.statement.table_name, [], lua, [], result)

class CreateIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, CreateIndexStatement)
        assert isinstance(instance, Instance)

        manager = IndexManager(instance.redis)
        manager.create_index(
            str(result.statement.index_name),
            str(result.statement.table_name),
            str(result.statement.field)
        )

        return Protocol.successful_response()

class DropIndex(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropIndexStatement)
        assert isinstance(instance, Instance)

        manager = IndexManager(instance.redis)
        manager.drop_index(str(result.statement.index_name))
        return Protocol.successful_response()

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

    def execute(self, result, instance):
        table = PermanentTable(instance.redis, str(result.statement.table_name))
        data = Expression.to_sql(result.statement.fields)

        record_id = table.add_record(json.loads(data))

        manager = IndexManager.get_instance(instance.redis)
        indexes = manager.get_indexes_for_table(
            str(result.statement.table_name)
        )
        for index in indexes.values():
            index.add_record(result.statement.fields[index.field_name].value, record_id)

        self.__publish_notifications(
            instance.redis,
            instance.notifications,
            instance.server._publish,
            instance.server._execute,
            data,
            result
        )

        return Protocol.successful_response()

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

class Select(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(instance.redis, StrictRedis)

        instance.redis.delete('agg')

        select = result.statement
        lua, args, manager = self.compile_select(result, instance.redis)

        if select.explain:
            instance.redis.delete('explain')
            return Protocol.successful_response(manager.explain(select.table_name))

        return self.run(
            instance.redis,
            select.table_name,
            instance.warnings,
            lua,
            args,
            result,
            manager
        )

    def __find_index(self, expression, redis, result, stages):
        """Try and find an index that can be used for the WHERE expression. If
        and index is found it is added to the query plan.

        Returns:
          If an index was found True is returned, else False.

        """
        def is_to_value(e):
            if e.right.value == 'null':
                return [Value(None)]
            if e.right.value == 'true':
                return [Value(True)]
            if e.right.value == 'false':
                return [Value(False)]

            return []

        tn = result.statement.table_name
        rules = {
            '^@I = @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': lambda e: [e.right],
            },
            '^@V. = @I$': {
                'index_name': lambda e: '%s.%s' % (tn, e.right),
                'args': lambda e: [e.left],
            },
            '^@I IS @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': is_to_value,
            },
        }

        signature = expression.where.signature()
        rule = None
        for r in rules.keys():
            if re.match(r, signature):
                rule = r
                break

        if rule:
            index_manager = IndexManager.get_instance(redis)
            indexes = index_manager.get_indexes_for_table(str(result.statement.table_name))
            for index_name in indexes:
                # noinspection PyCallingNonCallable
                looking_for = rules[rule]['index_name'](expression.where)
                if redis.hget('indexes', index_name).decode() == looking_for:
                    # noinspection PyCallingNonCallable
                    args = rules[rule]['args'](expression.where)
                    if len(args) > 0:
                        args.insert(0, index_name)
                        stages.add(IndexStage, args)
                        return True

        return False

    def __compile_where(self, expression, redis, result, stages):
        """When compiling the WHERE clause we need to do a few things:

        1. Verify the WHERE clause is not impossible. This is when the
           expression will always be false like 'x = null'.

        2. See if there is an available index with __find_index() - hopefully
           there is.

        3. Otherwise we fall back to a full table scan.

        """
        if expression.where:
            if expression.where.signature() == '@I = @Vn':
                stages.add(ImpossibleWhereStage, ())
                return

            index_found = self.__find_index(expression, redis, result, stages)
            if not index_found:
                stages.add(WhereStage, (expression.where,))

    def __compile_group(self, expression, stages):
        if expression.group or expression.contains_aggregate():
            stages.add(GroupStage, (expression.group, expression.columns))

    def __compile_order(self, expression, stages):
        if expression.order:
            stages.add(OrderStage, (expression.order,))

    def __compile_columns(self, expression, stages):
        """Compile the `SELECT` columns."""
        if len(expression.columns) > 1 or str(expression.columns[0]) != '*':
            stages.add(ExpressionStage, (expression.columns,))

    def __compile_limit(self, expression, stages):
        if expression.limit:
            stages.add(LimitStage, (expression.limit,))

    def compile_select(self, result, redis):
        assert isinstance(result.statement, SelectStatement)
        assert isinstance(redis, StrictRedis)

        expression = result.statement
        offset = 2
        args = []

        stages = StageManager(redis)

        self.__compile_where(expression, redis, result, stages)
        self.__compile_group(expression, stages)
        self.__compile_order(expression, stages)
        self.__compile_columns(expression, stages)
        self.__compile_limit(expression, stages)

        lua = """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        lua += stages.compile_lua(offset, expression.table_name)

        return (lua, args, stages)

class DropTable(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, DropTableStatement)
        assert isinstance(instance, Instance)

        table = PermanentTable(instance.redis, str(result.statement.table_name))
        table.drop()

        return Protocol.successful_response()

class Update(Statement):
    def execute(self, result, instance):
        assert isinstance(result.statement, UpdateStatement)
        assert isinstance(instance, Instance)

        statement = result.statement

        stages = StageManager(instance.redis)
        stages.add(UpdateStage, (statement.columns, statement.where))
        lua = stages.compile_lua(2, statement.table_name)

        return self.run(instance.redis, statement.table_name, [], lua, [], result)

class StartTransaction(Statement):
    def execute(self, result, instance):
        return Protocol.successful_response()

class CommitTransaction(Statement):
    def execute(self, result, instance):
        return Protocol.successful_response()

class RollbackTransaction(Statement):
    def execute(self, result, instance):
        return Protocol.successful_response()
