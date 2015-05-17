"""This module converts the YAML tests in the tests/ directory into python
tests.
"""

import glob
import os
import random
import time
from unittest import TestCase
import yaml
import json
from os import listdir
import re


class YAMLTestCase(TestCase):
    """The base TestCase for all YAML tests."""

    def setUp(self):
        TestCase.setUp(self)
        self.notifications = []
        self.table_name = ''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)
        )

    def publish(self, name, value):
        self.notifications.append({'to': name, 'with': json.loads(value)})

    def load_table(self, table_name, records, randomize=False):
        self.server._execute('DROP TABLE %s' % table_name)

        if randomize:
            random.shuffle(records)

        for record in records:
            sql = 'INSERT INTO %s %s' % (table_name, json.dumps(record))
            self.server._execute(sql)

    def begin_iteration(self):
        import tesseract.server
        self.warnings = []
        self.server = tesseract.server.Server()
        self.server._publish = self.publish

    def assert_result_unordered(self, expected):
        a = sorted([json.dumps(r, sort_keys=True) for r in self.result['data']])
        b = sorted([json.dumps(r, sort_keys=True) for r in expected])
        self.assertEqual('\n'.join(a), '\n'.join(b))

    def assert_notifications(self, expected):
        self.assertEqual(len(self.notifications), len(expected))
        for n in expected:
            self.assertTrue(n in self.notifications)

    def assert_parser(self, sql, sql_as=None):
        from tesseract import parser
        result = parser.parse(sql)
        if sql_as:
            sql = sql_as
        self.assertEquals(sql, str(result.statement))

    def execute(self, sql, must_succeed=False):
        result = self.server._execute(sql)

        if 'error' not in result:
            result['error'] = None

        if 'data' not in result:
            result['data'] = None

        if must_succeed:
            self.assertTrue(result['success'], msg=result['error'])

        # Catch all the warnings along the way
        if 'warnings' in result and isinstance(result['warnings'], list):
            self.warnings.extend(result['warnings'])

        self.result = result

    def assert_success(self, sql):
        self.execute(sql, must_succeed=True)

    def assert_result(self, expected):
        self.assertEqual(self.result['data'], expected)

    def assert_error(self, message):
        self.assertFalse(self.result['success'], msg=self.result['error'])
        self.assertEquals(self.result['error'], message)

    def assert_warnings(self, warnings):
        if not isinstance(warnings, list):
            warnings = [warnings]
        self.assertEqual(self.warnings, warnings)

class TestGenerator(object):
    def __init__(self):
        self.total_tests = 0
        self.__start = time.time()

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

        for file in listdir(path):
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
        self.__write("    self.begin_iteration()\n", 2)

        self.__load_data_for_test(test)
        self.__generate_parser_test(test)

        # Convert a single SQL into a list if we have to.
        if not isinstance(test['sql'], list):
            test['sql'] = [test['sql']]

        self.__execute_each_sql_statement(test)

        self.__check_error(test)
        self.__check_result(test)
        self.__check_warnings(test)
        self.__check_notifications(test)

        self.__write("\n")

    def __check_notifications(self, test):
        """Check notifications."""
        if 'notification' in test:
            if not isinstance(test['notification'], list):
                test['notification'] = [test['notification']]

            notifications = json.dumps(test['notification'])
            self.__write("self.assert_notifications(%s)\n" % notifications, 3)

    def __check_warnings(self, test):
        """If there are warnings we need to assert those at the end."""
        if 'warning' in test:
            warnings = json.dumps(test['warning'])
            self.__write("self.assert_warnings(%s)\n" % warnings, 3)

    def __check_result(self, test):
        """Test the output of the last SQL statement."""
        if 'result' in test:
            line = "self.assert_result(%s)\n" % test['result']
            self.__write(line, 3)

        if 'result-unordered' in test:
            self.__write("self.assert_result_unordered(%s)\n" % test['result-unordered'], 3)

    def __check_error(self, test):
        """An error must be asserted after the last SQL statement."""
        if 'error' in test:
            line = "self.assert_error(%s)\n" % self.__escape(test['error'])
            self.__write(line, 3)

    def __execute_each_sql_statement(self, test):
        """Execute each SQL statement and make sure that it passes."""
        for i in range(0, len(test['sql'])):
            sql = test['sql'][i]

            # Every statement must pass except for the last one if this is an
            # error test
            if 'error' in test and i == len(test['sql']) - 1:
                self.__write("self.execute(%s)\n" % self.__escape(sql), 3)
            else:
                self.__write("self.assert_success(%s)\n" % self.__escape(sql), 3)

    def __generate_parser_test(self, test):
        """We only generate a parser test if there is only one SQL statement
        provided.
        """
        single_sql = not isinstance(test['sql'], list)
        if single_sql and 'error' not in test and 'parse' not in test:
            if 'as' in test:
                self.__write("self.assert_parser(\n", 3)
                self.__write("    %s,\n" % self.__escape(test['sql']), 3)
                self.__write("    %s\n" % self.__escape(test['as']), 3)
                self.__write(")\n", 3)
            else:
                self.__write("self.assert_parser(%s)\n" % self.__escape(test['sql']), 3)

    def __write(self, line, indent=0):
        assert isinstance(indent, int)
        assert isinstance(line, str)
        self.__out.write('    ' * indent)
        self.__out.write(line)

    def __load_data_for_test(self, test):
        """Load any data sets if needed for the test."""
        if 'data' in test:
            self.__write("self.load_table('%s', self.TABLE_%s)\n" % (
                test['data'],
                test['data'].upper()
            ), 3)

        if 'data-randomized' in test:
            self.__write("self.load_table('%s', self.TABLE_%s, randomize=True)\n" % (
                test['data-randomized'],
                test['data-randomized'].upper()
            ), 3)

    def __render_data(self, tests_file):
        if 'data' in tests_file:
            for name, table in tests_file['data'].items():
                self.__write("    TABLE_%s = [\n" % name.upper())
                for row in table:
                    self.__write("        %s,\n" % row)
                self.__write("    ]\n\n")

    def __write_header(self, safe_name):
        self.__write("import tesseract.parser as parser\n")
        self.__write("from tesseract.test import YAMLTestCase\n\n")

        title = safe_name.replace('_', ' ').title().replace(' ', '')
        self.__write("class Test%s(YAMLTestCase):\n" % title)

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

