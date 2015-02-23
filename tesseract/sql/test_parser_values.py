import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestServer(ParserTestCase):
    def test_integer(self):
        result = parser.parse('SELECT * FROM foo WHERE 123')
        self.assertEquals(Expression.to_sql(result.statement.where), '123')

    def test_float(self):
        result = parser.parse('SELECT * FROM foo WHERE 1.23')
        self.assertEquals(Expression.to_sql(result.statement.where), '1.23')

    def test_null(self):
        result = parser.parse('SELECT * FROM foo WHERE NULL')
        self.assertEquals(Expression.to_sql(result.statement.where), 'NULL')
