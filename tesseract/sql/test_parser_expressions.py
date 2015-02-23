import tesseract.sql.parser as parser
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserExpressions(ParserTestCase):
    def test_equal(self):
        self.assertSQL('a = 1', 'a = 1')

    def test_select_where_not_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a <> 2')
        self.assertEquals(str(result.statement.where), 'a <> 2')

    def test_select_where_not_equal2(self):
        result = parser.parse('SELECT * FROM foo WHERE a != 3')
        self.assertEquals(str(result.statement.where), 'a <> 3')

    def test_select_where_greater(self):
        result = parser.parse('SELECT * FROM foo WHERE a > 4')
        self.assertEquals(str(result.statement.where), 'a > 4')

    def test_select_where_less(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 5')
        self.assertEquals(str(result.statement.where), 'a < 5')

    def test_select_where_greater_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a >= 6')
        self.assertEquals(str(result.statement.where), 'a >= 6')

    def test_select_where_less_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a <= 7')
        self.assertEquals(str(result.statement.where), 'a <= 7')

    def test_select_where_and(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 7 AND b > 15')
        self.assertEquals(str(result.statement.where), 'a < 7 AND b > 15')

    def test_select_where_or(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 7 OR b > 15')
        self.assertEquals(str(result.statement.where), 'a < 7 OR b > 15')

    def test_select_where_plus(self):
        result = parser.parse('SELECT * FROM foo WHERE a + b')
        self.assertEquals(str(result.statement.where), 'a + b')

    def test_select_where_minus(self):
        result = parser.parse('SELECT * FROM foo WHERE a - b')
        self.assertEquals(str(result.statement.where), 'a - b')

    def test_select_where_times(self):
        result = parser.parse('SELECT * FROM foo WHERE a * b')
        self.assertEquals(str(result.statement.where), 'a * b')

    def test_select_where_divide(self):
        result = parser.parse('SELECT * FROM foo WHERE a / b')
        self.assertEquals(str(result.statement.where), 'a / b')
