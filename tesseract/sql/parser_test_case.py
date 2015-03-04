from unittest import TestCase
from tesseract.server import Server
from tesseract.sql.expressions import Expression
import tesseract.sql.parser as parser

class ParserTestCase(TestCase):
    def assertFailure(self, sql, message):
        try:
            server = Server()
            result = server.execute(sql)
            self.fail(result.error if not result.success else 'Expected failure')
        except Exception as e:
            self.assertEqual(message, str(e))

    def assertSQL(self, sql, expected):
        result = parser.parse('SELECT * FROM foo WHERE %s' % sql)
        self.assertEquals(Expression.to_sql(result.statement.where), expected)
        return result
