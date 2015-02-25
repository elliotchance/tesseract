from unittest import TestCase
from tesseract.sql.expressions import DivideExpression

class TestDivideExpression(TestCase):
    def test_divide_integers(self):
        expr = DivideExpression(12, 6)
        self.assertEqual(2, expr.eval())
