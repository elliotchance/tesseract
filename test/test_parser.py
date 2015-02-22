from unittest import TestCase
import tesseract.parser as parser
from tesseract.parser import *

class TestServer(TestCase):
    def assertFailure(self, sql, message):
        try:
            parser.parse(sql)
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual(message, str(e))

    def test_insert_fail_1(self):
        self.assertFailure('INSERT', 'Expected table name after INSERT.')

    def test_insert_fail_2(self):
        self.assertFailure('INSERT INTO', 'Expected table name after INTO.')

    def test_fail(self):
        self.assertFailure('FOO', 'Not valid SQL.')

    def test_insert_fail_3(self):
        self.assertFailure('INSERT INTO foo',
                           'Expected record after table name or before INTO.')

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

    def test_insert_null(self):
        result = parser.parse('INSERT INTO foo {"foo": null}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": None}))

    def test_insert_true(self):
        result = parser.parse('INSERT INTO foo {"foo": true}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": True}))

    def test_insert_false(self):
        result = parser.parse('INSERT INTO foo {"foo": false}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": False}))

    def test_sql_is_not_case_sensitive(self):
        result = parser.parse('insert Into foo {"foo": false}')
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

    def test_select_fail_1(self):
        self.assertFailure('SELECT', 'Expected expression after SELECT.')

    def test_select_fail_2(self):
        self.assertFailure('SELECT *', 'Missing FROM clause.')

    def test_select_fail_3(self):
        self.assertFailure('SELECT * FROM', 'Expected table name after FROM.')

    def test_select(self):
        result = parser.parse('SELECT * FROM foo')
        self.assertEquals(result.statement, SelectStatement("foo"))

    def test_select_str(self):
        result = parser.parse('select * from foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')

    def test_ignore_newline(self):
        result = parser.parse('select *\nfrom foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')

    def test_ignore_tab(self):
        result = parser.parse('select *\tfrom foo')
        self.assertEquals(str(result.statement), 'SELECT * FROM foo')
