import tesseract.sql.parser as parser
from tesseract.sql.objects import *

class Server:
    """
    A server will execute SQL commands and return their result.
    """

    def execute(self, sql):
        """
        Execute a SQL statement.

            :param sql: str
            :return: boolean
        """

        # Try to parse the SQL.
        try:
            result = parser.parse(sql)

        # We could not parse the SQL, so return the error message in the
        # response.
        except RuntimeError as e:
            return ServerResult(False, None, str(e))

        # If the statement is an `INSERT` we always return success.
        if isinstance(result.statement, InsertStatement):
            return ServerResult(True)

        # This is a `SELECT`
        return ServerResult(True, [])


class ServerResult:
    def __init__(self, success, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
