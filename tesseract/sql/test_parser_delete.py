import tesseract.sql.parser as parser
from tesseract.sql.parser import *
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserDelete(ParserTestCase):
    def test_delete_fail_1(self):
        self.assertFailure('DELETE', 'Expected FROM after DELETE.')

    def test_delete_fail_2(self):
        self.assertFailure('DELETE FROM', 'Expected table name after FROM.')
