import json
from tesseract.sql.expressions import Value
import tesseract.sql.parser as parser
from tesseract.sql.statements import *
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
            self.warnings = result.warnings

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
        args = []

        # Compile the `SELECT` expression
        if expression.columns == '*':
            select_expression = "local tuple = row"
        else:
            name = "col1"
            if isinstance(expression.columns, Identifier):
                name = str(expression.columns)
            e, offset, new_args = expression.columns.compile_lua(offset)
            args.extend(new_args)
            select_expression = 'local tuple = {}\ntuple["%s"] = %s' % (name, e)

        # Compile the WHERE into a Lua expression.
        where_expression = expression.where if expression.where else Value(True)
        where_clause, offset, new_args = where_expression.compile_lua(offset)
        args.extend(new_args)

        # Generate the full Lua program.
        lua = """
        -- First thing is to convert all the incoming values from JSON to
        -- native. Skipping the first two arguments that are not JSON and will
        -- always exist.
        local args = {}
        for i = 3, #ARGV do
            args[i] = cjson.decode(ARGV[i])
        end

        -- Get one page - at the moment this is the whole table.
        local records = redis.call('LRANGE', ARGV[1], '0', '-1')

        -- Iterate each record in the page.
        local matches = {}
        for i, data in ipairs(records) do
            -- Each row is stored as a JSON string and needs to be decoded
            -- before we can use it.
            local row = cjson.decode(data)

            -- Process the fields in the SELECT clause.
            %s

            -- Test if the WHERE clause allows this record to be added to the
            -- result.
            if %s then
                table.insert(matches, tuple)
            end
        end

        -- The `matches` will be an array which Python can not decode on the
        -- other end so we wrap it into an object.
        return cjson.encode({result = matches})
        """ % (select_expression, where_clause)

        # Extract the values for the expression.
        return (lua, args)

    def execute_select(self, select):
        """
        :type select: SelectExpression
        """
        lua, args = self.compile_select(select)
        try:
            run = self.redis.eval(lua, 0, select.table_name, select.columns, *args)

            # The extra `str()` is a requirement of Python 3 where
            # `json.loads()` must take a `str` and will not accept the arbitrary
            # bytes in `run`.
            result = json.loads(str(run))

            if len(result['result']) == 0:
                result['result'] = []

            return ServerResult(True, result['result'], warnings=self.warnings)
        except Exception as e:
            # The actual exception message from Lua contains stuff we don't need
            # to report on like the SHA1 of the program, the line number of the
            # error, etc. So we need to trim down to what the actual usable
            # message is.
            message = str(e)
            message = message[message.rfind(':') + 1:].strip()

            return ServerResult(False, error=message)


class ServerResult:
    def __init__(self, success, data=None, error=None, warnings=None):
        self.success = success
        self.data = data
        self.error = error
        self.warnings = warnings
