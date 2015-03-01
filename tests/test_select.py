import tesseract.sql.parser as parser
from tesseract.server import Server
from tesseract.sql.parser_test_case import ParserTestCase

class TestSelect(ParserTestCase):
    def load_table1(self, server):
        server.execute('DELETE FROM table1')
        server.execute('INSERT INTO table1 {"foo": 123}')
        server.execute('INSERT INTO table1 {"foo": 124}')
        server.execute('INSERT INTO table1 {"foo": 125}')

    def test_fail_1(self):
        self.assertFailure('SELECT', 'Expected expression after SELECT.')

    def test_fail_2(self):
        self.assertFailure('SELECT *', 'Missing FROM clause.')

    def test_fail_3(self):
        self.assertFailure('SELECT * FROM', 'Expected table name after FROM.')

    def test_simple_parse(self):
        sql = 'SELECT * FROM table1'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_simple_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 123}, {'foo': 124}, {'foo': 125}]))

    def test_where_add_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo = 100 + 24'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_add_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo = 100 + 24'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_divide_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo = 248 / 2'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_divide_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo = 248 / 2'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_equal_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo = 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_equal_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo = 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_equal_reverse_parse(self):
        sql = 'SELECT * FROM table1 WHERE 124 = foo'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_equal_reverse_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE 124 = foo'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_greater_than_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo > 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_greater_than_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo > 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 125}]))

    def test_where_greater_than_equal_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo >= 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_greater_than_equal_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo >= 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}, {'foo': 125}]))

    def test_where_less_than_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo < 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_less_than_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo < 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 123}]))

    def test_where_less_than_equal_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo <= 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_less_than_equal_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo <= 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 123}, {'foo': 124}]))

    def test_where_multiply_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo = 62 * 2'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_multiply_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo = 62 * 2'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_not_equal_1_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo <> 124'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_not_equal_1_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo <> 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 123}, {'foo': 125}]))

    def test_where_not_equal_2_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo != 124'
        result = parser.parse(sql)
        sql = 'SELECT * FROM table1 WHERE foo <> 124'
        self.assertEquals(str(result.statement), sql)

    def test_where_not_equal_2_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo != 124'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 123}, {'foo': 125}]))

    def test_where_or_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo > 123 AND foo < 125'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_or_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo > 123 AND foo < 125'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

    def test_where_subtract_parse(self):
        sql = 'SELECT * FROM table1 WHERE foo = 150 - 26'
        result = parser.parse(sql)
        self.assertEquals(str(result.statement), sql)

    def test_where_subtract_execute(self):
        server = Server()
        self.load_table1(server)

        sql = 'SELECT * FROM table1 WHERE foo = 150 - 26'
        result = server.execute(sql)
        self.assertTrue(result.success)
        self.assertEqual(sorted(result.data), sorted([{'foo': 124}]))

