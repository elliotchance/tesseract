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
      __next_connection_id (int, static): The connection ID to be handed to the
        next accepted connection.
      __instance (Instance): The instance.
    """

    __next_connection_id = 0

    def __init__(self, redis_host=None):
        """Create the server.

        Arguments:
          redis_host (str): The host and optional port for the Redis server.
        """
        assert redis_host is None or isinstance(redis_host, str)
        self.__instance = instance.Instance(self, redis_host)

    def start(self):
        """Create an INET, STREAMing socket for the server socket. Once bound to
        0.0.0.0 on the default port 3679 it will begin accepting connections
        from clients.
        """
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind(('0.0.0.0', 3679))
        self.__server_socket.listen(5)

        print("Server ready.")

        while True:
            self.__accept_connection()

    def __accept_connection(self):
        """Accept a connection then spawn off a new thread to handle it. This
        method is blocking until a connection is made.
        """
        (client_socket, address) = self.__server_socket.accept()

        Server.__next_connection_id += 1

        c = connection.Connection(client_socket, Server.__next_connection_id,
                                  self.__instance)
        c.start()

        print("Accepted connection (%d)." % Server.__next_connection_id)

    def exit(self):
        print("Server shutting down.")
        self.__server_socket.close()

    def _publish(self, name, value):
        self.__instance.redis.publish(name, value)
