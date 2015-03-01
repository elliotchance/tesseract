from tesseract.sql.parser_test_case import ParserTestCase

class TestParserValues(ParserTestCase):
    def test_identifier(self):
        self.assertSQL('truthy', 'truthy')

    def test_identifier_case(self):
        self.assertSQL('Truthy', 'Truthy')

    def test_string(self):
        self.assertSQL('"false"', '"false"')
