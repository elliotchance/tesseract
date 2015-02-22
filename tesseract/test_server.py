from unittest import TestCase
from tesseract.server import Server

class TestServer(TestCase):
    def test_insert_into_table_that_doesnt_exist(self):
        server = Server()
        result = server.execute('INSERT INTO foo {"foo": "bar"}')
        self.assertTrue(result.success)
        self.assertEqual(result.data, None)

    def test_select_from_table_that_doesnt_exist(self):
        server = Server()
        server.redis.delete('foo')
        result = server.execute('SELECT * FROM foo')
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    def test_invalid_sql(self):
        server = Server()
        result = server.execute('INSERT INTO')
        self.assertFalse(result.success)
        self.assertEqual(result.error, 'Expected table name after INTO.')

    def test_insert_and_select(self):
        server = Server()
        server.redis.delete('foo')
        server.execute('INSERT INTO foo {"foo": "bar"}')
        result = server.execute('SELECT * FROM foo')
        self.assertTrue(result.success)
        self.assertEqual(result.data, [
            {"foo": "bar"},
        ])

    def test_insert_multiple_and_select(self):
        server = Server()
        server.redis.delete('foo')
        server.execute('INSERT INTO foo {"foo": "bar"}')
        server.execute('INSERT INTO foo {"bar": "baz"}')
        result = server.execute('SELECT * FROM foo')
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
