from unittest import TestCase
from tesseract.sql.expressions import DivideExpression

class TestDivideExpression(TestCase):
    NULL = None
    INTEGER_1 = 100
    INTEGER_2 = 20
    FLOAT_1 = 2.5
    FLOAT_2 = 7.5

    def test_null_null(self):
        expr = DivideExpression(self.NULL, self.NULL)
        self.assertEqual(self.NULL, expr.eval())

    def test_integer_integer(self):
        expr = DivideExpression(self.INTEGER_1, self.INTEGER_2)
        self.assertEqual(5, expr.eval())

    def test_integer_float(self):
        expr = DivideExpression(self.INTEGER_1, self.FLOAT_1)
        self.assertEqual(40, expr.eval())
