import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserDelete(ParserTestCase):
    def test_delete(self):
        result = parser.parse('DELETE FROM foo')
        self.assertEquals(result.statement, DeleteStatement("foo"))

    def test_delete_str(self):
        result = parser.parse('DELETE FROM foo')
        self.assertEquals(str(result.statement), 'DELETE FROM foo')
