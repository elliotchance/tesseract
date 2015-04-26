# Abstract Syntax Tree
# ====================
#
# This file contains all the objects that make up the AST when the SQL is
# parsed.


# Expressions
# -----------

class Expression:
    # A base class for all expressions.

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
        # This is just a placeholder to be overridden by sub-classes. It exists
        # here to satisfy PyCharms need to know that `compile_lua()` is
        # available on `Expression`
        pass

    def is_aggregate(self):
        return False


class Asterisk(Expression):
    def __str__(self):
        return '*'

    def compile_lua(self, offset):
        return ('true', offset, [])


class Value(Expression):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        # This is more of a convenience method for testing. It allows us to
        # compare two `Value`s based on their internal value.

        right = other

        # `other` is allowed to be another `Value` instance of a raw value.
        if isinstance(other, Value):
            right = other.value

        return self.value == right

    def __str__(self):
        if self.value is None:
            return "null"

        if isinstance(self.value, bool):
            return str(self.value).lower()

        if isinstance(self.value, (int, float)):
            return str(self.value)

        if isinstance(self.value, list):
            items = [str(value) for value in self.value]
            return '[%s]' % ', '.join(items)

        if isinstance(self.value, dict):
            items = ['"%s": %s' % (key, str(value))
                     for key, value
                     in self.value.items()]
            return '{%s}' % ', '.join(items)

        return '"%s"' % self.value

    def compile_lua(self, offset):
        # In most cases we can render the literal value as a string and use
        # that.
        value = str(self)

        # `nil` is a special case because a table in Lua that has a `nil` value
        # will not be encoded at all. So the `cjson` library provides a special
        # value for when you explicitly want a `null` in the JSON output.
        if self.value is None:
            value = 'cjson.null'

        # Arrays are also represented differently in Lua - surrounded by curly
        # braces instead of square ones.
        if isinstance(self.value, list):
            items = [value.compile_lua(offset)[0] for value in self.value]
            value = '{%s}' % ', '.join(items)

        # Last, but not least, is objects. There's a weird syntax...
        if isinstance(self.value, dict):
            items = ['["%s"] = %s' % (key, value.compile_lua(offset)[0])
                     for key, value
                     in self.value.items()]
            value = '{%s}' % ', '.join(items)

        return (value, offset, [])


class Identifier(Expression):
    """
    An `Identifier` represents a field or column in the expression to be
    evaluated at runtime with the value in a record.
    """

    def __init__(self, identifier):
        assert isinstance(identifier, str)

        self.identifier = identifier

    def __str__(self):
        return self.identifier

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        return ('row["%s"]' % self.identifier, offset, [])


class BinaryExpression(Expression):
    """
    Binary expressions represent any two expressions that contain an operator
    between them. A simple example is "1 + 2".
    """

    def __init__(self, left, operator, right, lua_operator=None):
        """
        Initialise a binary expression.
        """
        assert isinstance(left, Expression)
        assert isinstance(operator, str)
        assert isinstance(right, Expression)
        assert lua_operator is None or isinstance(lua_operator, str)

        # In most cases the SQL operator (`operator` - like '+') will be the
        # same operator when we render this binary expression in Lua
        # (`lua_operator`) - so addition in Lua also uses the '+' operator. But
        # sometimes it will be different, for example equality in SQL ('=') uses
        # the '==' operator in Lua to represent the same comparison.
        # It is important to note that Lua word operators are case-sensitive and
        # so 'AND' in SQL will not work in Lua, it must be made lowercase 'and'.
        if lua_operator is None:
            lua_operator = operator

        # Assign all the properties.
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

        # If the `lua_operator` starts with a colon then we mean a local
        # function rather than an operator, which has a different syntax.
        if self.lua_operator[0] == ':':
            lua = '%s(%s, %s)' % (self.lua_operator[1:], left, right)

        # Otherwise we are just replacing the operator.
        else:
            lua = '%s %s %s' % (left, self.lua_operator, right)

        return (lua, offset, args1)

    def is_aggregate(self):
        return self.left.is_aggregate() or self.right.is_aggregate()


class EqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '=', right, ':operator_equal')


class NotEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<>', right, ':operator_not_equal')


class GreaterExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>', right, ':operator_greater')


class LessExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<', right, ':operator_less')


class GreaterEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>=', right, ':operator_greater_equal')


class LessEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<=', right, ':operator_less_equal')


class AndExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'AND', right, ':operator_and')


class OrExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'OR', right, ':operator_or')


class AddExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '+', right, ':operator_plus')


class SubtractExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '-', right, ':operator_minus')


class MultiplyExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '*', right, ':operator_times')


class DivideExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '/', right, ':operator_divide')

class ConcatExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '||', right, ':operator_concat')

