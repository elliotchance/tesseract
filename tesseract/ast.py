"""This file contains all the objects that make up the AST (Abstract Syntax
Tree) when the SQL is parsed.

"""

class Expression:
    """A base class for all expressions."""

    @staticmethod
    def to_sql(object):
        # Render a JSON array.
        if isinstance(object, list):
            items = [Expression.to_sql(value) for value in object]
            return '[%s]' % ', '.join(items)

        # Render a JSON object.
        if isinstance(object, dict):
            items = ['"%s": %s' % (key, Expression.to_sql(value))
                     for key, value
                     in object.items()]
            return '{%s}' % ', '.join(items)

        # Let the magic of str() handle all the other cases.
        return str(object)

    def compile_lua(self, offset):
        """This is just a placeholder to be overridden by sub-classes. It exists
        here to satisfy PyCharms need to know that `compile_lua()` is available
        on `Expression`

        """
        pass

    def is_aggregate(self):
        """Test if the expression contains any elements (like function calls)
        that are on an aggregate set.

        """
        return False

    def signature(self):
        """Any expression can be reduced into a signature. This is expected to
        be overridden by the appropriate child classes.

        The signature should contain spaces where tokens are separated and use
        an "@" followed by a single character for distinct types. You can find
        more information about these types in Value.signature() and
        Identifier.signature().

        Some examples:

        expression      | signature
        --------------- | ---------
        12.3 + foo      | @Vf + @I
        12 > bar - true | @Vi > @I - @V1
        baz IS NOT null | @I IS NOT @Vn

        The signatures are used for detecting specific expressions for things
        like indexes.

        Returns:
          A string. If there is an exceptional case where a token cannot be made
          into a reliable signature (or it is not implemented) the return value
          should be "?".

        """
        return '?'


class Asterisk(Expression):
    """A unary asterisk (different from a binary asterisk which would be a
    MultiplyExpression) signals that all columns in a record are to be used
    like:

    SELECT * FROM foo

    """
    def __str__(self):
        return '*'

    def compile_lua(self, offset):
        """There is only one case where compiling this to Lua might make sense.
        For the `COUNT()` aggregate function where we want to count all the
        records and therefore `COUNT(*)` could be evaluated as `COUNT(true)`.
        For this reason we just return a blatant `true` until a case is found
        that is illogical.

        Returns:
          "true" for the reasoning above.

        """
        return ('true', offset, [])


class Value(Expression):
    """A constant value of any type (numbers, strings, arrays, etc) like `3`,
    `"foo"`, `[1, 2]`, etc.

    """
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        """This is more of a convenience method for testing. It allows us to
        compare two `Value`s based on their internal value."""

        right = other

        # `other` is allowed to be another `Value` instance of a raw value.
        if isinstance(other, Value):
            right = other.value

        return self.value == right

    def __list_to_sql(self):
        items = [str(value) for value in self.value]
        return '[%s]' % ', '.join(items)

    def __dict_to_sql(self):
        items = ['"%s": %s' % (key, str(value)) for key, value in
                 self.value.items()]
        return '{%s}' % ', '.join(items)

    def __str__(self):
        if self.value is None:
            return "null"

        if isinstance(self.value, (bool, int, float)):
            return str(self.value).lower()

        if isinstance(self.value, list):
            return self.__list_to_sql()

        if isinstance(self.value, dict):
            return self.__dict_to_sql()

        return '"%s"' % self.value

    def __compile_lua_array(self, offset, value):
        """Arrays are also represented differently in Lua (called tables) -
        surrounded by curly braces instead of square ones.

        """
        items = [value.compile_lua(offset)[0] for value in self.value]
        return '{%s}' % ', '.join(items)

    def __compile_lua_object(self, offset, value):
        """Objects have a weird syntax in Lua."""
        items = ['["%s"] = %s' % (key, value.compile_lua(offset)[0]) for
                 key, value in self.value.items()]
        return '{%s}' % ', '.join(items)

    def compile_lua(self, offset):
        """In most cases we can render the literal value as a string and use
        that - for example `3` or `foo`.

        `nil` is a special case because a table in Lua that has a `nil` value
        will not be encoded at all. So the `cjson` library provides a special
        value for when you explicitly want a `null` in the JSON output - this is
        called `cjson.null`.

        """
        value = str(self)

        if self.value is None:
            value = 'cjson.null'
        elif isinstance(self.value, list):
            value = self.__compile_lua_array(offset, value)
        elif isinstance(self.value, dict):
            value = self.__compile_lua_object(offset, value)

        return (value, offset, [])

    def signature(self):
        """Values use a two 3 character signature:

        value  | token
        ------ | -----
        null   | @Vn
        true   | @V1
        false  | @V0
        int    | @Vi
        float  | @Vf
        string | @Vs
        array  | @Vl
        object | @Vd

        The reason we use two characters prefixed with a "V" is to allow
        regular expressions that do not care about the value type, for example
        "/@V./" will safely match any value rather than the more brittle and
        longer "/@[n01ifsld]/".

        """
        if self.value is None:
            return '@Vn'

        if isinstance(self.value, bool):
            return '@V%d' % int(self.value)

        return '@V%s' % type(self.value).__name__[0]


