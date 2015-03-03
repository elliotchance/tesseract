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
                     for key, value in object.iteritems()]
            return '{%s}' % ', '.join(items)

        # Let the magic of str() handle all the other cases.
        return str(object)


class Value(Expression):
    NULL = 'null'
    BOOLEAN = 'boolean'
    INTEGER = 'integer'
    FLOAT = 'float'
    STRING = 'string'
    ARRAY = 'array'
    OBJECT = 'object'

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        right = other
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
            items = ['"%s": %s' % (key, str(value)) for key, value in self.value.iteritems()]
            return '{%s}' % ', '.join(items)

        return '"%s"' % self.value

    def eval(self):
        return self

    def type(self):
        if isinstance(self.value, bool):
            return self.BOOLEAN

        if isinstance(self.value, int):
            return self.INTEGER

        if isinstance(self.value, float):
            return self.FLOAT

        if isinstance(self.value, str):
            return self.STRING

        if isinstance(self.value, list):
            return self.ARRAY

        if isinstance(self.value, dict):
            return self.OBJECT

        return self.NULL

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
                     in self.value.iteritems()]
            value = '{%s}' % ', '.join(items)

        return (value, offset, [])


class Identifier(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return self.identifier

    def compile_lua(self, offset):
        return ('row["%s"]' % self.identifier, offset, [])


class BinaryExpression(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        self.operator = operator

    def __str__(self):
        return '%s %s %s' % (self.left, self.operator, self.right)

    def internal_compile_lua(self, operator, offset):
        args = []

        if isinstance(self.left, BinaryExpression):
            left, offset, new_args = self.left.compile_lua(offset)
            args.extend(new_args)
        else:
            args.append(self.left)
            if isinstance(self.left, Identifier):
                left = "tonumber(tuple[ARGV[%d]])" % offset
            else:
                left = "tonumber(ARGV[%d])" % offset
            offset += 1

        if isinstance(self.right, BinaryExpression):
            right, offset, new_args = self.right.compile_lua(offset)
            args.extend(new_args)
        else:
            args.append(self.right)
            if isinstance(self.right, Identifier):
                right = "tonumber(tuple[ARGV[%d]])" % offset
            else:
                right = "tonumber(ARGV[%d])" % offset
            offset += 1

        return ('%s %s %s' % (left, operator, right), offset, args)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, self.operator, offset)


class EqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '=', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, '==', offset)


class NotEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<>', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, '~=', offset)


class GreaterExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>', right)


class LessExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<', right)


class GreaterEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '>=', right)


class LessEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<=', right)


class AndExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'AND', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, 'and', offset)

    def eval(self):
        if self.left.type() == Value.BOOLEAN and self.right.type() == Value.BOOLEAN:
            return self.left.value and self.right.value

        raise RuntimeError('%s AND %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))


class OrExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'OR', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, 'or', offset)

    def eval(self):
        if self.left.type() == Value.BOOLEAN and self.right.type() == Value.BOOLEAN:
            return self.left.value or self.right.value

        raise RuntimeError('%s OR %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))


class AddExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '+', right)

    def eval(self):
        numeric = (Value.INTEGER, Value.FLOAT)

        if self.left.type() in numeric and self.right.type() in numeric:
            return self.left.value + self.right.value

        raise RuntimeError('%s + %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))


class SubtractExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '-', right)

    def eval(self):
        numeric = (Value.INTEGER, Value.FLOAT)

        if self.left.type() in numeric and self.right.type() in numeric:
            return self.left.value - self.right.value

        raise RuntimeError('%s - %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))


class MultiplyExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '*', right)

    def eval(self):
        numeric = (Value.INTEGER, Value.FLOAT)

        if self.left.type() in numeric and self.right.type() in numeric:
            return self.left.value * self.right.value

        raise RuntimeError('%s * %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))


class DivideExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '/', right)

    def eval(self):
        numeric = (Value.INTEGER, Value.FLOAT)

        if self.left.type() in numeric and self.right.type() in numeric:
            return self.left.value / self.right.value

        raise RuntimeError('%s / %s is not supported.' % (
            self.left.type(),
            self.right.type()
        ))
