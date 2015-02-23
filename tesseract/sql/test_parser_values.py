import tesseract.sql.parser as parser
from tesseract.sql.parser import *
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

    def test_object_null(self):
        self.assertSQL('{"foo": null}', '{"foo": null}')

    def test_insert_true(self):
        result = parser.parse('INSERT INTO foo {"foo": true}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": True}))

    def test_insert_false(self):
        result = parser.parse('INSERT INTO foo {"foo": false}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": False}))

    def test_insert_integer(self):
        result = parser.parse('INSERT INTO foo {"foo": 123}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": 123}))

    def test_insert_str(self):
        result = parser.parse('INSERT INTO foo {"foo": 123}')
        self.assertEquals(str(result.statement),
                          'INSERT INTO foo {"foo": 123}')

    def test_insert_floating(self):
        result = parser.parse('INSERT INTO foo {"foo": 1.23}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": 1.23}))


    def test_insert_no_fields(self):
        result = parser.parse('INSERT INTO foo {}')
        self.assertEquals(result.statement, InsertStatement("foo", {}))

    def test_insert_one_field(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar"}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": "bar"}))

    def test_insert_two_fields(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar", "bar": "baz"}')
        self.assertEquals(result.statement, InsertStatement("foo", {
            "foo": "bar",
            "bar": "baz"
        }))

    def test_insert_three_fields(self):
        sql = 'INSERT INTO foo {"foo": "bar", "bar": "baz", "abc": "def"}'
        result = parser.parse(sql)
        self.assertEquals(result.statement, InsertStatement("foo", {
            "foo": "bar",
            "bar": "baz",
            "abc": "def"
        }))

    def test_insert_duplicate_field_uses_second(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar", "foo": "baz"}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": "baz"}))

    def test_insert_duplicate_field_raises_warning(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar", "foo": "baz"}')
        self.assertEquals(result.warnings, [
            'Duplicate key "foo", using last value.'
        ])

    def test_multiple_warnings_can_be_raised(self):
        sql = 'INSERT INTO foo {"foo": "bar", "foo": "baz", "foo": "bax"}'
        result = parser.parse(sql)
        self.assertEquals(result.warnings, [
            'Duplicate key "foo", using last value.',
            'Duplicate key "foo", using last value.'
        ])

    def test_select_where_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a=1')
        self.assertEquals(str(result.statement.where), 'a = 1')

    def test_select_str2(self):
        result = parser.parse('SELECT * FROM foo WHERE a=1')
        self.assertEquals(str(result.statement),
                          'SELECT * FROM foo WHERE a = 1')

    def test_select_where_identifier(self):
        result = parser.parse('SELECT * FROM foo WHERE truthy')
        self.assertEquals(str(result.statement.where), 'truthy')

    def test_select_where_not_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a <> 2')
        self.assertEquals(str(result.statement.where), 'a <> 2')

    def test_select_where_not_equal2(self):
        result = parser.parse('SELECT * FROM foo WHERE a != 3')
        self.assertEquals(str(result.statement.where), 'a <> 3')

    def test_select_where_greater(self):
        result = parser.parse('SELECT * FROM foo WHERE a > 4')
        self.assertEquals(str(result.statement.where), 'a > 4')

    def test_select_where_less(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 5')
        self.assertEquals(str(result.statement.where), 'a < 5')

    def test_select_where_greater_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a >= 6')
        self.assertEquals(str(result.statement.where), 'a >= 6')

    def test_select_where_less_equal(self):
        result = parser.parse('SELECT * FROM foo WHERE a <= 7')
        self.assertEquals(str(result.statement.where), 'a <= 7')

    def test_select_where_and(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 7 AND b > 15')
        self.assertEquals(str(result.statement.where), 'a < 7 AND b > 15')

    def test_select_where_or(self):
        result = parser.parse('SELECT * FROM foo WHERE a < 7 OR b > 15')
        self.assertEquals(str(result.statement.where), 'a < 7 OR b > 15')

    def test_select_where_plus(self):
        result = parser.parse('SELECT * FROM foo WHERE a + b')
        self.assertEquals(str(result.statement.where), 'a + b')

    def test_select_where_minus(self):
        result = parser.parse('SELECT * FROM foo WHERE a - b')
        self.assertEquals(str(result.statement.where), 'a - b')

    def test_select_where_times(self):
        result = parser.parse('SELECT * FROM foo WHERE a * b')
        self.assertEquals(str(result.statement.where), 'a * b')

    def test_select_where_divide(self):
        result = parser.parse('SELECT * FROM foo WHERE a / b')
        self.assertEquals(str(result.statement.where), 'a / b')
