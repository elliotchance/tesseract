import tesseract.sql.parser as parser
from tesseract.server import Server
from tesseract.sql.parser_test_case import ParserTestCase

class TestValues(ParserTestCase):
    def test_None_parse(self):
        sql = 'SELECT null'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_None_execute(self):
        server = Server()
        sql = 'SELECT null'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': None}]))

    def test_False_parse(self):
        sql = 'SELECT false'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_False_execute(self):
        server = Server()
        sql = 'SELECT false'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': False}]))

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

    def test_explicit_positive_float_parse(self):
        sql = 'SELECT +12.3'
        result = parser.parse(sql)
        sql = 'SELECT 12.3'
        self.assertEquals(str(result.statement), sql)

    def test_explicit_positive_float_execute(self):
        server = Server()
        sql = 'SELECT +12.3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 12.3}]))

    def test_explicit_positive_integer_parse(self):
        sql = 'SELECT +123'
        result = parser.parse(sql)
        sql = 'SELECT 123'
        self.assertEquals(str(result.statement), sql)

    def test_explicit_positive_integer_execute(self):
        server = Server()
        sql = 'SELECT +123'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 123}]))

    def test_float_parse(self):
        sql = 'SELECT 12.3'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_float_execute(self):
        server = Server()
        sql = 'SELECT 12.3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 12.3}]))

    def test_float_in_scientific_notation_parse(self):
        sql = 'SELECT 1.23e3'
        result = parser.parse(sql)
        sql = 'SELECT 1230.0'
        self.assertEquals(str(result.statement), sql)

    def test_float_in_scientific_notation_execute(self):
        server = Server()
        sql = 'SELECT 1.23e3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 1230.0}]))

    def test_float_in_scientific_notation_with_big_exponent_parse(self):
        sql = 'SELECT 1.23e10'
        result = parser.parse(sql)
        sql = 'SELECT 12300000000.0'
        self.assertEquals(str(result.statement), sql)

    def test_float_in_scientific_notation_with_big_exponent_execute(self):
        server = Server()
        sql = 'SELECT 1.23e10'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 12300000000.0}]))

    def test_float_without_preceeding_integer_parse(self):
        sql = 'SELECT -.23'
        result = parser.parse(sql)
        sql = 'SELECT -0.23'
        self.assertEquals(str(result.statement), sql)

    def test_float_without_preceeding_integer_execute(self):
        server = Server()
        sql = 'SELECT -.23'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': -0.23}]))

    def test_integer_parse(self):
        sql = 'SELECT 123'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_integer_execute(self):
        server = Server()
        sql = 'SELECT 123'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 123}]))

    def test_integer_with_exponent_parse(self):
        sql = 'SELECT 1e3'
        result = parser.parse(sql)
        sql = 'SELECT 1000.0'
        self.assertEquals(str(result.statement), sql)

    def test_integer_with_exponent_execute(self):
        server = Server()
        sql = 'SELECT 1e3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 1000.0}]))

    def test_negative_float_parse(self):
        sql = 'SELECT -12.3'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_negative_float_execute(self):
        server = Server()
        sql = 'SELECT -12.3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': -12.3}]))

    def test_negative_float_in_scientific_notation_parse(self):
        sql = 'SELECT 1.23e-3'
        result = parser.parse(sql)
        sql = 'SELECT 0.00123'
        self.assertEquals(str(result.statement), sql)

    def test_negative_float_in_scientific_notation_execute(self):
        server = Server()
        sql = 'SELECT 1.23e-3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 0.00123}]))

    def test_negative_float_in_scientific_notation_with_explicit_positive_exponent_parse(self):
        sql = 'SELECT 1.23e+3'
        result = parser.parse(sql)
        sql = 'SELECT 1230.0'
        self.assertEquals(str(result.statement), sql)

    def test_negative_float_in_scientific_notation_with_explicit_positive_exponent_execute(self):
        server = Server()
        sql = 'SELECT 1.23e+3'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 1230.0}]))

    def test_negative_integer_parse(self):
        sql = 'SELECT -123'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_negative_integer_execute(self):
        server = Server()
        sql = 'SELECT -123'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': -123}]))

    def test_string_parse(self):
        sql = 'SELECT "foo"'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_string_execute(self):
        server = Server()
        sql = 'SELECT "foo"'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'col1': 'foo'}]))

