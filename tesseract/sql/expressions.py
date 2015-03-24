# Expressions
# ===========


class Expression:
    """
    A base class for all expressions.
    """

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
                     in Expression.dict_iterator(object)]
            return '{%s}' % ', '.join(items)

        # Let the magic of str() handle all the other cases.
        return str(object)

    def compile_lua(self, offset):
        """
        This is just a placeholder to be overridden by sub-classes. It exists
        here to satisfy PyCharms need to know that `compile_lua()` is available
        on `Expression`
        :param offset: integer
        :return: str
        """

    @staticmethod
    def dict_iterator(object):
        try:
            # Python 2.x
            return object.iteritems()
        except:
            # Python 3.x
            return object.items()


class Value(Expression):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        """
        This is more of a convenience method for testing. It allows us to
        compare two `Value`s based on their internal value.

        :return: boolean
        """
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
                     in Expression.dict_iterator(self.value)]
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
        #  braces instead of square ones.
        if isinstance(self.value, list):
            items = [value.compile_lua(offset)[0] for value in self.value]
            value = '{%s}' % ', '.join(items)

        # Last, but not least, is objects. There's a weird syntax...
        if isinstance(self.value, dict):
            items = ['["%s"] = %s' % (key, value.compile_lua(offset)[0])
                     for key, value
                     in Expression.dict_iterator(self.value)]
            value = '{%s}' % ', '.join(items)

        return (value, offset, [])


class Identifier(Expression):
    """
    And `Identifier` represents a field or column in the expression to be
    evaluated at runtime with the value in a record.
    """

    def __init__(self, identifier):
        assert isinstance(identifier, str)

        self.identifier = identifier

    def __str__(self):
        return self.identifier

    def compile_lua(self, offset):
        return ('row["%s"]' % self.identifier, offset, [])


class BinaryExpression(Expression):
    """
    Binary expressions represent any two expressions that contain an operator
    between them. A simple example is "1 + 2".
    """

    def __init__(self, left, operator, right, lua_operator=None):
        """
        Initialise a binary expression.
        :param left: Expression
        :param operator: str
        :param right: Expression
        :param lua_operator: None|str
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


class EqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '=', right, ':operator_equal')


class NotEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<>', right, ':operator_not_equal')


class GreaterExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>', right)


class LessExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<', right, ':operator_less')


class GreaterEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>=', right)


class LessEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<=', right)


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
