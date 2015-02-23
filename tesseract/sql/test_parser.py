from tesseract.sql.expressions import Value
from tesseract.sql.parser_test_case import ParserTestCase
from tesseract.sql.objects import InsertStatement
import tesseract.sql.parser as parser

class TestParser(ParserTestCase):
    def test_fail(self):
        self.assertFailure('FOO', 'Not valid SQL.')

    def test_sql_is_not_case_sensitive(self):
        result = parser.parse('insert Into foo {"foo": false}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": False}))

    def test_ignore_newline(self):
        result = parser.parse('select *\nfrom foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')

    def test_ignore_tab(self):
        result = parser.parse('select *\tfrom foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')

    def test_ignore_carriage_return(self):
        result = parser.parse('select *\rfrom foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')
