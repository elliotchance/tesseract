import json
import os
import socket
from tesseract.sql.expressions import Value
import tesseract.sql.parser as parser
from tesseract.sql.statements import *
import redis

try:
    # Python 2.x
    from thread import start_new_thread
except:
    # Python 3.x
    import threading

class Server:
    """
    A server will execute SQL commands and return their result.
    """

    def __init__(self, redis_host=None):
        # The default Redis host is `localhost` if it is not provided.
        if not redis_host:
            redis_host = 'localhost'

        # The Redis host must be a `str`.
        assert isinstance(redis_host, str)

        # Attempt to connect.
        self.redis = redis.StrictRedis(host=redis_host, port=6379, db=0)
        self.redis.set('tesseract_server', 1)

        self.notifications = {}

        # Setup NO_TABLE
        self.execute('DELETE FROM %s' % SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % SelectStatement.NO_TABLE)


    def start(self):
        # Create an INET, STREAMing socket.
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to a public host, and the default port.
        server_socket.bind(('0.0.0.0', 3679))

        # Become a server socket.
        server_socket.listen(5)

        # Start accepting messages.
        print("Server ready.")
        while True:
            # Accept connections from outside.
            (client_socket, address) = server_socket.accept()

            # A connection has been made, spawn off a new thread to handle it.
            print("Accepted connection.")
            
            try:
                # Python 2.x
                start_new_thread(self.handle_client, (client_socket,))
            except:
                # Python 3.x
                threading.Thread(target=self.handle_client, args=(client_socket)).start()

    def handle_client(self, client_socket):
        while True:
            # Read the incoming request.
            data = client_socket.recv(1024)

            # Decode the JSON.
            request = json.loads(data)

            # Process the request.
            result = self.execute(request['sql'])

            # Send the response.
            client_socket.send(str(result))


    def execute(self, sql):
        """
        Execute a SQL statement.

            :param sql: str
            :return: boolean
        """

        # Try to parse the SQL.
        try:
            result = parser.parse(sql)
            self.warnings = result.warnings

        # We could not parse the SQL, so return the error message in the
        # response.
        except RuntimeError as e:
            return ServerResult(False, None, str(e))

        # If the statement is a `DELETE`
        if isinstance(result.statement, DeleteStatement):
            self.redis.delete(result.statement.table_name)
            return ServerResult(True)

        # If the statement is an `INSERT` we always return success.
        if isinstance(result.statement, InsertStatement):
            data = Expression.to_sql(result.statement.fields)
            self.redis.lpush(result.statement.table_name, data)

            for notification_name in self.notifications:
                table_name = self.notifications[notification_name]
                if str(table_name) == str(result.statement.table_name):
                    self.publish('foo', data)

            return ServerResult(True)

        # If the statement is a `CREATE NOTIFICATION`
        if isinstance(result.statement, CreateNotificationStatement):
            self.notifications[result.statement.notification_name] = \
                result.statement.table_name
            return ServerResult(True)

        # This is a `SELECT`
        return self.execute_select(result)


    def load_lua_dependency(self, operator):
        here = os.path.dirname(os.path.realpath(__file__))
        with open(here + '/lua/%s.lua' % operator) as lua_script:
            return ''.join(lua_script.read())


    def compile_select(self, result):
        expression = result.statement
        assert isinstance(expression, SelectStatement)

        offset = 3
        args = []

        # Compile the `SELECT` expression
        if expression.columns == '*':
            select_expression = "local tuple = row"
        else:
            name = "col1"
            if isinstance(expression.columns, Identifier):
                name = str(expression.columns)
            e, offset, new_args = expression.columns.compile_lua(offset)
            args.extend(new_args)
            select_expression = 'local tuple = {}\ntuple["%s"] = %s' % (name, e)

        # Compile the WHERE into a Lua expression.
        where_expression = expression.where if expression.where else Value(True)
        where_clause, offset, new_args = where_expression.compile_lua(offset)
        args.extend(new_args)

        # Lua dependencies. It is important we load the base before anything
        # else otherwise Lua will throw an error about base stuff missing.
        lua = self.load_lua_dependency('base')
        for requirement in result.lua_requirements:
            lua += self.load_lua_dependency(requirement)

        # Generate the full Lua program.
        lua += """
        local function process_fields_in_select_clause(row)
            %s
            return tuple
        end

        local function matches_where_clause(row)
            return %s
        end
        """ % (select_expression, where_clause)

        lua += self.load_lua_dependency('main')

        # Extract the values for the expression.
        return (lua, args)

    def publish(self, name, value):
        pass

    def execute_select(self, result):
        """
        :type select: SelectExpression
        """
        select = result.statement
        lua, args = self.compile_select(result)
        try:
            run = self.redis.eval(lua, 0, select.table_name, select.columns,
                                  *args)

            # The extra `decode()` is a requirement of Python 3 where
            # `json.loads()` must take a `str` and will not accept the arbitrary
            # bytes in `run`.
            result = json.loads(run.decode())

            if len(result['result']) == 0:
                result['result'] = []

            return ServerResult(True, result['result'], warnings=self.warnings)
        except Exception as e:
            # The actual exception message from Lua contains stuff we don't need
            # to report on like the SHA1 of the program, the line number of the
            # error, etc. So we need to trim down to what the actual usable
            # message is.
            message = str(e)
            message = message[message.rfind(':') + 1:].strip()

            return ServerResult(False, error=message)


class ServerResult:
    def __init__(self, success, data=None, error=None, warnings=None):
        self.success = success
        self.data = data
        self.error = error
        self.warnings = warnings


    def __str__(self):
        obj = {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
        }
        return json.dumps(obj)
