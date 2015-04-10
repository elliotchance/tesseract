import json
import os
import socket
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.sql.expressions import Expression
import tesseract.sql.parser as parser
import redis
import time
from tesseract.sql.statements.delete import DeleteStatement
from tesseract.sql.statements.insert import InsertStatement
from tesseract.sql.statements.select import SelectStatement

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

        # Setup NO_TABLE
        self.execute('DELETE FROM %s' % SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % SelectStatement.NO_TABLE)

        self.lua_cache = {}


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
            start_time = time.time()
            result = parser.parse(sql)
            parser_time = time.time() - start_time

            self.warnings = result.warnings

            # If the statement is a `DELETE`
            if isinstance(result.statement, DeleteStatement):
                self.redis.delete(result.statement.table_name)
                server_result = ServerResult(True)

            # If the statement is an `INSERT` we always return success.
            elif isinstance(result.statement, InsertStatement):
                self.redis.lpush(result.statement.table_name,
                                 Expression.to_sql(result.statement.fields))
                server_result = ServerResult(True)

            # This is a `SELECT`
            else:
                server_result = self.execute_select(result)

            server_result.time = {
                'parser': parser_time,
                'execute': time.time() - start_time - parser_time,
            }
            return server_result

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
            self.redis.rpush(result.statement.table_name,
                             Expression.to_sql(result.statement.fields))
            return ServerResult(True)

        # This is a `SELECT`
        return self.execute_select(result)


    def load_lua_dependency(self, operator):
        key = '/lua/%s.lua' % operator
        if key not in self.lua_cache:
            here = os.path.dirname(os.path.realpath(__file__))
            with open(here + key) as lua_script:
                self.lua_cache[key] = ''.join(lua_script.read())
        return self.lua_cache[key]


    def compile_select(self, result):
        expression = result.statement
        assert isinstance(expression, SelectStatement)

        offset = 2
        args = []

        stages = StageManager()

        # Compile WHERE stage.
        if expression.where:
            stages.add(WhereStage, (expression.where))

        # Compile the ORDER BY clause.
        if expression.order:
            stages.add(OrderStage, (expression.order))

        # Lua dependencies. It is important we load the base before anything
        # else otherwise Lua will throw an error about base stuff missing.
        lua = self.load_lua_dependency('base')
        for requirement in result.lua_requirements:
            lua += self.load_lua_dependency(requirement)

        # Generate the full Lua program.
        lua += """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        # Compile the `SELECT` columns
        if expression.columns != '*':
            stages.add(ExpressionStage, (expression.columns))

        lua += stages.compile_lua(offset, expression.table_name)

        # Extract the values for the expression.
        return (lua, args)


    def execute_select(self, result):
        """
        :type select: SelectExpression
        """
        select = result.statement
        lua, args = self.compile_select(result)
        try:
            run = self.redis.eval(lua, 0, select.table_name, *args)

            records = []

            # The value returns will be the name of the key that can be scanned
            # for results.
            for record in self.redis.lrange(run, 0, -1):
                records.append(json.loads(record.decode()))

            return ServerResult(True, records, warnings=self.warnings)
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
        self.time = {}


    def __str__(self):
        obj = {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
            "time": self.time,
        }
        return json.dumps(obj)
