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
        result = server.execute('SELECT * FROM foo')
        self.assertTrue(result.success)
        self.assertEqual(result.data, [])

    def test_invalid_sql(self):
        server = Server()
        result = server.execute('INSERT INTO')
        self.assertFalse(result.success)
        self.assertEqual(result.error, 'Expected table name after INTO.')
