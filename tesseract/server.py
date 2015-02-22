import tesseract.sql.parser as parser
from tesseract.sql.objects import *
import redis

class Server:
    """
    A server will execute SQL commands and return their result.
    """

    def __init__(self, redis_host=None):
        # The default Redis host is `localhost` if it is not provided
        if not redis_host:
            redis_host = 'localhost'

        # The Redis host must be a `str`.
        assert isinstance(redis_host, str)

        # Attempt to connect.
        self.redis = redis.StrictRedis(host=redis_host, port=6379, db=0)
        self.redis.set('tesseract_server', 1)

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
            self.redis.lpush(result.statement.table_name,
                             json.dumps(result.statement.fields))
            return ServerResult(True)

        # This is a `SELECT`
        page = self.redis.lrange(result.statement.table_name, 0, -1)
        all_records = [json.loads(object) for object in page]
        return ServerResult(True, all_records)


class ServerResult:
    def __init__(self, success, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
