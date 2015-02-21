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
    token.parser.error = "Unexpected token %s" % token.type

# Build the lexer
import ply.lex as lex
lex.lex()

# Parsing rules

precedence = ()

def p_insert_statement(token):
    """
    insert_statement : INSERT
    """
    token.parser.error = "Expected table name after INSERT."

def p_error(token):
    if token:
        token.parser.error = "Could not parse SQL."

import ply.yacc as yacc

bparser = yacc.yacc()

def parse(data):
    bparser.error = None
    p = bparser.parse(data)
    if bparser.error:
        raise RuntimeError(bparser.error)
    return p
