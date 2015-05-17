from unittest import TestCase
from tesseract.server import Server


class TestServer(TestCase):
    def test_providing_a_server_that_doesnt_exist(self):
        try:
            Server('nowhere')
            self.fail("Expected failure")
        except Exception as e:
            self.assertTrue(str(e).find('connecting to nowhere:6379') > 0)
