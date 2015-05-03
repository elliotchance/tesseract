import json
import socket
from tesseract.engine.statements.delete import Delete
from tesseract.engine.statements.indexes import CreateIndex, DropIndex
from tesseract.engine.statements.insert import Insert
from tesseract.engine.statements.notifications import CreateNotification, \
    DropNotification
from tesseract.engine.statements.select import Select
from tesseract.engine.statements.tables import DropTable
from tesseract.engine.statements.update import Update
from tesseract.server.instance import Instance
from tesseract.server.protocol import Protocol
import tesseract.sql.parser as parser
from tesseract.sql.ast import *


try: # pragma: no cover
    # Python 2.x
    from thread import start_new_thread
except: # pragma: no cover
    # Python 3.x
    import threading

class Server:
    """A server will execute SQL commands and return their result."""

    def __init__(self, redis_host=None):
        self.instance = Instance(redis_host)

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
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket)
                ).start()

    def handle_client(self, client_socket):
        while True:
            # Read the incoming request.
            data = client_socket.recv(1024)

            # When data is blank it means the client has disconnected.
            if data == '':
                break

            # Decode the JSON.
            try:
                request = json.loads(data)
                print("SQL: %s" % request['sql'])
            except ValueError:
                print("Bad request: %s" % data)

                # The JSON could not be decoded, return an error.
                client_socket.send('{"success":false,"error":"Not valid JSON"}')
                continue

            # Process the request.
            result = self.execute(request['sql'])

            # Send the response.
            client_socket.send(json.dumps(result))

    def execute(self, sql):
        """Execute a SQL statement."""

        assert isinstance(sql, str)

        # Try to parse the SQL.
        try:
            result = parser.parse(sql)
            self.warnings = result.warnings

        # We could not parse the SQL, so return the error message in the
        # response.
        except RuntimeError as e:
            return Protocol.failed_response(str(e))

        statements = {
            CreateIndexStatement: CreateIndex,
            CreateNotificationStatement: CreateNotification,
            DeleteStatement: Delete,
            DropIndexStatement: DropIndex,
            DropNotificationStatement: DropNotification,
            DropTableStatement: DropTable,
            UpdateStatement: Update
        }

        cls = result.statement.__class__
        if cls in statements:
            statement = statements[cls]()
            return statement.execute(result, self.instance)

        # If the statement is an `INSERT` we always return success.
        if isinstance(result.statement, InsertStatement):
            statement = Insert()
            return statement.execute(result, self.instance.redis, self.instance.notifications,
                                     self.publish, self.execute)

        # This is a `SELECT`
        statement = Select()
        return statement.execute(result, self.instance.redis, self.warnings)


    def publish(self, name, value):
        self.instance.redis.publish(name, value)
