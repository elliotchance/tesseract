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
            out.write("    def test_%s_parse(self):\n" % name)
            out.write("        sql = '%s'\n" % test['sql'])
            out.write("        result = parser.parse(sql)\n")
            if 'as' in test:
                out.write("        sql = '%s'\n" % test['as'])
            out.write("        self.assertEquals(str(result.statement), sql)\n\n")

            out.write("    def test_%s_execute(self):\n" % name)
            out.write("        server = Server()\n")
            if 'data' in test:
                out.write("        self.load_%s(server)\n\n" % test['data'])

            out.write("        sql = '%s'\n" % test['sql'])
            out.write("        result = server.execute(sql)\n")
            out.write("        self.assertTrue(result.success)\n")
            out.write("        self.assertEqual(sorted(result.data), sorted(%s))\n\n" % test['result'])


for file in listdir('tests'):
    if file.endswith('.yml'):
        process_file(file)
