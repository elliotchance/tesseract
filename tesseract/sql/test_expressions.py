from tesseract.sql.expression_test_case import ExpressionTestCase
from tesseract.sql.expressions import *


class TestAndExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null AND null is not supported.'),
            "null boolean": Exception('null AND boolean is not supported.'),
            "null integer": Exception('null AND integer is not supported.'),
            "null float": Exception('null AND float is not supported.'),
            "null string": Exception('null AND string is not supported.'),
            "null array": Exception('null AND array is not supported.'),
            "null object": Exception('null AND object is not supported.'),
            "boolean null": Exception('boolean AND null is not supported.'),
            "boolean boolean": False,
            "boolean integer": Exception('boolean AND integer is not supported.'),
            "boolean float": Exception('boolean AND float is not supported.'),
            "boolean string": Exception('boolean AND string is not supported.'),
            "boolean array": Exception('boolean AND array is not supported.'),
            "boolean object": Exception('boolean AND object is not supported.'),
            "integer null": Exception('integer AND null is not supported.'),
            "integer boolean": Exception('integer AND boolean is not supported.'),
            "integer integer": Exception('integer AND integer is not supported.'),
            "integer float": Exception('integer AND float is not supported.'),
            "integer string": Exception('integer AND string is not supported.'),
            "integer array": Exception('integer AND array is not supported.'),
            "integer object": Exception('integer AND object is not supported.'),
            "float null": Exception('float AND null is not supported.'),
            "float boolean": Exception('float AND boolean is not supported.'),
            "float integer": Exception('float AND integer is not supported.'),
            "float float": Exception('float AND float is not supported.'),
            "float string": Exception('float AND string is not supported.'),
            "float array": Exception('float AND array is not supported.'),
            "float object": Exception('float AND object is not supported.'),
            "string null": Exception('string AND null is not supported.'),
            "string boolean": Exception('string AND boolean is not supported.'),
            "string integer": Exception('string AND integer is not supported.'),
            "string float": Exception('string AND float is not supported.'),
            "string string": Exception('string AND string is not supported.'),
            "string array": Exception('string AND array is not supported.'),
            "string object": Exception('string AND object is not supported.'),
            "array null": Exception('array AND null is not supported.'),
            "array boolean": Exception('array AND boolean is not supported.'),
            "array integer": Exception('array AND integer is not supported.'),
            "array float": Exception('array AND float is not supported.'),
            "array string": Exception('array AND string is not supported.'),
            "array array": Exception('array AND array is not supported.'),
            "array object": Exception('array AND object is not supported.'),
            "object null": Exception('object AND null is not supported.'),
            "object boolean": Exception('object AND boolean is not supported.'),
            "object integer": Exception('object AND integer is not supported.'),
            "object float": Exception('object AND float is not supported.'),
            "object string": Exception('object AND string is not supported.'),
            "object array": Exception('object AND array is not supported.'),
            "object object": Exception('object AND object is not supported.'),
        }

    def expression_class(self):
        return AndExpression


class TestOrExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null OR null is not supported.'),
            "null boolean": Exception('null OR boolean is not supported.'),
            "null integer": Exception('null OR integer is not supported.'),
            "null float": Exception('null OR float is not supported.'),
            "null string": Exception('null OR string is not supported.'),
            "null array": Exception('null OR array is not supported.'),
            "null object": Exception('null OR object is not supported.'),
            "boolean null": Exception('boolean OR null is not supported.'),
            "boolean boolean": True,
            "boolean integer": Exception('boolean OR integer is not supported.'),
            "boolean float": Exception('boolean OR float is not supported.'),
            "boolean string": Exception('boolean OR string is not supported.'),
            "boolean array": Exception('boolean OR array is not supported.'),
            "boolean object": Exception('boolean OR object is not supported.'),
            "integer null": Exception('integer OR null is not supported.'),
            "integer boolean": Exception('integer OR boolean is not supported.'),
            "integer integer": Exception('integer OR integer is not supported.'),
            "integer float": Exception('integer OR float is not supported.'),
            "integer string": Exception('integer OR string is not supported.'),
            "integer array": Exception('integer OR array is not supported.'),
            "integer object": Exception('integer OR object is not supported.'),
            "float null": Exception('float OR null is not supported.'),
            "float boolean": Exception('float OR boolean is not supported.'),
            "float integer": Exception('float OR integer is not supported.'),
            "float float": Exception('float OR float is not supported.'),
            "float string": Exception('float OR string is not supported.'),
            "float array": Exception('float OR array is not supported.'),
            "float object": Exception('float OR object is not supported.'),
            "string null": Exception('string OR null is not supported.'),
            "string boolean": Exception('string OR boolean is not supported.'),
            "string integer": Exception('string OR integer is not supported.'),
            "string float": Exception('string OR float is not supported.'),
            "string string": Exception('string OR string is not supported.'),
            "string array": Exception('string OR array is not supported.'),
            "string object": Exception('string OR object is not supported.'),
            "array null": Exception('array OR null is not supported.'),
            "array boolean": Exception('array OR boolean is not supported.'),
            "array integer": Exception('array OR integer is not supported.'),
            "array float": Exception('array OR float is not supported.'),
            "array string": Exception('array OR string is not supported.'),
            "array array": Exception('array OR array is not supported.'),
            "array object": Exception('array OR object is not supported.'),
            "object null": Exception('object OR null is not supported.'),
            "object boolean": Exception('object OR boolean is not supported.'),
            "object integer": Exception('object OR integer is not supported.'),
            "object float": Exception('object OR float is not supported.'),
            "object string": Exception('object OR string is not supported.'),
            "object array": Exception('object OR array is not supported.'),
            "object object": Exception('object OR object is not supported.'),
        }

    def expression_class(self):
        return OrExpression


class TestAddExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null + null is not supported.'),
            "null boolean": Exception('null + boolean is not supported.'),
            "null integer": Exception('null + integer is not supported.'),
            "null float": Exception('null + float is not supported.'),
            "null string": Exception('null + string is not supported.'),
            "null array": Exception('null + array is not supported.'),
            "null object": Exception('null + object is not supported.'),
            "boolean null": Exception('boolean + null is not supported.'),
            "boolean boolean": Exception('boolean + boolean is not supported.'),
            "boolean integer": Exception('boolean + integer is not supported.'),
            "boolean float": Exception('boolean + float is not supported.'),
            "boolean string": Exception('boolean + string is not supported.'),
            "boolean array": Exception('boolean + array is not supported.'),
            "boolean object": Exception('boolean + object is not supported.'),
            "integer null": Exception('integer + null is not supported.'),
            "integer boolean": Exception('integer + boolean is not supported.'),
            "integer integer": 120,
            "integer float": 107.5,
            "integer string": Exception('integer + string is not supported.'),
            "integer array": Exception('integer + array is not supported.'),
            "integer object": Exception('integer + object is not supported.'),
            "float null": Exception('float + null is not supported.'),
            "float boolean": Exception('float + boolean is not supported.'),
            "float integer": 22.5,
            "float float": 10,
            "float string": Exception('float + string is not supported.'),
            "float array": Exception('float + array is not supported.'),
            "float object": Exception('float + object is not supported.'),
            "string null": Exception('string + null is not supported.'),
            "string boolean": Exception('string + boolean is not supported.'),
            "string integer": Exception('string + integer is not supported.'),
            "string float": Exception('string + float is not supported.'),
            "string string": Exception('string + string is not supported.'),
            "string array": Exception('string + array is not supported.'),
            "string object": Exception('string + object is not supported.'),
            "array null": Exception('array + null is not supported.'),
            "array boolean": Exception('array + boolean is not supported.'),
            "array integer": Exception('array + integer is not supported.'),
            "array float": Exception('array + float is not supported.'),
            "array string": Exception('array + string is not supported.'),
            "array array": Exception('array + array is not supported.'),
            "array object": Exception('array + object is not supported.'),
            "object null": Exception('object + null is not supported.'),
            "object boolean": Exception('object + boolean is not supported.'),
            "object integer": Exception('object + integer is not supported.'),
            "object float": Exception('object + float is not supported.'),
            "object string": Exception('object + string is not supported.'),
            "object array": Exception('object + array is not supported.'),
            "object object": Exception('object + object is not supported.'),
        }

    def expression_class(self):
        return AddExpression


class TestSubtractExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null - null is not supported.'),
            "null boolean": Exception('null - boolean is not supported.'),
            "null integer": Exception('null - integer is not supported.'),
            "null float": Exception('null - float is not supported.'),
            "null string": Exception('null - string is not supported.'),
            "null array": Exception('null - array is not supported.'),
            "null object": Exception('null - object is not supported.'),
            "boolean null": Exception('boolean - null is not supported.'),
            "boolean boolean": Exception('boolean - boolean is not supported.'),
            "boolean integer": Exception('boolean - integer is not supported.'),
            "boolean float": Exception('boolean - float is not supported.'),
            "boolean string": Exception('boolean - string is not supported.'),
            "boolean array": Exception('boolean - array is not supported.'),
            "boolean object": Exception('boolean - object is not supported.'),
            "integer null": Exception('integer - null is not supported.'),
            "integer boolean": Exception('integer - boolean is not supported.'),
            "integer integer": 80,
            "integer float": 92.5,
            "integer string": Exception('integer - string is not supported.'),
            "integer array": Exception('integer - array is not supported.'),
            "integer object": Exception('integer - object is not supported.'),
            "float null": Exception('float - null is not supported.'),
            "float boolean": Exception('float - boolean is not supported.'),
            "float integer": -17.5,
            "float float": -5,
            "float string": Exception('float - string is not supported.'),
            "float array": Exception('float - array is not supported.'),
            "float object": Exception('float - object is not supported.'),
            "string null": Exception('string - null is not supported.'),
            "string boolean": Exception('string - boolean is not supported.'),
            "string integer": Exception('string - integer is not supported.'),
            "string float": Exception('string - float is not supported.'),
            "string string": Exception('string - string is not supported.'),
            "string array": Exception('string - array is not supported.'),
            "string object": Exception('string - object is not supported.'),
            "array null": Exception('array - null is not supported.'),
            "array boolean": Exception('array - boolean is not supported.'),
            "array integer": Exception('array - integer is not supported.'),
            "array float": Exception('array - float is not supported.'),
            "array string": Exception('array - string is not supported.'),
            "array array": Exception('array - array is not supported.'),
            "array object": Exception('array - object is not supported.'),
            "object null": Exception('object - null is not supported.'),
            "object boolean": Exception('object - boolean is not supported.'),
            "object integer": Exception('object - integer is not supported.'),
            "object float": Exception('object - float is not supported.'),
            "object string": Exception('object - string is not supported.'),
            "object array": Exception('object - array is not supported.'),
            "object object": Exception('object - object is not supported.'),
        }

    def expression_class(self):
        return SubtractExpression


class TestMultiplyExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null * null is not supported.'),
            "null boolean": Exception('null * boolean is not supported.'),
            "null integer": Exception('null * integer is not supported.'),
            "null float": Exception('null * float is not supported.'),
            "null string": Exception('null * string is not supported.'),
            "null array": Exception('null * array is not supported.'),
            "null object": Exception('null * object is not supported.'),
            "boolean null": Exception('boolean * null is not supported.'),
            "boolean boolean": Exception('boolean * boolean is not supported.'),
            "boolean integer": Exception('boolean * integer is not supported.'),
            "boolean float": Exception('boolean * float is not supported.'),
            "boolean string": Exception('boolean * string is not supported.'),
            "boolean array": Exception('boolean * array is not supported.'),
            "boolean object": Exception('boolean * object is not supported.'),
            "integer null": Exception('integer * null is not supported.'),
            "integer boolean": Exception('integer * boolean is not supported.'),
            "integer integer": 2000,
            "integer float": 750,
            "integer string": Exception('integer * string is not supported.'),
            "integer array": Exception('integer * array is not supported.'),
            "integer object": Exception('integer * object is not supported.'),
            "float null": Exception('float * null is not supported.'),
            "float boolean": Exception('float * boolean is not supported.'),
            "float integer": 50,
            "float float": 18.75,
            "float string": Exception('float * string is not supported.'),
            "float array": Exception('float * array is not supported.'),
            "float object": Exception('float * object is not supported.'),
            "string null": Exception('string * null is not supported.'),
            "string boolean": Exception('string * boolean is not supported.'),
            "string integer": Exception('string * integer is not supported.'),
            "string float": Exception('string * float is not supported.'),
            "string string": Exception('string * string is not supported.'),
            "string array": Exception('string * array is not supported.'),
            "string object": Exception('string * object is not supported.'),
            "array null": Exception('array * null is not supported.'),
            "array boolean": Exception('array * boolean is not supported.'),
            "array integer": Exception('array * integer is not supported.'),
            "array float": Exception('array * float is not supported.'),
            "array string": Exception('array * string is not supported.'),
            "array array": Exception('array * array is not supported.'),
            "array object": Exception('array * object is not supported.'),
            "object null": Exception('object * null is not supported.'),
            "object boolean": Exception('object * boolean is not supported.'),
            "object integer": Exception('object * integer is not supported.'),
            "object float": Exception('object * float is not supported.'),
            "object string": Exception('object * string is not supported.'),
            "object array": Exception('object * array is not supported.'),
            "object object": Exception('object * object is not supported.'),
        }

    def expression_class(self):
        return MultiplyExpression


class TestDivideExpression(ExpressionTestCase):
    def matrix(self):
        return {
            "null null": Exception('null / null is not supported.'),
            "null boolean": Exception('null / boolean is not supported.'),
            "null integer": Exception('null / integer is not supported.'),
            "null float": Exception('null / float is not supported.'),
            "null string": Exception('null / string is not supported.'),
            "null array": Exception('null / array is not supported.'),
            "null object": Exception('null / object is not supported.'),
            "boolean null": Exception('boolean / null is not supported.'),
            "boolean boolean": Exception('boolean / boolean is not supported.'),
            "boolean integer": Exception('boolean / integer is not supported.'),
            "boolean float": Exception('boolean / float is not supported.'),
            "boolean string": Exception('boolean / string is not supported.'),
            "boolean array": Exception('boolean / array is not supported.'),
            "boolean object": Exception('boolean / object is not supported.'),
            "integer null": Exception('integer / null is not supported.'),
            "integer boolean": Exception('integer / boolean is not supported.'),
            "integer integer": 5,
            "integer float": 13.3333333,
            "integer string": Exception('integer / string is not supported.'),
            "integer array": Exception('integer / array is not supported.'),
            "integer object": Exception('integer / object is not supported.'),
            "float null": Exception('float / null is not supported.'),
            "float boolean": Exception('float / boolean is not supported.'),
            "float integer": 0.125,
            "float float": 0.3333333,
            "float string": Exception('float / string is not supported.'),
            "float array": Exception('float / array is not supported.'),
            "float object": Exception('float / object is not supported.'),
            "string null": Exception('string / null is not supported.'),
            "string boolean": Exception('string / boolean is not supported.'),
            "string integer": Exception('string / integer is not supported.'),
            "string float": Exception('string / float is not supported.'),
            "string string": Exception('string / string is not supported.'),
            "string array": Exception('string / array is not supported.'),
            "string object": Exception('string / object is not supported.'),
            "array null": Exception('array / null is not supported.'),
            "array boolean": Exception('array / boolean is not supported.'),
            "array integer": Exception('array / integer is not supported.'),
            "array float": Exception('array / float is not supported.'),
            "array string": Exception('array / string is not supported.'),
            "array array": Exception('array / array is not supported.'),
            "array object": Exception('array / object is not supported.'),
            "object null": Exception('object / null is not supported.'),
            "object boolean": Exception('object / boolean is not supported.'),
            "object integer": Exception('object / integer is not supported.'),
            "object float": Exception('object / float is not supported.'),
            "object string": Exception('object / string is not supported.'),
            "object array": Exception('object / array is not supported.'),
            "object object": Exception('object / object is not supported.'),
        }

    def expression_class(self):
        return DivideExpression