class Identifier(Expression):
    """An `Identifier` represents a field or column in the expression to be
    evaluated at runtime with the value in a record.

    """
    def __init__(self, identifier):
        assert isinstance(identifier, str)
        self.identifier = identifier

    def __str__(self):
        return self.identifier

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        return ('f(row, "%s")' % self.identifier, offset, [])

    def signature(self):
        """An "@I" for an Identifier is used in signatures."""
        return '@I'


class BinaryExpression(Expression):
    """Binary expressions represent any two expressions that contain an operator
    between them. A simple example is "1 + 2".

    """
    def __init__(self, left, operator, right, lua_operator):
        """Initialise a binary expression."""
        assert isinstance(left, Expression)
        assert isinstance(operator, str)
        assert isinstance(right, Expression)
        assert isinstance(lua_operator, str)

        self.left = left
        self.right = right
        self.operator = operator
        self.lua_operator = lua_operator

    def __str__(self):
        return '%s %s %s' % (self.left, self.operator, self.right)

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        left, offset, args1 = self.left.compile_lua(offset)
        right, offset, args2 = self.right.compile_lua(offset)
        args1.extend(args2)

        lua = '%s(%s, %s)' % (self.lua_operator, left, right)

        return (lua, offset, args1)

    def is_aggregate(self):
        return self.left.is_aggregate() or self.right.is_aggregate()

    def signature(self):
        return '%s %s %s' % (
            self.left.signature(),
            self.operator,
            self.right.signature()
        )


class EqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '=', right, 'operator_equal')


class NotEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<>', right, 'operator_not_equal')


class GreaterExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>', right, 'operator_greater')


class LessExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<', right, 'operator_less')


class GreaterEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>=', right, 'operator_greater_equal')


class LessEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<=', right, 'operator_less_equal')


class AndExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'AND', right, 'operator_and')


class OrExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'OR', right, 'operator_or')


class AddExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '+', right, 'operator_plus')


class SubtractExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '-', right, 'operator_minus')


class MultiplyExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '*', right, 'operator_times')


class DivideExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '/', right, 'operator_divide')

class ConcatExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '||', right, 'operator_concat')

class FunctionCall(Expression):
    def __init__(self, function_name, argument):
        assert isinstance(function_name, str)
        assert isinstance(argument, Expression)

        self.function_name = function_name
        self.argument = argument

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        lua_arg, offset, new_args = self.argument.compile_lua(offset)

        if self.is_aggregate():
            lua = 'function_%s(group, %s)' % (self.function_name, lua_arg)
        else:
            lua = 'function_%s(%s)' % (self.function_name, lua_arg)

        return (lua, offset, new_args)

    def __str__(self):
        return '%s(%s)' % (self.function_name, str(self.argument))

    def is_aggregate(self):
        return self.function_name in ('avg', 'count', 'max', 'min', 'sum')


class LikeExpression(BinaryExpression):
    def __init__(self, value, regex, is_not, case_sensitive):
        assert isinstance(is_not, bool)
        assert isinstance(case_sensitive, bool)

        function = 'operator_not_like' if is_not else 'operator_like'
        operator = 'NOT LIKE' if is_not else 'LIKE'

        if not case_sensitive:
            function = function.replace('like', 'ilike')
            operator = operator.replace('LIKE', 'ILIKE')

        BinaryExpression.__init__(self, value, operator, regex, function)


