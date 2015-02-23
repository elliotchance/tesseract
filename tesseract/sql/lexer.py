import ply.lex as lex

# Lexer
# =====

# SQL keywords.
sql_keywords = (
    'AND',
    'DELETE',
    'FROM',
    'INSERT',
    'INTO',
    'OR',
    'SELECT',
    'WHERE',
)

# Operators.
operators = (
    'COLON',
    'COMMA',
    'CURLY_CLOSE',
    'CURLY_OPEN',
    'EQUAL',
    'NOT_EQUAL',
    'GREATER',
    'GREATER_EQUAL',
    'LESS',
    'LESS_EQUAL',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
)

# Values and identifiers.
expression_types = (
    'FLOAT',
    'IDENTIFIER',
    'INTEGER',
    'STRING',
)

# The actual tokens used will be the aggregation of all the groups above. It is
# important that the `sql_keyword` are appended at the end since they are
# pseudo-tokens and we do not want them to interfere with read tokens.
tokens = operators + expression_types + sql_keywords

# Regular expressions for each of the tokens go here.
t_COLON = ':'
t_COMMA = ','
t_CURLY_CLOSE = '}'
t_CURLY_OPEN = '{'
t_FLOAT = '[0-9]+.[0-9]+'
t_INTEGER = r'\-?[0-9]+'
t_STRING = r'\".*?\"'
t_EQUAL = '='
t_NOT_EQUAL = '(<>)|(!=)'
t_GREATER = '>'
t_GREATER_EQUAL = '>='
t_LESS = '<'
t_LESS_EQUAL = '<='
t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_DIVIDE = r'\/'

def t_IDENTIFIER(t):
    # Expression for an identifier or keyword.
    r'[a-zA-Z_][a-zA-Z_0-9]*'

    # Check for reserved words. Be sure to convert all identifiers to upper
    # case.
    if t.value.upper() in sql_keywords:
        t.type = t.value.upper()

    return t

# Characters that can be ignored, at the moment it is only a space.
t_ignore = " \n\t\r"

def t_error(token):
    """
    Handle an unknown token.
    :type token: LexToken
    """
    raise RuntimeError("Unexpected token %s." % token.value)


# Build the lexer.
lex.lex()
