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
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Value):
            return self.value == other.value

        return self.value == other

    def __str__(self):
        if self.value is None:
            return "null"

        if isinstance(self.value, bool):
            return str(self.value).lower()

        if isinstance(self.value, (int, float)):
            return str(self.value)

        return '"%s"' % self.value


class Identifier(Expression):
    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return self.identifier


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


class OrExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'OR', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, 'or', offset)


class AddExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '+', right)


class SubtractExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '-', right)


class MultiplyExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '*', right)


class DivideExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '/', right)

    def eval(self):
        if self.left is None:
            return None
        return self.left / self.right
