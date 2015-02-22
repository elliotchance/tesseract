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
