import ply.yacc as yacc
import ply.lex as lex

tokens = (
    'COLON',
    'COMMA',
    'CURLY_CLOSE',
    'CURLY_OPEN',
    'IDENTIFIER',
    'INSERT',
    'INTO',
    'STRING',
)

# Tokens

t_COLON = ':'
t_COMMA = ','
t_CURLY_CLOSE = '}'
t_CURLY_OPEN = '{'
t_IDENTIFIER = r'[a-z]+'
t_INSERT = r'INSERT'
t_INTO = r'INTO'
t_STRING = r'\".*?\"'

t_ignore = " "

def t_error(token):
    """
    :type token: LexToken
    """
    raise RuntimeError("Unexpected token %s." % token.value)

# Parsing rules

precedence = ()

def p_insert_statement(p):
    """
    insert_statement : INSERT INTO IDENTIFIER json_object
                     | INSERT INTO IDENTIFIER
                     | INSERT INTO
                     | INSERT
    """
    if len(p) == 4:
        raise RuntimeError("Expected record after table name or before INTO.")
    elif len(p) == 3:
        raise RuntimeError("Expected table name after INTO.")
    elif len(p) == 2:
        raise RuntimeError("Expected table name after INSERT.")

    p.parser.statement = InsertStatement(p[3], p[4])

def p_json_object(p):
    """
    json_object : CURLY_OPEN CURLY_CLOSE
                | CURLY_OPEN json_object_items CURLY_CLOSE
    """
    if len(p) == 3:
        p[0] = {}
    else:
        p[0] = p[2]

def p_json_object_items(p):
    """
    json_object_items : json_object_item
                      | json_object_items COMMA json_object_item
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        intersection = list(set(p[1].keys()) & set(p[3].keys()))
        for key in intersection:
            message = 'Duplicate key "%s", using last value.' % key
            p.parser.warnings.append(message)

        p[0] = dict(p[1].items() + p[3].items())

def p_json_object_item(p):
    """
    json_object_item : STRING COLON STRING
    """
    p[0] = {p[1][1:-1]: p[3][1:-1]}

def p_error(p):
    pass

def parse(data):
    # Build the lexer.
    lex.lex()

    # Build the parser.
    parser = yacc.yacc()
    parser.statement = None
    parser.warnings = []

    # Run the parser.
    parser.parse(data)

    # Return the base AST tree.
    return parser

class InsertStatement:
    def __init__(self, table_name, fields):
        """
        :param table_name: str
        :param fields: dict
        """
        self.table_name = table_name
        self.fields = fields

        self.assert_type('table_name', str)
        self.assert_type('fields', dict)

    def __eq__(self, other):
        """
        Compare objects based on their attributes.
        :param other: object
        :return: boolean
        """
        assert isinstance(other, object), \
            'other is not an object, got: %r' % object

        return self.__dict__ == other.__dict__

    def assert_type(self, field_name, expected_type):
        field = getattr(self, field_name)
        assert isinstance(field, expected_type), \
            '%s is not %s, got: %r' % (field_name, expected_type, field)
