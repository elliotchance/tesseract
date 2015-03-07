import time
import yaml
import json
from os import listdir

def escape(string):
    enclose = "'"
    if string.find('\n'):
        enclose = "'''"
    return "%s%s%s" % (enclose, string.replace("'", "\\'"), enclose)

def process_file(file):
    total = 0
    tests_file = yaml.load(open('tests/%s' % file, 'r'))
    out = open('tests/test_%s.py' % file[:-4], 'w')

    out.write("from unittest import TestCase\n")
    out.write("from tesseract.server import Server\n\n")

    out.write("class Test%s(TestCase):\n" % file[:-4].capitalize())

    if 'data' in tests_file:
        for name, table in tests_file['data'].iteritems():
            out.write("    def load_%s(self, server):\n" % name)
            out.write("        server.execute('DELETE FROM %s')\n" % name)
            for row in table:
                out.write("        server.execute('INSERT INTO %s %s')\n" % (name, json.dumps(row)))
            out.write("\n")

    for name, test in iter(sorted(tests_file['tests'].iteritems())):
        total += 1
        out.write("    def test_%s(self):\n" % name)
        out.write("        warnings = []\n")
        out.write("        server = Server()\n")

        # Load any data sets if needed.
        if 'data' in test:
            out.write("        self.load_%s(server)\n\n" % test['data'])

        # Convert a single SQL into a list if we have to.
        if not isinstance(test['sql'], list):
            test['sql'] = [ test['sql'] ]

        # Execute each SQL statement and make sure that it passed.
        for i in xrange(0, len(test['sql'])):
            sql = test['sql'][i]
            out.write("        sql = %s\n" % escape(sql))
            out.write("        result = server.execute(sql)\n")

            # Every statement must pass except for the last one if this is an
            # error test
            if not ('error' in test and i == len(test['sql']) - 1):
                out.write("        self.assertTrue(result.success, msg=result.error)\n")

            # Catch all the warnings along the way
            out.write("        if isinstance(result.warnings, list):\n")
            out.write("            warnings.extend(result.warnings)\n")

        # An error must be asserted after the last SQL statement
        if 'error' in test:
            out.write("        self.assertFalse(result.success)\n")
            out.write("        self.assertEquals(result.error, %s)\n" % escape(test['error']))

        # Test the output of the last SQL statement
        if 'result' in test:
            out.write("        self.assertEqual(sorted(result.data), sorted(%s))\n" % \
                      test['result'])

        # If there are warnings we need to assert those at the end.
        if 'warning' in test:
            # We must always assert against an array, so convert a single
            # (str) warnings into an array.
            if not isinstance(test['warning'], list):
                test['warning'] = [ test['warning'] ]

            out.write("        self.assertEqual(warnings, %s)\n" % \
                      json.dumps(test['warning']))

        out.write("\n")

    return total


total = 0
start = time.time()
for file in listdir('tests'):
    if file.endswith('.yml'):
        total += process_file(file)

print('%d tests generated in %f seconds.' % (total, time.time() - start))
