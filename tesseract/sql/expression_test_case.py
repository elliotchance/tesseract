from unittest import TestCase
from tesseract.sql.expressions import Value


class ExpressionTestCase(TestCase):
    NULL = Value(None)
    BOOLEAN_1 = Value(True)
    BOOLEAN_2 = Value(False)
    INTEGER_1 = Value(100)
    INTEGER_2 = Value(20)
    FLOAT_1 = Value(2.5)
    FLOAT_2 = Value(7.5)
    STRING_1 = Value("foo")
    STRING_2 = Value("BAR")
    ARRAY_1 = Value([123])
    ARRAY_2 = Value(["foo"])
    OBJECT_1 = Value({"foo": "bar"})
    OBJECT_2 = Value({"bar": "baz"})

    def assertExpressionFail(self, expr, message):
        try:
            expr.eval()
            self.fail("Expected failure")
        except Exception as e:
            self.assertEqual(message, str(e))

    def perform(self, name, args):
        if self.__class__.__name__[:4] != 'Test':
            return

        matrix = self.matrix()

        if isinstance(matrix[name], Exception):
            self.assertExpressionFail(
                self.expression_class()(*args),
                str(matrix[name])
            )
            return

        self.assertAlmostEqual(self.expression_class()(*args).eval(), matrix[name])

    def test_null_null(self):
        self.perform('null null', (self.NULL, self.NULL))

    def test_null_boolean(self):
        self.perform('null boolean', (self.NULL, self.BOOLEAN_2))

    def test_null_integer(self):
        self.perform('null integer', (self.NULL, self.INTEGER_2))

    def test_null_float(self):
        self.perform('null float', (self.NULL, self.FLOAT_2))

    def test_null_string(self):
        self.perform('null string', (self.NULL, self.STRING_2))

    def test_null_array(self):
        self.perform('null array', (self.NULL, self.ARRAY_2))

    def test_null_object(self):
        self.perform('null object', (self.NULL, self.OBJECT_2))

    def test_boolean_null(self):
        self.perform('boolean null', (self.BOOLEAN_1, self.NULL))

    def test_boolean_boolean(self):
        self.perform('boolean boolean', (self.BOOLEAN_1, self.BOOLEAN_2))

    def test_boolean_integer(self):
        self.perform('boolean integer', (self.BOOLEAN_1, self.INTEGER_2))

    def test_boolean_float(self):
        self.perform('boolean float', (self.BOOLEAN_1, self.FLOAT_2))

    def test_boolean_string(self):
        self.perform('boolean string', (self.BOOLEAN_1, self.STRING_2))

    def test_boolean_array(self):
        self.perform('boolean array', (self.BOOLEAN_1, self.ARRAY_2))

    def test_boolean_object(self):
        self.perform('boolean object', (self.BOOLEAN_1, self.OBJECT_2))

    def test_integer_null(self):
        self.perform('integer null', (self.INTEGER_1, self.NULL))

    def test_integer_boolean(self):
        self.perform('integer boolean', (self.INTEGER_1, self.BOOLEAN_2))

    def test_integer_integer(self):
        self.perform('integer integer', (self.INTEGER_1, self.INTEGER_2))

    def test_integer_float(self):
        self.perform('integer float', (self.INTEGER_1, self.FLOAT_2))

    def test_integer_string(self):
        self.perform('integer string', (self.INTEGER_1, self.STRING_2))

    def test_integer_array(self):
        self.perform('integer array', (self.INTEGER_1, self.ARRAY_2))

    def test_integer_object(self):
        self.perform('integer object', (self.INTEGER_1, self.OBJECT_2))

    def test_float_null(self):
        self.perform('float null', (self.FLOAT_1, self.NULL))

    def test_float_boolean(self):
        self.perform('float boolean', (self.FLOAT_1, self.BOOLEAN_2))

    def test_float_integer(self):
        self.perform('float integer', (self.FLOAT_1, self.INTEGER_2))

    def test_float_float(self):
        self.perform('float float', (self.FLOAT_1, self.FLOAT_2))

    def test_float_string(self):
        self.perform('float string', (self.FLOAT_1, self.STRING_2))

    def test_float_array(self):
        self.perform('float array', (self.FLOAT_1, self.ARRAY_2))

    def test_float_object(self):
        self.perform('float object', (self.FLOAT_1, self.OBJECT_2))

    def test_string_null(self):
        self.perform('string null', (self.STRING_1, self.NULL))

    def test_string_boolean(self):
        self.perform('string boolean', (self.STRING_1, self.BOOLEAN_2))

    def test_string_integer(self):
        self.perform('string integer', (self.STRING_1, self.INTEGER_2))

    def test_string_float(self):
        self.perform('string float', (self.STRING_1, self.FLOAT_2))

    def test_string_string(self):
        self.perform('string string', (self.STRING_1, self.STRING_2))

    def test_string_array(self):
        self.perform('string array', (self.STRING_1, self.ARRAY_2))

    def test_string_object(self):
        self.perform('string object', (self.STRING_1, self.OBJECT_2))

    def test_array_null(self):
        self.perform('array null', (self.ARRAY_1, self.NULL))

    def test_array_boolean(self):
        self.perform('array boolean', (self.ARRAY_1, self.BOOLEAN_2))

    def test_array_integer(self):
        self.perform('array integer', (self.ARRAY_1, self.INTEGER_2))

    def test_array_float(self):
        self.perform('array float', (self.ARRAY_1, self.FLOAT_2))

    def test_array_string(self):
        self.perform('array string', (self.ARRAY_1, self.STRING_2))

    def test_array_array(self):
        self.perform('array array', (self.ARRAY_1, self.ARRAY_2))

    def test_array_object(self):
        self.perform('array object', (self.ARRAY_1, self.OBJECT_2))

    def test_object_null(self):
        self.perform('object null', (self.OBJECT_1, self.NULL))

    def test_object_boolean(self):
        self.perform('object boolean', (self.OBJECT_1, self.BOOLEAN_2))

    def test_object_integer(self):
        self.perform('object integer', (self.OBJECT_1, self.INTEGER_2))

    def test_object_float(self):
        self.perform('object float', (self.OBJECT_1, self.FLOAT_2))

    def test_object_string(self):
        self.perform('object string', (self.OBJECT_1, self.STRING_2))

    def test_object_array(self):
        self.perform('object array', (self.OBJECT_1, self.ARRAY_2))

    def test_object_object(self):
        self.perform('object object', (self.OBJECT_1, self.OBJECT_2))
