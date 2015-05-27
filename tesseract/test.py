"""This module converts the YAML tests in the tests/ directory into python
tests.

Attributes:
  port (int): A random port number that the server will run on. Is is important
    that this is different each time the suite is created so that subsequent
    runs do not give the dreaded "Address already in use.". However, it is not
    safe to run multiple suites at the same time.
"""

import glob
import random
import threading
import time
import unittest
import sys
import yaml
import json
import os
import re


port = random.randint(1000, 10000)
notifications = []
tests_run = 0
total_tests = 0
s = None

try:
    with open('tests_cache/total_tests', 'r') as f:
        total_tests = int(f.read())
except:
    pass

class YAMLTestCase(unittest.TestCase):
    """The base TestCase for all YAML tests."""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.table_name = ''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)
        )

    def tearDown(self):
        global tests_run, s
        tests_run += 1
        if tests_run == total_tests:
            s.exit()

        unittest.TestCase.tearDown(self)

    def publish(self, name, value):
        global notifications
        notifications.append({'to': name, 'with': json.loads(value)})

    def get_client(self, port):
        from tesseract import client
        from tesseract import server

        try:
            return client.Client(port=port)
        except:
            global s
            s = server.Server(port=port)
            s.instance.publish = self.publish
            s.instance.log = lambda _: 0

            thread = threading.Thread(target=s.start)
            thread.start()

            while not s.is_ready:
                time.sleep(0.01)

            return client.Client(port=port)

    def load_table(self, connection, table_name, records, randomize=False):
        connection.execute('DROP TABLE %s' % table_name)

        if randomize:
            random.shuffle(records)

        for record in records:
            sql = 'INSERT INTO %s %s' % (table_name, json.dumps(record))
            connection.execute(sql)

    def assert_result_unordered(self, expected):
        a = sorted([json.dumps(r, sort_keys=True) for r in self.result])
        b = sorted([json.dumps(r, sort_keys=True) for r in expected])
        self.assertEqual('\n'.join(a), '\n'.join(b))

    def assert_notifications(self, expected):
        global notifications
        self.assertEqual(len(notifications), len(expected))
        for n in expected:
            self.assertTrue(n in notifications)

    def assert_parser(self, sql, sql_as=None):
        from tesseract import parser
        result = parser.parse(sql)
        if sql_as:
            sql = sql_as
        self.assertEquals(sql, str(result.statement))

    def execute(self, connection, sql, must_succeed=False):
        from tesseract import client
        assert isinstance(connection, client.Client)

        try:
            self.result = connection.execute(sql)
            self.warnings = connection.warnings
        except Exception as e:
            self.error = str(e)
            if must_succeed:
                self.fail(self.error)

    def assert_success(self, connection, sql):
        self.execute(connection, sql, must_succeed=True)

    def assert_result(self, expected):
        self.assertEqual(self.result, expected)

    def assert_error(self, message):
        self.assertEquals(self.error, message)

    def assert_warnings(self, warnings):
        if not isinstance(warnings, list):
            warnings = [warnings]

        self.assertEqual(self.warnings, [w.strip() for w in warnings])


