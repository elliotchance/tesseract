from unittest import TestCase
import random

class ServerTestCase(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.table_name = ''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)
        )
