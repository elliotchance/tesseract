import tesseract.sql.parser as parser
from tesseract.sql.parser_test_case import ParserTestCase

class TestParserJson(ParserTestCase):
    def test_object_null(self):
        self.assertSQL('{"foo": null}', '{"foo": null}')

    def test_object_true(self):
        self.assertSQL('{"foo": true}', '{"foo": true}')

    def test_object_false(self):
        self.assertSQL('{"foo": false}', '{"foo": false}')

    def test_object_integer(self):
        self.assertSQL('{"foo": 123}', '{"foo": 123}')

    def test_object_float(self):
        self.assertSQL('{"foo": 1.23}', '{"foo": 1.23}')

    def test_object_empty(self):
        self.assertSQL('{}', '{}')

    def test_object_two_items(self):
        self.assertSQL('{"foo": "bar", "bar": "baz"}',
                       '{"foo": "bar", "bar": "baz"}')

    def test_object_three_items(self):
        self.assertSQL('{"foo": "bar", "bar": "baz", "abc": "def"}',
                       '{"foo": "bar", "bar": "baz", "abc": "def"}')

    def test_object_duplicate_item_uses_second(self):
        self.assertSQL('{"foo": "bar", "foo": "baz"}',
                       '{"foo": "baz"}')

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

    def test_array_empty(self):
        self.assertSQL('[]', '[]')
