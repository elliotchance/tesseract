import json
import os
import random
import socket
from tesseract.engine.stage.expression import ExpressionStage
from tesseract.engine.stage.manager import StageManager
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.stage.where import WhereStage
from tesseract.engine.statements.create_notification import CreateNotification
from tesseract.engine.statements.delete import Delete
from tesseract.engine.statements.insert import Insert
from tesseract.engine.statements.select import Select
from tesseract.server_result import ServerResult
from tesseract.sql.expressions import Expression
import tesseract.sql.parser as parser
import redis
from tesseract.sql.statements.create_notification import \
    CreateNotificationStatement
from tesseract.sql.statements.delete import DeleteStatement
from tesseract.sql.statements.insert import InsertStatement
from tesseract.sql.statements.select import SelectStatement


try: # pragma: no cover
    # Python 2.x
    from thread import start_new_thread
except: # pragma: no cover
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
            try:
                request = json.loads(data)
            except ValueError:
                print data

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
            statement = Delete()
            return statement.execute(result, self.redis)

        # If the statement is an `INSERT` we always return success.
        if isinstance(result.statement, InsertStatement):
            statement = Insert()
            return statement.execute(result, self.redis, self.notifications,
                                     self.publish, self.execute)

        # If the statement is a `CREATE NOTIFICATION`
        if isinstance(result.statement, CreateNotificationStatement):
            statement = CreateNotification()
            return statement.execute(result, self.notifications)

        # This is a `SELECT`
        statement = Select()
        return statement.execute(result, self.redis, self.warnings)


    def publish(self, name, value):
        self.redis.publish(name, value)
