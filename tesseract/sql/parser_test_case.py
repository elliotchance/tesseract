from unittest import TestCase
import tesseract.sql.parser as parser

class ParserTestCase(TestCase):
    def assertFailure(self, sql, message):
        try:
            parser.parse(sql)
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual(message, str(e))
