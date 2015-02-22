from unittest import TestCase
from tesseract.server import Server

class TestServer(TestCase):
    def test_insert_into_table_that_doesnt_exist(self):
        server = Server()
        result = server.execute('INSERT "foo" INTO foo')
        self.assertTrue(result)