class FunctionCall(Expression):
    def __init__(self, function_name, argument):
        assert isinstance(function_name, str)
        assert isinstance(argument, Expression)

        self.function_name = function_name
        self.argument = argument

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        # Compile the argument.
        lua_arg, offset, new_args = self.argument.compile_lua(offset)

        if self.is_aggregate():
            lua = 'function_%s(group, %s)' % (self.function_name, lua_arg)
        else:
            lua = 'function_%s(%s)' % (self.function_name, lua_arg)

        return (lua, offset, new_args)

    def __str__(self):
        return '%s(%s)' % (self.function_name, str(self.argument))

    def is_aggregate(self):
        return self.function_name in ('count', 'sum')


class LikeExpression(BinaryExpression):
    def __init__(self, value, regex, is_not):
        assert isinstance(is_not, bool)

        function = ':operator_not_like' if is_not else ':operator_like'
        operator = 'NOT LIKE' if is_not else 'LIKE'
        BinaryExpression.__init__(self, value, operator, regex, function)


class IsExpression(BinaryExpression):
    def __init__(self, value, type, is_not):
        assert isinstance(is_not, bool)

        function = ':operator_is_not' if is_not else ':operator_is'
        operator = 'IS NOT' if is_not else 'IS'
        BinaryExpression.__init__(self, value, operator, type, function)

    def __str__(self):
        return '%s %s %s' % (str(self.left), self.operator, self.right.value)


class NotExpression(Expression):
    def __init__(self, value):
        assert isinstance(value, Expression)

        self.value = value

    def __str__(self):
        return 'NOT %s' % str(self.value)

    def compile_lua(self, offset):
        assert isinstance(offset, int)

        # Compile the argument.
        lua_arg, offset, new_args = self.value.compile_lua(offset)

        lua = 'operator_not(%s)' % lua_arg

        return (lua, offset, new_args)

    def is_aggregate(self):
        return self.value.is_aggregate()


class PowerExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '^', right, ':operator_power')


class ModuloExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '%', right, ':operator_modulo')


class InExpression(BinaryExpression):
    def __init__(self, left, right, is_not):
        assert isinstance(is_not, bool)

        self.is_not = is_not

        function = ':operator_not_in' if is_not else ':operator_in'
        operator = 'NOT IN' if is_not else 'IN'
        BinaryExpression.__init__(self, left, operator, right, function)

    def __str__(self):
        items = [str(item) for item in self.right.value]
        return '%s %s (%s)' % (str(self.left), self.operator, ', '.join(items))


class BetweenExpression(BinaryExpression):
    def __init__(self, left, right, is_not):
        assert isinstance(is_not, bool)

        self.is_not = is_not

        function = ':operator_not_between' if is_not else ':operator_between'
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


# Statements
# ----------

class Statement:
    # Represents a SQL statement.

    def __eq__(self, other):
        # Compare objects based on their attributes.

        assert isinstance(other, object)

        return cmp(self.__dict__, other.__dict__)


class CreateNotificationStatement(Statement):
    # `CREATE NOTIFICATION` statement.

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
    # `DELETE` statement.

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
    # `DROP NOTIFICATION` statement.

    def __init__(self, notification_name):
        assert isinstance(notification_name, Identifier)

        self.notification_name = notification_name

    def __str__(self):
        return "DROP NOTIFICATION %s" % self.notification_name


class InsertStatement(Statement):
    # `INSERT` statement.

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
    # `SELECT` statement.

    NO_TABLE = Identifier('__no_table')

    def __init__(self, table_name, columns, where=None, order=None, group=None):
        assert isinstance(table_name, Identifier)
        assert isinstance(columns, list)
        assert where is None or isinstance(where, Expression)
        assert order is None or isinstance(order, OrderByClause)
        assert group is None or isinstance(group, Identifier)

        self.table_name = table_name
        self.where = where
        self.columns = columns
        self.order = order
        self.group = group

    def __str__(self):
        r = "SELECT %s" % ', '.join([str(col) for col in self.columns])

        if self.table_name != SelectStatement.NO_TABLE:
            r += " FROM %s" % self.table_name

        if self.where:
            r += ' WHERE %s' % self.where

        if self.group:
            r += ' GROUP BY %s' % self.group

        if self.order:
            r += ' %s' % self.order

        return r

    def contains_aggregate(self):
        for col in self.columns:
            if isinstance(col, FunctionCall) and col.is_aggregate():
                return True
        return False


class UpdateStatement(Statement):
    # `UPDATE` statement.

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
    def __init__(self, field_name, ascending):
        assert isinstance(field_name, Identifier)
        assert ascending is None or isinstance(ascending, bool)

        self.field_name = field_name
        self.ascending = ascending

    def __str__(self):
        direction = ''
        if self.ascending == True:
            direction = ' ASC'
        elif self.ascending == False:
            direction = ' DESC'

        return 'ORDER BY %s%s' % (self.field_name, direction)
