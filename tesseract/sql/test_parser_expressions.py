import tesseract.sql.parser as parser
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserExpressions(ParserTestCase):
    def test_equal(self):
        self.assertSQL('a = 1', 'a = 1')

    def test_not_equal_1(self):
        self.assertSQL('a <> 2', 'a <> 2')

    def test_not_equal_2(self):
        self.assertSQL('a != 3', 'a <> 3')

    def test_greater(self):
        self.assertSQL('a > 4', 'a > 4')

    def test_less(self):
        self.assertSQL('a < 5', 'a < 5')

    def test_greater_equal(self):
        self.assertSQL('a >= 6', 'a >= 6')

    def test_less_equal(self):
        self.assertSQL('a <= 7', 'a <= 7')

    def test_and(self):
        self.assertSQL('a AND b', 'a AND b')

    def test_or(self):
        self.assertSQL('a OR b', 'a OR b')

    def test_plus(self):
        self.assertSQL('a + 3', 'a + 3')

    def test_minus(self):
        self.assertSQL('a - 3', 'a - 3')

    def test_times(self):
        self.assertSQL('a * 3', 'a * 3')

    def test_divide(self):
        self.assertSQL('a / 3', 'a / 3')

    def test_nested(self):
        self.assertSQL('a < 7 AND b > 15', 'a < 7 AND b > 15')
