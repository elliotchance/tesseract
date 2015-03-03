import tesseract.sql.parser as parser
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserJson(ParserTestCase):
    def test_object_duplicate_item_raises_warning(self):
        result = self.assertSQL('{"foo": "bar", "foo": "baz"}',
                                '{"foo": "baz"}')
        self.assertEquals(result.warnings, [
            'Duplicate key "foo", using last value.'
        ])

    def test_multiple_warnings_can_be_raised(self):
        result = self.assertSQL('{"foo": "bar", "foo": "baz", "foo": "bax"}',
                                '{"foo": "bax"}')
        self.assertEquals(result.warnings, [
            'Duplicate key "foo", using last value.',
            'Duplicate key "foo", using last value.'
        ])
