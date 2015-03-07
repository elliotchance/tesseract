from tesseract.server import Server
from tesseract.server_test_case import ServerTestCase
import os
import time

class TestServerBench(ServerTestCase):
    def runner(self, method):
        # We do not run these tests unless BENCH environment variable is set.
        if 'BENCH' not in os.environ:
            return

        # Create the server and start the timer.
        server = Server()
        start = time.time()

        # Run the task.
        method(server)

        # Print out the results.
        print("%s: %s seconds" % (method.__func__, time.time() - start))

    def test_all(self):
        self.runner(self.insert)
        self.runner(self.select)

    def insert(self, server):
        for x in xrange(0, 100000):
            result = server.execute('INSERT INTO %s {"id": %d}' % (self.table_name, x))
            self.assertTrue(result.success)

    def select(self, server):
        sql = 'SELECT * FROM %s WHERE id = 1' % self.table_name
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(1, len(result.data))
        self.assertEqual([{"id": 1}], result.data)
