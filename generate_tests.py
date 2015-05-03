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

    # However, if the SQL is multi-line then we need to use triple single
    # quotes.
    if string.count('\n') or string.count('\r'):
        enclose = "'''"

    sql = "%s%s%s" % (enclose, string.replace("'", "\\'"), enclose)

    # If the SQL contains any `%foo%` identifiers lets create the substitution
    # now.
    if len(variables):
        values = ['self.%s' % var for var in variables]
        sql = '%s %% (%s)' % (sql, ', '.join(values))

    return sql

def process_file(file):
    total = 0
    tests_file = yaml.load(open(file, 'r'))
    safe_name = file[6:-4].replace('/', '_')
    out = open('tests_cache/test_%s.py' % safe_name, 'w')

    out.write("from unittest import TestCase\n")
    out.write("from tesseract.server import Server\n")
    out.write("import tesseract.sql.parser as parser\n")
    out.write("import json\n")
    out.write("import random\n\n")

    out.write("class Test%s(TestCase):\n" % safe_name.replace('_', ' ').title().replace(' ', ''))

    out.write("    def publish(self, name, value):\n")
    out.write("        self.notifications.append({'to': name, 'with': json.loads(value)})\n")

    out.write("    def setUp(self):\n")
    out.write("        TestCase.setUp(self)\n")
    out.write("        self.notifications = []\n")
    out.write("        self.table_name = ''.join(\n")
    out.write("            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)\n")
    out.write("        )\n\n")

    if 'data' in tests_file:
        for name, table in tests_file['data'].items():
            out.write("    def load_%s(self, server, randomize):\n" % name)
            out.write("        server.execute('DROP TABLE %s')\n" % name)
            out.write("        records = [\n")
            for row in table:
                out.write("            'INSERT INTO %s %s',\n" % (name, json.dumps(row)))
            out.write("        ]\n")
            out.write("        if randomize:\n")
            out.write("            random.shuffle(records)\n")
            out.write("        for sql in records:\n")
            out.write("            server.execute(sql)\n")
            out.write("\n")

    for name, test in tests_file['tests'].items():
        total += 1
        out.write("    def test_%s(self):\n" % name)

        # If the `repeat` is not set then let's set it to 1.
        if 'repeat' not in test:
            test['repeat'] = 1

        out.write("        for repeat in range(0, %d):\n" % test['repeat'])
        out.write("            warnings = []\n")
        out.write("            server = Server()\n")

        # Setup to receive notifications
        out.write("            server.publish = self.publish\n")

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
        for i in range(0, len(test['sql'])):
            sql = test['sql'][i]
            out.write("            sql = %s\n" % escape(sql))
            out.write("            result = server.execute(sql)\n")
            out.write("            if 'error' not in result:\n")
            out.write("                result['error'] = None\n")
            out.write("            if 'data' not in result:\n")
            out.write("                result['data'] = None\n")

            # Every statement must pass except for the last one if this is an
            # error test
            if not ('error' in test and i == len(test['sql']) - 1):
                out.write("            self.assertTrue(result['success'], msg=result['error'])\n")

            # Catch all the warnings along the way
            out.write("            if 'warnings' in result and isinstance(result['warnings'], list):\n")
            out.write("                warnings.extend(result['warnings'])\n")

        # An error must be asserted after the last SQL statement
        if 'error' in test:
            out.write("            self.assertFalse(result['success'], msg=result['error'])\n")
            out.write("            self.assertEquals(result['error'], %s)\n" % escape(test['error']))

        # Test the output of the last SQL statement
        if 'result' in test:
            out.write("            self.assertEqual(result['data'], %s)\n" % \
                      test['result'])
        if 'result-unordered' in test:
            out.write("            expected = %s\n" % test['result-unordered'])
            out.write("            a = sorted([json.dumps(r) for r in result['data']])\n")
            out.write("            b = sorted([json.dumps(r) for r in expected])\n")
            out.write("            self.assertEqual('\\n'.join(a), '\\n'.join(b))\n")

        # If there are warnings we need to assert those at the end.
        if 'warning' in test:
            # We must always assert against an array, so convert a single
            # (str) warnings into an array.
            if not isinstance(test['warning'], list):
                test['warning'] = [ test['warning'] ]

            out.write("            self.assertEqual(warnings, %s)\n" % \
                      json.dumps(test['warning']))

        # Check notifications.
        if 'notification' in test:
            if not isinstance(test['notification'], list):
                test['notification'] = [ test['notification'] ]
            out.write("        self.assertEqual(len(self.notifications), %s)\n" % \
                      len(test['notification']))
            for n in test['notification']:
                out.write("        self.assertTrue(%s in self.notifications)\n" % json.dumps(n))

        out.write("\n")

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
