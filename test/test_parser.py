from unittest import TestCase
import tesseract.parser as parser
from tesseract.parser import *

class TestServer(TestCase):
    def assertFailure(self, sql, message):
        try:
            parser.parse(sql)
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual(str(e), message)

    def test_insert_fail_1(self):
        self.assertFailure('INSERT', 'Expected table name after INSERT.')

    def test_insert_fail_2(self):
        self.assertFailure('INSERT INTO', 'Expected table name after INTO.')

    def test_fail(self):
        self.assertFailure('FOO', 'Unexpected token FOO.')

    def test_insert_fail_3(self):
        self.assertFailure('INSERT INTO foo',
                           'Expected record after table name or before INTO.')

    def test_insert_no_fields(self):
        result = parser.parse('INSERT INTO foo {}')
        self.assertEquals(result, InsertStatement({}))

    def test_insert_one_field(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar"}')
        self.assertEquals(result, InsertStatement({"foo": "bar"}))

    def test_insert_two_fields(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar", "bar": "baz"}')
        self.assertEquals(result, InsertStatement({"foo": "bar", "bar": "baz"}))