class IsExpression(BinaryExpression):
    def __init__(self, value, type, is_not):
        assert isinstance(is_not, bool)

        function = 'operator_is_not' if is_not else 'operator_is'
        operator = 'IS NOT' if is_not else 'IS'
        BinaryExpression.__init__(self, value, operator, type, function)

    def __str__(self):
        return '%s %s %s' % (str(self.left), self.operator, self.right.value)

    def signature(self):
        return '%s %s %s' % (
            self.left.signature(),
            self.operator,
            self.right.signature()
        )


class NotExpression(Expression):
    def __init__(self, value):
        assert isinstance(value, Expression)

        self.value = value

    def __str__(self):
        return 'NOT %s' % str(self.value)

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        lua_arg, offset, new_args = self.value.compile_lua(offset)
        lua = 'operator_not(%s)' % lua_arg

        return (lua, offset, new_args)

    def is_aggregate(self):
        return self.value.is_aggregate()


class PowerExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '^', right, 'operator_power')


class ModuloExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '%', right, 'operator_modulo')


class InExpression(BinaryExpression):
    def __init__(self, left, right, is_not):
        assert isinstance(is_not, bool)

        self.is_not = is_not

        function = 'operator_not_in' if is_not else 'operator_in'
        operator = 'NOT IN' if is_not else 'IN'
        BinaryExpression.__init__(self, left, operator, right, function)

    def __str__(self):
        items = [str(item) for item in self.right.value]
        return '%s %s (%s)' % (str(self.left), self.operator, ', '.join(items))


class BetweenExpression(BinaryExpression):
    def __init__(self, left, right, is_not):
        assert isinstance(is_not, bool)

        self.is_not = is_not

        function = 'operator_not_between' if is_not else 'operator_between'
        operator = 'NOT BETWEEN' if is_not else 'BETWEEN'
        BinaryExpression.__init__(self, left, operator, right, function)

    def __str__(self):
        return '%s %s %s AND %s' % (
            str(self.left),
            self.operator,
            str(self.right.value[0]),
            str(self.right.value[1])
        )


class GroupExpression(Expression):
    def __init__(self, value):
        assert isinstance(value, Expression)

        self.value = value

    def __str__(self):
        return '(%s)' % str(self.value)

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        return self.value.compile_lua(offset)

    def is_aggregate(self):
        return self.value.is_aggregate()


class Statement:
    """Represents a SQL statement."""
    pass


class CreateNotificationStatement(Statement):
    """`CREATE NOTIFICATION` statement.

    """
    def __init__(self, notification_name, table_name, where=None):
        assert isinstance(notification_name, Identifier)
        assert isinstance(table_name, Identifier)
        assert where is None or isinstance(where, Expression)

        self.notification_name = notification_name
        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "CREATE NOTIFICATION %s ON %s" % (
            self.notification_name,
            self.table_name
        )

        if self.where:
            sql += ' WHERE %s' % str(self.where)

        return sql


class DeleteStatement(Statement):
    """`DELETE` statement.

    """
    def __init__(self, table_name, where=None):
        assert isinstance(table_name, Identifier)
        assert where is None or isinstance(where, Expression)

        self.table_name = table_name
        self.where = where

    def __str__(self):
        sql = "DELETE FROM %s" % self.table_name

        if self.where:
            sql += " WHERE %s" % str(self.where)

        return sql


class DropNotificationStatement(Statement):
    """`DROP NOTIFICATION` statement.

    """
    def __init__(self, notification_name):
        assert isinstance(notification_name, Identifier)
        self.notification_name = notification_name

    def __str__(self):
        return "DROP NOTIFICATION %s" % self.notification_name


class InsertStatement(Statement):
    """`INSERT` statement.

    """
    def __init__(self, table_name, fields):
        assert isinstance(table_name, Identifier)
        assert isinstance(fields, dict)

        self.table_name = table_name
        self.fields = fields

    def __str__(self):
        return "INSERT INTO %s %s" % (
            self.table_name,
            Expression.to_sql(self.fields)
        )


