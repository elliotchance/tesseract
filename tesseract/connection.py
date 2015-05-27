import json
import socket
import threading
from tesseract import client
from tesseract import instance
from tesseract import parser
from tesseract import select
from tesseract import transaction


class Connection(threading.Thread):
    def __init__(self, client_socket, connection_id, tesseract):
        threading.Thread.__init__(self)
        assert isinstance(client_socket, socket.socket)
        assert isinstance(connection_id, int)
        assert isinstance(tesseract, instance.Instance)
        self.__client_socket = client_socket
        self.connection_id = connection_id
        self.instance = tesseract
        manager = transaction.TransactionManager.get_instance(tesseract.redis)
        self.transaction_id = manager.next_transaction_id()
        self.setName(connection_id)

    def __send(self, data):
        try:
            self.__client_socket.send(data)
        except:
            self.__client_socket.send(bytes(data, 'UTF-8'))

    def run(self):
        self.__setup_no_table()

        while True:
            # Read the incoming request.
            data = self.__client_socket.recv(1024)

            # When data is blank it means the client has disconnected.
            if len(data) == 0:
                self.__disconnect_client()
                break

            # Decode the JSON.
            try:
                request = json.loads(data.decode())
                sql = request['sql'].strip()

                if len(sql) == 0:
                    self.instance.log("Empty SQL request (%d): %s" % (self.connection_id, data))
                    self.__send('{"success":false,"error":"Empty SQL request."}')
                    continue

                self.instance.log("SQL (%d): %s" % (self.connection_id, sql))
            except ValueError:
                self.instance.log("Bad request (%d): %s" % (self.connection_id, data))

                # The JSON could not be decoded, return an error.
                self.__send('{"success":false,"error":"Not valid JSON"}')
                continue

            # Process the request.
            result = self.execute(str(request['sql']))

            # Send the response.
            self.__send(json.dumps(result))

            manager = transaction.TransactionManager.get_instance(self.instance.redis)
            if not manager.in_transaction():
                self.transaction_id = manager.next_transaction_id()

    def __disconnect_client(self):
        manager = transaction.TransactionManager.get_instance(self.instance.redis)
        if manager.in_transaction():
            self.instance.log("ROLLBACK (%d)." % self.connection_id)
            manager.rollback()

        self.instance.log("Client disconnected (%d)." % self.connection_id)

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
        return threading.current_thread()

    def __execute_statement(self, result):
        return result.statement.execute(result, self.instance)

    def __setup_no_table(self):
        self.execute('DELETE FROM %s' % select.SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % select.SelectStatement.NO_TABLE)
