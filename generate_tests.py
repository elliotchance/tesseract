import glob
import os
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

def process_tests(tests_file, out, safe_name):
    total = 0

    out.write("from unittest import TestCase\n")
    out.write("import tesseract.sql.parser as parser\n")
    out.write("import random\n\n")

    out.write("class Test%s(TestCase):\n" % safe_name.replace('_', ' ').title().replace(' ', ''))

    out.write("    def setUp(self):\n")
    out.write("        TestCase.setUp(self)\n")
    out.write("        self.table_name = ''.join(\n")
    out.write("            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)\n")
    out.write("        )\n\n")

    if 'data' in tests_file:
        for name, table in get_iterator(tests_file, 'data'):
            out.write("    def load_%s(self, server, randomize):\n" % name)
            out.write("        server.execute('DELETE FROM %s')\n" % name)
            out.write("        records = [\n")
            for row in table:
                out.write("            'INSERT INTO %s %s',\n" % (name, json.dumps(row)))
            out.write("        ]\n")
            out.write("        if randomize:\n")
            out.write("            random.shuffle(records)\n")
            out.write("        for sql in records:\n")
            out.write("            server.execute(sql)\n")
            out.write("\n")

    for name, test in get_iterator(tests_file, 'tests'):
        total += 1
        out.write("    def test_%s(self):\n" % name)

        # If the `repeat` is not set then let's set it to 1.
        if 'repeat' not in test:
            test['repeat'] = 1

        out.write("        for repeat in range(0, %d):\n" % test['repeat'])
        out.write("            warnings = []\n")
        out.write("            server = Server()\n")

        # Load any data sets if needed.
        if 'data' in test:
            out.write("            self.load_%s(server, False)\n\n" % test['data'])
        elif 'data-randomized' in test:
            out.write("            self.load_%s(server, True)\n\n" % test['data-randomized'])

        # We only generate a parse test if there is only one SQL statement
        # provided.
        if not isinstance(test['sql'], list) and 'error' not in test and 'parse' not in test:
            out.write("            sql = %s\n" % escape(test['sql']))
            out.write("            result = parser.parse(sql)\n")
            if 'as' in test:
                out.write("            sql = %s\n" % escape(test['as']))
            out.write("            self.assertEquals(sql, str(result.statement))\n")
            out.write("\n")

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
            out.write("            sql = %s\n" % escape(sql))
            out.write("            result = server.execute(sql)\n")

            # Every statement must pass except for the last one if this is an
            # error test
            if not ('error' in test and i == len(test['sql']) - 1):
                out.write("            self.assertTrue(result.success, msg=result.error)\n")

            # Catch all the warnings along the way
            out.write("            if isinstance(result.warnings, list):\n")
            out.write("                warnings.extend(result.warnings)\n")

        # An error must be asserted after the last SQL statement
        if 'error' in test:
            out.write("            self.assertFalse(result.success, msg=result.error)\n")
            out.write("            self.assertEquals(result.error, %s)\n" % escape(test['error']))

        # Test the output of the last SQL statement
        if 'result' in test:
            out.write("            self.assertEqual(result.data, %s)\n" % \
                      test['result'])

        # If there are warnings we need to assert those at the end.
        if 'warning' in test:
            # We must always assert against an array, so convert a single
            # (str) warnings into an array.
            if not isinstance(test['warning'], list):
                test['warning'] = [ test['warning'] ]

            out.write("            self.assertEqual(warnings, %s)\n" % \
                      json.dumps(test['warning']))

        out.write("\n")

    return total

def process_benchmark(tests_file, out):
    out.write("import time\n\n")

    out.write("server = Server()\n\n")
    for name, test in get_iterator(tests_file, 'benchmark'):
        out.write("# %s\n" % name)
        out.write("print('Running %s...')\n" % name)
        if 'repeat' not in test:
            test['repeat'] = 1
        out.write("start_time = time.time()\n")
        out.write("parser_time = 0\n")
        out.write("execute_time = 0\n")
        out.write("for iteration in xrange(0, %d):\n" % test['repeat'])

        # Convert a single SQL into a list if we have to.
        if not isinstance(test['sql'], list):
            test['sql'] = [ test['sql'] ]

        for sql in test['sql']:
            if 'arguments' in test:
                out.write("    result = server.execute(%s %% iteration)\n" % escape(sql))
            else:
                out.write("    result = server.execute(%s)\n" % escape(sql))
        out.write("    parser_time += result.time['parser']\n")
        out.write("    execute_time += result.time['execute']\n")
        out.write("    assert result.success\n")
        out.write("elapsed = time.time() - start_time\n")
        out.write("print('  Total: %.3f seconds' % elapsed)\n")
        out.write("print('  Parser: %.3f seconds' % parser_time)\n")
        out.write("print('  Execute: %.3f seconds' % execute_time)\n")
        out.write("\n")


def process_file(file):
    tests_file = yaml.load(open(file, 'r'))
    safe_name = file[6:-4].replace('/', '_')
    out = open('tests_cache/test_%s.py' % safe_name, 'w')

    out.write("from tesseract.server import Server\n\n")

    if 'data' in tests_file:
        for name, table in get_iterator(tests_file, 'data'):
            out.write("    def load_%s(self, server):\n" % name)
            out.write("        server.execute('DELETE FROM %s')\n" % name)
            for row in table:
                out.write("        server.execute('INSERT INTO %s %s')\n" % (name, json.dumps(row)))
            out.write("\n")

    total = 0
    if 'tests' in tests_file:
        total = process_tests(tests_file, out, safe_name)
    elif 'benchmark' in tests_file:
        process_benchmark(tests_file, out)

    return total

def process_folder(path):
    total = 0
    for file in listdir(path):
        file_path = '%s/%s' % (path, file)
        if os.path.isdir(file_path):
            total += process_folder(file_path)
        elif file.endswith('.yml'):
            total += process_file(file_path)
    return total

# Clean out the cache before we generate all the tests
for test in glob.glob("tests_cache/test_*.py"):
    os.remove(test)

start = time.time()
total = process_folder('tests')

print('%d tests generated in %f seconds.' % (total, time.time() - start))
