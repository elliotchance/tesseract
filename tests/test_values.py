import tesseract.sql.parser as parser
from tesseract.server import Server
from tesseract.sql.parser_test_case import ParserTestCase

class TestValues(ParserTestCase):
    def test_int_parse(self):
        sql = 'SELECT 123'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_int_execute(self):
        server = Server()
        sql = 'SELECT 123'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 123}]))

    def test_True_parse(self):
        sql = 'SELECT true'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_True_execute(self):
        server = Server()
        sql = 'SELECT true'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': True}]))

