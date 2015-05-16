import json
import socket
from tesseract.engine.statements import *
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

    def __setup_no_table(self):
        self.execute('DELETE FROM %s' % SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % SelectStatement.NO_TABLE)

    def __init__(self, redis_host=None):
        self.instance = Instance(self, redis_host)
        self.__setup_no_table()

    def __accept_connection(self, server_socket):
        """Accept a connection then spawn off a new thread to handle it. This
        method is blocking until a connection is made.

        """
        (client_socket, address) = server_socket.accept()

        print("Accepted connection.")

        try:
            # Python 2.x
            start_new_thread(self.handle_client, (client_socket,))
        except:
            # Python 3.x
            threading.Thread(target=self.handle_client,
                             args=(client_socket,)).start()

    def start(self):
        """Create an INET, STREAMing socket for the server socket. Once bound to
        0.0.0.0 on the default port 3679 it will begin accepting connections
        from clients.

        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 3679))
        server_socket.listen(5)

        print("Server ready.")

        while True:
            self.__accept_connection(server_socket)

    def handle_client(self, client_socket):
        while True:
            # Read the incoming request.
            data = client_socket.recv(1024)

            # When data is blank it means the client has disconnected.
            if data == '':
                break

            # Decode the JSON.
            try:
                request = json.loads(data.decode())
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

        self.instance.reset_warnings()

        # Try to parse the SQL.
        try:
            result = parser.parse(sql)
            self.instance.warnings = result.warnings

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
            InsertStatement: Insert,
            SelectStatement: Select,
            UpdateStatement: Update,
        }

        cls = result.statement.__class__
        if cls in statements:
            statement = statements[cls]()
            return statement.execute(result, self.instance)

    def publish(self, name, value):
        self.instance.redis.publish(name, value)
