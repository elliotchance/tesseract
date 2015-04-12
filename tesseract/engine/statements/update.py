from tesseract.server.protocol import Protocol


class Update:
    def execute(self, result):
        return Protocol.successful_response()
