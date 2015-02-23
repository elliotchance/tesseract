from tesseract.sql.parser_test_case import ParserTestCase

class TestParserValues(ParserTestCase):
    def test_integer(self):
        self.assertSQL('123', '123')

    def test_float(self):
        self.assertSQL('1.23', '1.23')

    def test_null(self):
        self.assertSQL('NULL', 'null')

    def test_true(self):
        self.assertSQL('TRUE', 'true')

    def test_false(self):
        self.assertSQL('FALSE', 'false')

    def test_identifier(self):
        self.assertSQL('truthy', 'truthy')

    def test_identifier_case(self):
        self.assertSQL('Truthy', 'Truthy')

    def test_string(self):
        self.assertSQL('"false"', '"false"')