class TestGenerator(object):
    def __init__(self):
        self.total_tests = 0
        self.__start = time.time()
        self.exclude = []

    def clean_all(self):
        """Clean out the cache before we generate all the tests."""
        for test in glob.glob("tests_cache/test_*.py"):
            os.remove(test)

    def elapsed_time(self):
        return time.time() - self.__start

    def process_folder(self, path):
        """Process all the files (recursively) in a directory.

        Arguments:
          path (str): The path (can be relative or absolute).
        """
        assert isinstance(path, str)

        for file in os.listdir(path):
            file_path = '%s/%s' % (path, file)
            if os.path.isdir(file_path):
                self.process_folder(file_path)
            elif file.endswith('.yml'):
                self.process_file(file_path)

    def process_file(self, file):
        """Process a single file.

        Arguments:
          file (str): The path (can be relative or absolute).
        """
        assert isinstance(file, str)

        tests_file = yaml.load(open(file, 'r'))
        safe_name = file[6:-4].replace('/', '_')
        self.__out = open('tests_cache/test_%s.py' % safe_name, 'w')

        if 'tests' not in tests_file:
            return

        if 'tags' in tests_file:
            match = list(set(tests_file['tags'].split(' ')) & set(self.exclude))
            if match:
                return

        self.__write_header(safe_name)
        self.__render_data(tests_file)
        self.__render_tests(tests_file)

    def __render_tests(self, tests_file):
        for name, test in tests_file['tests'].items():
            self.__render_test(name, test)

    def __render_test(self, name, test):
        self.total_tests += 1

        self.__write("def test_%s(self):\n" % name, 1)
        doc = yaml.dump(test, default_flow_style=False)
        doc = str(doc).replace('\n', '\n        ')
        self.__write('"""\n        %s"""\n' % doc, 2)

        # If the `repeat` is not set then let's set it to 1.
        if 'repeat' not in test:
            test['repeat'] = 1

        self.__write("for repeat in range(0, %d):\n" % test['repeat'], 2)
        self.__write("try:\n", 3)
        self.__write("    test.notifications = []\n", 3)
        self.__write("    self.warnings = []\n\n", 3)

        if 'multi' in test:
            clients = sorted(set([title.split('-')[1] for title in test['multi']]))

            for client in clients:
                self.__write("connection_%s = self.get_client(%d)\n" % (client, port), 4)

            for step in sorted(test['multi']):
                client_name = step.split('-')[1]
                self.__write("\n")
                self.__write("connection = connection_%s\n" % client_name, 4)
                self.__render_single_test(test['multi'][step])

            self.__write("finally:\n", 3)
            for client in clients:
                self.__write("connection_%s.close()\n" % client, 4)
            self.__write("\n")
        else:
            self.__write("connection = self.get_client(%d)\n" % port, 4)
            self.__render_single_test(test)
            self.__write("finally:\n", 3)
            self.__perform_finally(test)
            self.__write("connection.close()\n", 4)

        self.__write("\n")

    def __perform_finally(self, test):
        if 'finally' not in test:
            test['finally'] = []
        if not isinstance(test['finally'], list):
            test['finally'] = [test['finally']]

        for f in test['finally']:
            self.__write("self.execute(connection, %s)\n" % self.__escape(f), 4)

    def __render_single_test(self, test):
        self.__load_data_for_test(test)
        self.__generate_parser_test(test)

        if not isinstance(test['sql'], list):
            test['sql'] = [test['sql']]

        self.__execute_each_sql_statement(test)
        self.__check_error(test)
        self.__check_result(test)
        self.__check_warnings(test)
        self.__check_notifications(test)

    def __check_notifications(self, test):
        """Check notifications."""
        if 'notification' in test:
            if not isinstance(test['notification'], list):
                test['notification'] = [test['notification']]

            notifications = json.dumps(test['notification'])
            self.__write("self.assert_notifications(%s)\n" % notifications, 4)

    def __check_warnings(self, test):
        """If there are warnings we need to assert those at the end."""
        if 'warning' in test:
            warnings = json.dumps(test['warning'])
            self.__write("self.assert_warnings(%s)\n" % warnings, 4)

    def __check_result(self, test):
        """Test the output of the last SQL statement."""
        if 'result' in test:
            line = "self.assert_result(%s)\n" % test['result']
            self.__write(line, 4)

        if 'result-unordered' in test:
            self.__write("self.assert_result_unordered(%s)\n" % test['result-unordered'], 4)

    def __check_error(self, test):
        """An error must be asserted after the last SQL statement."""
        if 'error' in test:
            line = "self.assert_error(%s)\n" % self.__escape(test['error'])
            self.__write(line, 4)

    def __execute_each_sql_statement(self, test):
        """Execute each SQL statement and make sure that it passes."""
        for i in range(0, len(test['sql'])):
            sql = test['sql'][i]

            # Every statement must pass except for the last one if this is an
            # error test
            if 'error' in test and i == len(test['sql']) - 1:
                self.__write("self.execute(connection, %s)\n" % self.__escape(sql), 4)
            else:
                self.__write("self.assert_success(connection, %s)\n" % self.__escape(sql), 4)

    def __generate_parser_test(self, test):
        """We only generate a parser test if there is only one SQL statement
        provided.
        """
        single_sql = not isinstance(test['sql'], list)
        if single_sql and 'error' not in test and 'parse' not in test:
            if 'as' in test:
                self.__write("self.assert_parser(\n", 4)
                self.__write("    %s,\n" % self.__escape(test['sql']), 4)
                self.__write("    %s\n" % self.__escape(test['as']), 4)
                self.__write(")\n", 4)
            else:
                self.__write("self.assert_parser(%s)\n" % self.__escape(test['sql']), 4)

    def __write(self, line, indent=0):
        assert isinstance(indent, int)
        assert isinstance(line, str)
        self.__out.write('    ' * indent)
        self.__out.write(line)

    def __load_data_for_test(self, test):
        """Load any data sets if needed for the test."""
        if 'data' in test:
            self.__write("self.load_table(connection, '%s', self.TABLE_%s)\n" % (
                test['data'],
                test['data'].upper()
            ), 4)

        if 'data-randomized' in test:
            self.__write("self.load_table(connection, '%s', self.TABLE_%s, randomize=True)\n" % (
                test['data-randomized'],
                test['data-randomized'].upper()
            ), 4)

    def __render_data(self, tests_file):
        if 'data' in tests_file:
            for name, table in tests_file['data'].items():
                self.__write("    TABLE_%s = [\n" % name.upper())
                for row in table:
                    self.__write("        %s,\n" % row)
                self.__write("    ]\n\n")

    def __write_header(self, safe_name):
        self.__write("from tesseract import parser\n")
        self.__write("from tesseract import client\n")
        self.__write("from tesseract import test\n\n")

        title = safe_name.replace('_', ' ').title().replace(' ', '')
        self.__write("class Test%s(test.YAMLTestCase):\n" % title)

    def __escape(self, string):
        # SQL statement can contain `%foo%` where `foo` is the name of the
        # instance value to substitute
        variables = re.findall('%([a-z_]+)%', string)
        string = re.sub('%([a-z_]+)%', '%s', string)

        # If the SQL is only one line it can be enclosed in simple quotes.
        enclose = "'"

        # However, if the SQL is multi-line then we need to use triple single
        # quotes.
        if string.count('\n') or string.count('\r'):
            enclose = "'''"

        sql = "%s%s%s" % (enclose, string.replace("'", "\\'"), enclose)

        # If the SQL contains any `%foo%` identifiers lets create the
        # substitution now.
        if len(variables):
            values = ['self.%s' % var for var in variables]
            sql = '%s %% (%s)' % (sql, ', '.join(values))

        return sql


if __name__ == "__main__":
    generator = TestGenerator()
    generator.clean_all()
    generator.exclude = [e[1:] for e in sys.argv[1:]]
    generator.process_folder('tests')

    print('%d tests generated in %f seconds.' % (
        generator.total_tests,
        generator.elapsed_time()
    ))

    with open('tests_cache/total_tests', 'w') as f:
        f.write(str(generator.total_tests))
