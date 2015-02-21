from unittest import TestCase
import tesseract.parser as parser

class TestServer(TestCase):
    def test_insert_fail_1(self):
        try:
            parser.parse('INSERT')
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual(str(e), 'Expected table name after INSERT.')
