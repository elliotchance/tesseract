import yaml
import json
from os import listdir

def process_file(file):
    tests_file = yaml.load(open('tests/%s' % file, 'r'))
    out = open('tests/test_%s.py' % file[:-4], 'w')

    out.write("import tesseract.sql.parser as parser\n")
    out.write("from tesseract.server import Server\n")
    out.write("from tesseract.sql.parser_test_case import ParserTestCase\n\n")

    out.write("class Test%s(ParserTestCase):\n" % file[:-4].capitalize())

    if 'data' in tests_file:
        for name, table in tests_file['data'].iteritems():
            out.write("    def load_%s(self, server):\n" % name)
            out.write("        server.execute('DELETE FROM %s')\n" % name)
            for row in table:
                out.write("        server.execute('INSERT INTO %s %s')\n" % (name, json.dumps(row)))
            out.write("\n")

    for name, test in iter(sorted(tests_file['tests'].iteritems())):
        if 'error' in test:
            out.write("    def test_%s(self):\n" % name)
            out.write("        self.assertFailure('%s', '%s')\n\n" % (test['sql'], test['error']))
        else:
            # We only generate a `parse` test if there is only one SQL statement
            # provided.
            if not isinstance(test['sql'], list):
                out.write("    def test_%s_parse(self):\n" % name)
                out.write("        sql = '''%s'''\n" % test['sql'])
                out.write("        result = parser.parse(sql)\n")
                if 'as' in test:
                    out.write("        sql = '''%s'''\n" % test['as'])
                out.write("        self.assertEquals(sql, str(result.statement))\n")
            out.write("\n")

            # Create the test that runs all of the SQL statements and asserts
            # the `result`.
            out.write("    def test_%s_execute(self):\n" % name)
            out.write("        server = Server()\n")
            if 'data' in test:
                out.write("        self.load_%s(server)\n\n" % test['data'])

            # Convert a single SQL into a list if we have to.
            if not isinstance(test['sql'], list):
                test['sql'] = [ test['sql'] ]

            for sql in test['sql']:
                out.write("        sql = '''%s'''\n" % sql)
                out.write("        result = server.execute(sql)\n")
                out.write("        self.assertTrue(result.success, msg=result.error)\n")

            # If there are warnings we need to assert those.
            if 'warning' in test:
                # We must always assert against an array, so convert a single
                # (str) warnings into an array.
                if not isinstance(test['warning'], list):
                    test['warning'] = [ test['warning'] ]

                out.write("        self.assertEqual(result.warnings, %s)\n" % json.dumps(test['warning']))

            # Finally assert the result of the last statement.
            if 'result' in test:
                out.write("        self.assertEqual(sorted(result.data), sorted(%s))\n" % test['result'])
            out.write("\n")


for file in listdir('tests'):
    if file.endswith('.yml'):
        process_file(file)
