import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserInsert(ParserTestCase):
    def test_insert_fail_1(self):
        self.assertFailure('INSERT', 'Expected table name after INSERT.')

    def test_insert_fail_2(self):
        self.assertFailure('INSERT INTO', 'Expected table name after INTO.')

    def test_insert_fail_3(self):
        self.assertFailure('INSERT INTO foo',
                           'Expected record after table name or before INTO.')

    def test_insert(self):
        result = parser.parse('INSERT INTO foo {"foo": "bar"}')
        self.assertEquals(result.statement,
                          InsertStatement("foo", {"foo": "bar"}))
