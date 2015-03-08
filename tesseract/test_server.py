from tesseract.server import Server
from tesseract.server_test_case import ServerTestCase


class TestServer(ServerTestCase):
    def test_providing_a_server_that_doesnt_exist(self):
        try:
            Server('nowhere')
            self.fail("Expected failure")
        except Exception as e:
            self.assertTrue(str(e).find('connecting to nowhere:6379') > 0)
