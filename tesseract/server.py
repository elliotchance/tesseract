import socket
from tesseract import connection
from tesseract import instance

try: # pragma: no cover
    # Python 2.x
    # noinspection PyUnresolvedReferences
    from thread import start_new_thread
except: # pragma: no cover
    # Python 3.x
    import threading

class Server(object):
    """The server acts as the main controller for all incoming connections.

    Each accepted connection spawns a new thread (Connection) that will
    exclusively handle that connection.

    Attributes:
      is_ready (bool): Indicates is the server is ready and accepting
        connections.
      __next_connection_id (int, static): The connection ID to be handed to the
        next accepted connection.
      __instance (Instance): The instance.
      __port (int): The port number to run the server on.
    """

    __next_connection_id = 0

    def __init__(self, redis_host=None, port=3679):
        """Create the server.

        Arguments:
          redis_host (str): The host and optional port for the Redis server.
          port (int): The port number to run the server on.
        """
        assert redis_host is None or isinstance(redis_host, str)
        assert isinstance(port, int)
        self.instance = instance.Instance(self, redis_host)
        self.__port = port
        self.is_ready = False

    def start(self):
        """Create an INET, STREAMing socket for the server socket. Once bound to
        0.0.0.0 on the default port 3679 it will begin accepting connections
        from clients.
        """
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__server_socket.bind(('0.0.0.0', self.__port))
        self.__server_socket.listen(5)

        self.instance.log("Server ready and listening on port %d." % self.__port)
        self.is_ready = True

        self.__accept_connections()
        self.__server_socket.close()

    def __accept_connections(self):
        """Continuously accept connections until the server is told to stop."""
        while self.is_ready:
            self.__accept_connection()

    def __accept_connection(self):
        while self.is_ready:
            try:
                self.__try_to_accept_connection()
            except socket.timeout:
                pass

    def __try_to_accept_connection(self):
        """Accept a connection in a one second timeout. If a connection is made
        a connection will spawn off a new thread to handle it.

        Raises:
          socket.timeout: If no connection is not accepted in the timeout.
        """
        self.__server_socket.settimeout(1)
        (client_socket, address) = self.__server_socket.accept()
        client_socket.settimeout(None)

        Server.__next_connection_id += 1

        c = connection.Connection(client_socket, Server.__next_connection_id,
                                  self.instance)
        c.start()

        self.instance.log("Accepted connection (%d)." % Server.__next_connection_id)

    def exit(self):
        self.instance.log("Server shutting down.")
        self.is_ready = False
