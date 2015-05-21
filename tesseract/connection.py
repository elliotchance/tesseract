import json
import socket
import threading
from tesseract import client
from tesseract import instance
from tesseract import parser
from tesseract import select


class Connection(threading.Thread):
    def __init__(self, client_socket, connection_id, tesseract):
        threading.Thread.__init__(self)
        assert isinstance(client_socket, socket.socket)
        assert isinstance(connection_id, int)
        assert isinstance(tesseract, instance.Instance)
        self.__client_socket = client_socket
        self.connection_id = connection_id
        self.instance = tesseract
        self.transaction_id = 1
        self.setName(connection_id)

    def run(self):
        self.__setup_no_table()

        while True:
            # Read the incoming request.
            data = self.__client_socket.recv(1024)

            # When data is blank it means the client has disconnected.
            if data == '':
                break

            # Decode the JSON.
            try:
                request = json.loads(data.decode())
                print("SQL (%d): %s" % (self.connection_id, request['sql'].strip()))
            except ValueError:
                print("Bad request: %s" % data)

                # The JSON could not be decoded, return an error.
                self.__client_socket.send('{"success":false,"error":"Not valid JSON"}')
                continue

            # Process the request.
            result = self.execute(str(request['sql']))

            # Send the response.
            self.__client_socket.send(json.dumps(result))

            self.transaction_id += 1

    def execute(self, sql):
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
            return client.Protocol.failed_response(str(e))

        return self.__execute_statement(result)

    @staticmethod
    def current_connection():
        thread = threading.current_thread()
        if isinstance(thread, Connection):
            return thread

        from tesseract import test
        return test.TestConnection.current_connection()

    def __execute_statement(self, result):
        return result.statement.execute(result, self.instance)

    def __setup_no_table(self):
        self.execute('DELETE FROM %s' % select.SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % select.SelectStatement.NO_TABLE)
