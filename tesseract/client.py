"""This module is mainly useful for other applications wishing to use the
tesseract server.
"""

import json
import socket


class Client:
    """The tesseract protocol is very simple. This is a basic implementation of
    it.

    Attributes:
      warnings (list): Retained from the last query.
      _socket (socket.socket): The socket between the client and server.
      _host (str): The server host - this should not include the port.
      _port (int): The server port.
    """

    def __init__(self, host='127.0.0.1', port=3679):
        """Create a new client. The connection is made in the constructor.

        Arguments:
          host (str, optional): The host of the server. If not specified then
            localhost is used.
          port (int, optional): The port the server is running on. If no
            specified the default port 3679 is used.

        Example:
          >>> client = Client()
          >>> print(client)
          Client(host='127.0.0.1', port=3679)
        """
        assert isinstance(host, str)
        assert isinstance(port, int)

        self._host = host
        self._port = port
        self.warnings = []
        self._connect()

    def execute(self, sql):
        """Execute a SQL statement and return the result.

        Arguments:
          sql (str): A single SQL statement.

        Returns:
          A mixed result for the query.

        Raises:
          ClientException if an error occurs.

        Examples:
          >>> client = Client()
          >>> print(client.execute("SELECT 1 + 2"))
          [{'col1': 3}]

          >>> client.execute("FOO")
          Traceback (most recent call last):
            ...
          client.ClientException: Could not parse SQL. Error at or near: FOO
        """
        assert isinstance(sql, str)
        result = self._send(Protocol.sql_request(sql))

        self.warnings = result['warnings'] if 'warnings' in result else []

        if result['success']:
            return result['data'] if 'data' in result else None

        raise ClientException(result['error'])

    def __str__(self):
        return "Client(host='%s', port=%d)" % (self._host, self._port)

    def _send(self, request):
        """Send a synchronous request to the server and return its result.

        Arguments:
          request (dict): The request.

        Returns:
          A dict containing the server response.
        """
        assert isinstance(request, dict)
        self._send_request(request)
        return self._read_response()

    def _connect(self):
        """This method is called by the constructor and should never be called
        manually after creating the Client instance.

        It is a protected method so that it can be overridden by a subclass.
        """
        self._socket = socket.socket()
        self._socket.connect((self._host, self._port))

    def _send_request(self, request):
        """Send a request to the server.

        Arguments:
          request (dict): The request.
        """
        assert isinstance(request, dict)
        try:
            self._socket.send(bytes(json.dumps(request), 'UTF-8'))
        except TypeError:
            self._socket.send(json.dumps(request))

    def _read_response(self):
        """Wait on the response from the server.

        Returns:
          A dict containing the server response.
        """
        response = self._socket.recv(1048576)
        return json.loads(response.decode())

    def close(self):
        self._socket.close()


class ClientException(Exception):
    """Thrown when an error is returned from the tesseract server."""
    pass


class Protocol:
    """This class handles the basic protocols that tesseract uses to communicate
    with the server. You can read how the protocol works in the documentation
    under Appendix > Server Protocol.
    """

    @staticmethod
    def successful_response(data=None, warnings=None):
        # If there is no data to be returned (for instance a `DELETE` statement)
        # then you should provide `None`.
        assert data is None or isinstance(data, list), '%r' % data

        # Warning are of course optional.
        assert warnings is None or isinstance(warnings, list), '%r' % warnings

        # Build the response.
        response = {
            "success": True
        }
        if data is not None:
            response['data'] = data
        if warnings is not None:
            response['warnings'] = warnings

        return response

    @staticmethod
    def failed_response(error):
        assert isinstance(error, str)
        return {
            "success": False,
            "error": error
        }

    @staticmethod
    def sql_request(sql):
        assert isinstance(sql, str)
        return {
            "sql": sql,
        }
