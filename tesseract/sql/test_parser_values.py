import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestServer(ParserTestCase):
    def test_integer(self):
        result = parser.parse('SELECT * FROM foo WHERE 123')
        self.assertEquals(str(result.statement.where), '123')
