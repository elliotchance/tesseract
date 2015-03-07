from tesseract.server import Server
from tesseract.server_test_case import ServerTestCase


class TestServer(ServerTestCase):
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
            self.assertTrue(str(e).find('connecting to nowhere:6379') > 0)
