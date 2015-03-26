import json
import socket

class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.connect(('127.0.0.1', 3679))

    def send(self, request):
        # Send the request.
        self.socket.send(json.dumps(request))

        # Read the response.
        return json.loads(self.socket.recv(1024))
