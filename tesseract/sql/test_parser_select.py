import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestServer(ParserTestCase):
    def test_select_fail_1(self):
        self.assertFailure('SELECT', 'Expected expression after SELECT.')

    def test_select_fail_2(self):
        self.assertFailure('SELECT *', 'Missing FROM clause.')

    def test_select_fail_3(self):
        self.assertFailure('SELECT * FROM', 'Expected table name after FROM.')

    def test_select(self):
        result = parser.parse('SELECT * FROM foo')
        self.assertEquals(result.statement, SelectStatement("foo"))

    def test_select_str(self):
        result = parser.parse('select * from foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')

    def test_select_where_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a=1')
        self.assertEquals(str(result.statement.where), 'a = 1')

    def test_select_str2(self):
        result = parser.parse('SELECT * FROM foo WHERE a=1')
        self.assertEquals(str(result.statement),
                          'SELECT * FROM foo WHERE a = 1')

    def test_select_where_identifier(self):
        result = parser.parse('SELECT * FROM foo WHERE truthy')
        self.assertEquals(str(result.statement.where), 'truthy')

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
