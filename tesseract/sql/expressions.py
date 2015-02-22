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

    def compile_lua(self):
        return 'tostring(tuple[ARGV[2]]) %s tostring(ARGV[3])' % self.operator


class EqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '=', right)

    def compile_lua(self):
        return 'tostring(tuple[ARGV[2]]) == tostring(ARGV[3])'


class NotEqualExpression(BinaryExpression):
    def __init__(self, left, right):
        BinaryExpression.__init__(self, left, '<>', right)

    def compile_lua(self):
        return 'tostring(tuple[ARGV[2]]) ~= tostring(ARGV[3])'


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
