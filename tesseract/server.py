import tesseract.sql.parser as parser
from tesseract.sql.objects import *

class Server:
    def execute(self, sql):
        """
        Execute a SQL statement.
        :param sql: str
        :return: boolean
        """
        result = parser.parse(sql)
        if isinstance(result.statement, InsertStatement):
            return ServerResult(True, None)

        return ServerResult(True, [])


class ServerResult:
    def __init__(self, success, data):
        self.success = success
        self.data = data
