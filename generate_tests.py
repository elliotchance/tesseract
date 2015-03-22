import time
import yaml
import json
from os import listdir
import re


def escape(string):
    # SQL statement can contain `%foo%` where `foo` is the name of the instance
    # value to substitute
    variables = re.findall('%([a-z_]+)%', string)
    string = re.sub('%([a-z_]+)%', '%s', string)

    # If the SQL is only one line it can be enclosed in simple quotes.
    enclose = "'"

    # However, if the SQL is multiline then we need to use triple single quotes.
    if string.count('\n') or string.count('\r'):
        enclose = "'''"

    sql = "%s%s%s" % (enclose, string.replace("'", "\\'"), enclose)

    # If the SQL contains any `%foo%` identifiers lets create the substitution
    # now.
    if len(variables):
        values = ['self.%s' % var for var in variables]
        sql = '%s %% (%s)' % (sql, ', '.join(values))

    return sql

def get_iterator(tests_file, name):
    try:
        # Python 2.x
        return iter(sorted(tests_file[name].iteritems()))
    except:
        # Python 3.x
        return tests_file[name].items()

def process_file(file):
    total = 0
    tests_file = yaml.load(open('tests/%s' % file, 'r'))
    out = open('tests/test_%s.py' % file[:-4], 'w')

    out.write("from unittest import TestCase\n")
    out.write("from tesseract.server import Server\n")
    out.write("import random\n\n")

    out.write("class Test%s(TestCase):\n" % file[:-4].capitalize())

    out.write("    def setUp(self):\n")
    out.write("        TestCase.setUp(self)\n")
    out.write("        self.table_name = ''.join(\n")
    out.write("            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)\n")
    out.write("        )\n\n")

    if 'data' in tests_file:
        for name, table in get_iterator(tests_file, 'data'):
            out.write("    def load_%s(self, server):\n" % name)
            out.write("        server.execute('DELETE FROM %s')\n" % name)
            for row in table:
                out.write("        server.execute('INSERT INTO %s %s')\n" % (name, json.dumps(row)))
            out.write("\n")

    for name, test in get_iterator(tests_file, 'tests'):
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
        try:
            # Python 2.x
            for_range = xrange(0, len(test['sql']))
        except:
            # Python 3.x
            for_range = range(0, len(test['sql']))

        for i in for_range:
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
            out.write("        self.assertFalse(result.success, msg=result.error)\n")
            out.write("        self.assertEquals(result.error, %s)\n" % escape(test['error']))

        # Test the output of the last SQL statement
        if 'result' in test:
            out.write("        self.assertEqual(result.data, %s)\n" % \
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
