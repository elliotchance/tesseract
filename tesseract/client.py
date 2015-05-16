import json
import socket

class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.connect(('127.0.0.1', 3679))

    def send_request(self, request):
        self.socket.send(json.dumps(request))

    def read_response(self):
        return json.loads(self.socket.recv(1024))

    def send(self, request):
        self.send_request(request)
        return self.read_response()