class SelectStatement(Statement):
    """`SELECT` statement.

    Attributes:
      NO_TABLE (Identifier, static) - is used when no table is provided. So
        this:
          SELECT 1
        Is actually equivalent to:
          SELECT 1 FROM __no_table

    """
    NO_TABLE = Identifier('__no_table')

    def __init__(self, table_name, columns, where=None, order=None, group=None,
                 explain=False, limit=None):
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, Expression)
        assert order is None or isinstance(order, OrderByClause)
        assert group is None or isinstance(group, Identifier)
        assert limit is None or isinstance(limit, LimitClause)
        assert group is None or isinstance(group, Identifier)
        assert isinstance(explain, bool)

        self.table_name = table_name
        self.where = where
        self.columns = columns
        self.order = order
        self.group = group
        self.limit = limit
        self.explain = explain

    def __limit_to_sql(self):
        if self.limit:
            return ' %s' % self.limit

        return ''

    def __order_to_sql(self):
        if self.order:
            return ' %s' % self.order

        return ''

    def __group_to_sql(self):
        if self.group:
            return ' GROUP BY %s' % self.group

        return ''

    def __where_to_sql(self):
        if self.where:
            return ' WHERE %s' % self.where

        return ''

    def __table_to_sql(self):
        if self.table_name != SelectStatement.NO_TABLE:
            return " FROM %s" % self.table_name

        return ''

    def __str__(self):
        r = 'EXPLAIN ' if self.explain else ''
        r += "SELECT %s" % ', '.join([str(col) for col in self.columns])
        r += self.__table_to_sql()
        r += self.__where_to_sql()
        r += self.__group_to_sql()
        r += self.__order_to_sql()
        r += self.__limit_to_sql()

        return r

    def contains_aggregate(self):
        """Tests if any of the expressions in the `SELECT` clause contain
        aggregate expressions.

        """
        for col in self.columns:
            if col.is_aggregate():
                return True

        return False


class UpdateStatement(Statement):
    """`UPDATE` statement.

    """
    def __init__(self, table_name, columns, where):
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, Expression)

        self.table_name = table_name
        self.columns = columns
        self.where = where

    def __str__(self):
        sql = "UPDATE %s SET " % self.table_name

        columns = []
        for column in self.columns:
            columns.append("%s = %s" % (column[0], column[1]))
        sql += ', '.join(columns)

        if self.where:
            sql += ' WHERE %s' % self.where

        return sql


class OrderByClause:
    """An `ORDER BY` to be used with `SELECT`.

    """
    def __init__(self, field_name, ascending):
        assert isinstance(field_name, Identifier)
        assert ascending is None or isinstance(ascending, bool)

        self.field_name = field_name
        self.ascending = ascending

    def __str__(self):
        direction = ''
        if self.ascending is True:
            direction = ' ASC'
        elif self.ascending is False:
            direction = ' DESC'

        return 'ORDER BY %s%s' % (self.field_name, direction)


class CreateIndexStatement(Statement):
    """`CREATE INDEX` statement.

    """
    def __init__(self, index_name, table_name, field):
        assert isinstance(index_name, Identifier)
        assert isinstance(table_name, Identifier)
        assert isinstance(field, Identifier)

        self.index_name = index_name
        self.table_name = table_name
        self.field = field

    def __str__(self):
        return "CREATE INDEX %s ON %s (%s)" % (
            self.index_name,
            self.table_name,
            self.field
        )


class DropTableStatement(Statement):
    """`DROP TABLE` statement.

    """
    def __init__(self, table_name):
        assert isinstance(table_name, Identifier)

        self.table_name = table_name

    def __str__(self):
        return "DROP TABLE %s" % self.table_name


class DropIndexStatement(Statement):
    """`DROP INDEX` statement.

    """
    def __init__(self, index_name):
        assert isinstance(index_name, Identifier)
        self.index_name = index_name

    def __str__(self):
        return "DROP INDEX %s" % self.index_name


class LimitClause:
    """A `LIMIT` clause to be used with a `SELECT` statement.

    Attributes:
      ALL (Value, static) - is used to represent the SQL `LIMIT ALL`. Even
        though this is the same as having no limit it must be rendered out
        exactly as it came in.

    """
    ALL = Value(1000000000)

    def __init__(self, limit=None, offset=None):
        assert limit is None or isinstance(limit, Value)
        assert offset is None or isinstance(offset, Value)

        self.limit = limit
        self.offset = offset

    def __append_limit_to_sql(self, sql):
        if self.limit:
            limit = 'ALL' if self.limit == LimitClause.ALL else self.limit
            sql.append('LIMIT %s' % limit)

    def __append_offset_to_sql(self, sql):
        if self.offset:
            sql.append('OFFSET %s' % self.offset)

    def __str__(self):
        sql = []
        self.__append_limit_to_sql(sql)
        self.__append_offset_to_sql(sql)
        return ' '.join(sql)


class StartTransactionStatement(Statement):
    def __str__(self):
        return 'START TRANSACTION'


class CommitTransactionStatement(Statement):
    def __str__(self):
        return 'COMMIT'
