# Expressions
# ===========

class Expression:
    pass


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
            left = "tonumber(tuple[ARGV[%d]])" % offset
            offset += 1

        if isinstance(self.right, BinaryExpression):
            right, offset, new_args = self.right.compile_lua(offset)
            args.extend(new_args)
        else:
            args.append(self.right)
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


class OrExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, 'OR', right)

    def compile_lua(self, offset):
        return BinaryExpression.internal_compile_lua(self, 'or', offset)
