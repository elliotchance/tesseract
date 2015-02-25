from unittest import TestCase
from tesseract.sql.expressions import DivideExpression

class TestDivideExpression(TestCase):
    def test_integer_integer(self):
        expr = DivideExpression(12, 6)
        self.assertEqual(2, expr.eval())

    def test_integer_float(self):
        expr = DivideExpression(5, 2.5)
        self.assertEqual(2, expr.eval())
