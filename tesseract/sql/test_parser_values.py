from tesseract.sql.parser_test_case import ParserTestCase

class TestParserValues(ParserTestCase):
    def test_integer_1(self):
        self.assertSQL('123', '123')

    def test_integer_2(self):
        self.assertSQL('-123', '-123')

    def test_float_1(self):
        self.assertSQL('1.23', '1.23')

    def test_float_2(self):
        self.assertSQL('-1.23', '-1.23')

    def test_float_3(self):
        self.assertSQL('-.23', '-0.23')

    def test_float_4(self):
        self.assertSQL('1.23e3', '1230.0')

    def test_float_5(self):
        self.assertSQL('1.23e-3', '0.00123')

    def test_float_6(self):
        self.assertSQL('1.23e10', '12300000000.0')

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
