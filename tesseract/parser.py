tokens = (
    'IDENTIFIER',
    'INSERT',
    'INTO',
    'STRING',
)

# Tokens

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
    insert_statement : INSERT INTO IDENTIFIER
                     | INSERT INTO
                     | INSERT
    """
    if len(p) == 4:
        raise RuntimeError("Expected record after table name or before INTO.")
    elif len(p) == 3:
        raise RuntimeError("Expected table name after INTO.")
    else:
        raise RuntimeError("Expected table name after INSERT.")

def p_error(p):
    pass

import ply.yacc as yacc
import ply.lex as lex

def parse(data):
    # Build the lexer
    lex.lex()

    # Build the parser
    parser = yacc.yacc()

    # Run the parser
    return parser.parse(data)
