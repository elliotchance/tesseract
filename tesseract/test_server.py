from unittest import TestCase
from tesseract.server import Server
import string
import random

class TestServer(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.table_name = ''.join(
            random.choice(string.lowercase) for i in range(8)
        )

    def test_insert_into_table_that_doesnt_exist(self):
        server = Server()
        result = server.execute(
            'INSERT INTO %s {"foo": "bar"}' % self.table_name
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data, None)

    def test_select_from_table_that_doesnt_exist(self):
        server = Server()
        result = server.execute('SELECT * FROM %s' % self.table_name)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    def test_invalid_sql(self):
        server = Server()
        result = server.execute('INSERT INTO')
        self.assertFalse(result.success)
        self.assertEqual(result.error, 'Expected table name after INTO.')

    def test_insert_and_select(self):
        server = Server()
        server.execute('INSERT INTO %s {"foo": "bar"}' % self.table_name)
        result = server.execute('SELECT * FROM %s' % self.table_name)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [
            {"foo": "bar"},
        ])

    def test_insert_multiple_and_select(self):
        server = Server()
        server.execute('INSERT INTO %s {"foo": "bar"}' % self.table_name)
        server.execute('INSERT INTO %s {"bar": "baz"}' % self.table_name)
        result = server.execute('SELECT * FROM %s' % self.table_name)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [
            {"bar": "baz"},
            {"foo": "bar"},
        ])

    def test_providing_a_server_that_doesnt_exist(self):
        try:
            Server('nowhere')
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual('Error 8 connecting to nowhere:6379. nodename nor '
                'servname provided, or not known.', str(e))

    def test_delete(self):
        server = Server()
        server.execute('INSERT INTO %s {"foo": "bar"}' % self.table_name)
        server.execute('DELETE FROM %s' % self.table_name)
        result = server.execute('SELECT * FROM %s' % self.table_name)
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    def test_select_where_equal(self):
        server = Server()
        server.execute('INSERT INTO %s {"foo": 123}' % self.table_name)
        server.execute('INSERT INTO %s {"foo": 124}' % self.table_name)
        result = server.execute(
            'SELECT * FROM %s WHERE foo = 124' % self.table_name
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data, [{"foo": 124}])
