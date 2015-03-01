import json
from tesseract.sql.expressions import Value
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

        # Setup NO_TABLE
        self.execute('DELETE FROM %s' % SelectStatement.NO_TABLE)
        self.execute('INSERT INTO %s {}' % SelectStatement.NO_TABLE)

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

        # If the statement is a `DELETE`
        if isinstance(result.statement, DeleteStatement):
            self.redis.delete(result.statement.table_name)
            return ServerResult(True)

        # If the statement is an `INSERT` we always return success.
        if isinstance(result.statement, InsertStatement):
            self.redis.lpush(result.statement.table_name,
                             Expression.to_sql(result.statement.fields))
            return ServerResult(True)

        # This is a `SELECT`
        return self.execute_select(result.statement)

    def compile_select(self, expression):
        assert isinstance(expression, SelectStatement)

        offset = 3

        # Compile the `SELECT` expression
        if expression.columns == '*':
            select_expression = "local tuple = cjson.decode(data)"
        else:
            select_expression = 'local tuple = {}\ntuple["col1"] = %s' % \
                                expression.columns.compile_lua(offset)[0]

        # Compile the WHERE into a Lua expression.
        where_expression = expression.where if expression.where else Value(True)
        where_clause, offset, args = where_expression.compile_lua(offset)

        # Generate the full Lua program.
        lua = """
        local records = redis.call('LRANGE', ARGV[1], '0', '-1')
        local matches = {}

        for i, data in ipairs(records) do
            %s
            if %s then
                table.insert(matches, tuple)
            end
        end

        return cjson.encode({result = matches})
        """ % (select_expression, where_clause)

        # Extract the values for the expression.
        return (lua, args)

    def execute_select(self, select):
        """
        :type select: SelectExpression
        """
        lua, args = self.compile_select(select)
        result = json.loads(self.redis.eval(lua, 0, select.table_name, select.columns, *args))

        if len(result['result']) == 0:
            result['result'] = []

        return ServerResult(True, result['result'])


class ServerResult:
    def __init__(self, success, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
