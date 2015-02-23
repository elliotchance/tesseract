from unittest import TestCase
from tesseract.server import Server
import string
import random

class TestServerWhere(TestCase):
    def assertWhere(self, where, expected):
        self.table_name = ''.join(
            random.choice(string.lowercase) for i in range(8)
        )
        server = Server()
        server.execute('INSERT INTO %s {"foo": 123}' % self.table_name)
        server.execute('INSERT INTO %s {"foo": 124}' % self.table_name)
        server.execute('INSERT INTO %s {"foo": 125}' % self.table_name)
        result = server.execute(
            'SELECT * FROM %s WHERE %s' % (self.table_name, where)
        )
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted(expected))

    def test_select_where_equal(self):
        self.assertWhere('foo = 124', [{"foo": 124}])

    def test_select_where_not_equal(self):
        self.assertWhere('foo != 124', [{"foo": 123}, {"foo": 125}])

    def test_select_where_less(self):
        self.assertWhere('foo < 125', [{"foo": 123}, {"foo": 124}])

    def test_select_where_greater(self):
        self.assertWhere('foo > 123', [{"foo": 124}, {"foo": 125}])

    def test_select_where_less_equal(self):
        self.assertWhere('foo <= 124', [{"foo": 123}, {"foo": 124}])

    def test_select_where_greater_equal(self):
        self.assertWhere('foo >= 124', [{"foo": 124}, {"foo": 125}])

    def test_select_where_or(self):
        self.assertWhere('foo = 123 OR foo = 125', [{"foo": 123}, {"foo": 125}])

    def test_select_where_and(self):
        self.assertWhere('foo < 125 AND foo > 123', [{"foo": 124}])

    def test_select_where_equal_reverse(self):
        self.assertWhere('124 = foo', [{"foo": 124}])