class YAMLTestCase(TestCase):
    """The base TestCase for all YAML tests."""

    def setUp(self):
        TestCase.setUp(self)
        self.notifications = []
        self.table_name = ''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)
        )

    def publish(self, name, value):
        self.notifications.append({'to': name, 'with': json.loads(value)})

    def load_table(self, table_name, records, randomize=False):
        self.server._execute('DROP TABLE %s' % table_name)

        if randomize:
            random.shuffle(records)

        for record in records:
            sql = 'INSERT INTO %s %s' % (table_name, json.dumps(record))
            self.server._execute(sql)

    def begin_iteration(self):
        import tesseract.server
        self.warnings = []
        self.server = tesseract.server.Server()
        self.server._publish = self.publish

    def assert_result_unordered(self, expected):
        a = sorted([json.dumps(r, sort_keys=True) for r in self.result['data']])
        b = sorted([json.dumps(r, sort_keys=True) for r in expected])
        self.assertEqual('\n'.join(a), '\n'.join(b))

    def assert_notifications(self, expected):
        self.assertEqual(len(self.notifications), len(expected))
        for n in expected:
            self.assertTrue(n in self.notifications)

    def assert_parser(self, sql, sql_as=None):
        from tesseract import parser
        result = parser.parse(sql)
        if sql_as:
            sql = sql_as
        self.assertEquals(sql, str(result.statement))

    def execute(self, sql, must_succeed=False):
        result = self.server._execute(sql)

        if 'error' not in result:
            result['error'] = None

        if 'data' not in result:
            result['data'] = None

        if must_succeed:
            self.assertTrue(result['success'], msg=result['error'])

        # Catch all the warnings along the way
        if 'warnings' in result and isinstance(result['warnings'], list):
            self.warnings.extend(result['warnings'])

        self.result = result

    def assert_success(self, sql):
        self.execute(sql, must_succeed=True)

    def assert_result(self, expected):
        self.assertEqual(self.result['data'], expected)

    def assert_error(self, message):
        self.assertFalse(self.result['success'], msg=self.result['error'])
        self.assertEquals(self.result['error'], message)

    def assert_warnings(self, warnings):
        if not isinstance(warnings, list):
            warnings = [warnings]
        self.assertEqual(self.warnings, warnings)

if __name__ == "__main__":
    generator = TestGenerator()
    generator.clean_all()
    generator.process_folder('tests')

    print('%d tests generated in %f seconds.' % (
        generator.total_tests,
        generator.elapsed_time()
    ))
