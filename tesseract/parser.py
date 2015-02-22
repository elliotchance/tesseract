import ply.yacc as yacc
import ply.lex as lex

tokens = (
    'IDENTIFIER',
    'INSERT',
    'INTO',
    'STRING',
    'CURLY_CLOSE',
    'CURLY_OPEN',
)

# Tokens

t_IDENTIFIER = r'[a-z]+'
t_INSERT = r'INSERT'
t_INTO = r'INTO'
t_STRING = r'\".*?\"'
t_CURLY_CLOSE = '}'
t_CURLY_OPEN = '{'

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

    p.parser.ast = InsertStatement({})

def p_json_object(p):
    """
    json_object : CURLY_OPEN CURLY_CLOSE
    """

def p_error(p):
    pass

def parse(data):
    # Build the lexer.
    lex.lex()

    # Build the parser.
    parser = yacc.yacc()
    parser.ast = 'a'

    # Run the parser.
    parser.parse(data)

    # Return the base AST tree.
    return parser.ast

class InsertStatement:
    def __init__(self, fields):
        """
        :param fields: dict
        """
        self.fields = fields

    def __eq__(self, other):
        """
        Compare objects based on their attributes.
        :param other: object
        :return: boolean
        """
        return self.__dict__ == other.__dict__
