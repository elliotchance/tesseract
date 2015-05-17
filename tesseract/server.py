import socket
import tesseract.parser as parser
from tesseract.statements import *


try: # pragma: no cover
    # Python 2.x
    # noinspection PyUnresolvedReferences
    from thread import start_new_thread
except: # pragma: no cover
    # Python 3.x
    import threading


class Server:
    """The server acts as the main controller for all incoming connections.

    Each accepted connection spawns a new thread that will exclusively handle
    that connection.

    Attributes:
      __statements (dict): A mapping of ast.py classes to their respective
        statements.py to handle the request.
    """

    __statements = {
        CommitTransactionStatement: CommitTransaction,
        CreateIndexStatement: CreateIndex,
        CreateNotificationStatement: CreateNotification,
        DeleteStatement: Delete,
        DropIndexStatement: DropIndex,
        DropNotificationStatement: DropNotification,
        DropTableStatement: DropTable,
        InsertStatement: Insert,
        SelectStatement: Select,
        UpdateStatement: Update,
        StartTransactionStatement: StartTransaction,
    }

    def __init__(self, redis_host=None):
        """Create the server.

        Arguments:
          redis_host (str): The host and optional port for the Redis server.
        """
        assert redis_host is None or isinstance(redis_host, str)
        self.instance = Instance(self, redis_host)
        self.__setup_no_table()

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

    def __setup_no_table(self):
        self._execute('DELETE FROM %s' % SelectStatement.NO_TABLE)
        self._execute('INSERT INTO %s {}' % SelectStatement.NO_TABLE)

    def __accept_connection(self, server_socket):
        """Accept a connection then spawn off a new thread to handle it. This
        method is blocking until a connection is made.

        """
        (client_socket, address) = server_socket.accept()

        print("Accepted connection.")

        try:
            # Python 2.x
            start_new_thread(self.__handle_client, (client_socket,))
        except:
            # Python 3.x
            threading.Thread(target=self.__handle_client,
                             args=(client_socket,)).start()

    def __handle_client(self, client_socket):
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
            result = self._execute(str(request['sql']))

            # Send the response.
            client_socket.send(json.dumps(result))

    def _publish(self, name, value):
        self.instance.redis.publish(name, value)

    def _execute(self, sql):
        """Execute a SQL statement.

        Arguments:
          sql (str): The single SQL statement to execute.
        """
        assert isinstance(sql, str)

        self.instance.reset_warnings()

        try:
            result = parser.parse(sql)
            self.instance.warnings = result.warnings

        # We could not parse the SQL, so return the error message in the
        # response.
        except RuntimeError as e:
            return Protocol.failed_response(str(e))

        return self.__execute_statement(result)

    def __execute_statement(self, result):
        cls = result.statement.__class__
        if cls in Server.__statements:
            statement = Server.__statements[cls]()
            return statement.execute(result, self.instance)
