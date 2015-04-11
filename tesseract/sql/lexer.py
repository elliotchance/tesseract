import ply.lex as lex
from tesseract.sql.expressions import Value, Identifier

# Lexer
# =====

# SQL keywords.
sql_keywords = (
    'AND',
    'ASC',
    'BY',
    'CREATE',
    'DELETE',
    'DESC',
    'DROP',
    'FROM',
    'INSERT',
    'INTO',
    'IS',
    'LIKE',
    'NOT',
    'NOTIFICATION',
    'ON',
    'OR',
    'ORDER',
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
    'SQUARE_CLOSE',
    'SQUARE_OPEN',
    'PARAM_CLOSE',
    'PARAM_OPEN',
)

# Values and identifiers.
expression_types = (
    'NUMBER',
    'IDENTIFIER',
    'STRING_SINGLE',
    'STRING_DOUBLE',
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
t_SQUARE_CLOSE = r'\]'
t_SQUARE_OPEN = r'\['
t_PARAM_CLOSE = r'\)'
t_PARAM_OPEN = r'\('

def t_IDENTIFIER(t):
    # Expression for an identifier or keyword.
    r'[a-zA-Z_][a-zA-Z_0-9]*'

    # Check for value keywords.
    if t.value.upper() == 'NULL':
        t.value = Value(None)
    elif t.value.upper() == 'TRUE':
        t.value = Value(True)
    elif t.value.upper() == 'FALSE':
        t.value = Value(False)

    # Check for reserved words. Be sure to convert all identifiers to upper
    # case.
    elif t.value.upper() in sql_keywords:
        t.type = t.value.upper()
        t.value = t.type

    # If all the above fail then it really is an identifier.
    else:
        # The extra `str()` conversion here is to handle `unicode`.
        t.value = Identifier(str(t.value))

    return t

def t_NUMBER(t):
    r'([0-9]*\.)?[0-9]+(e[\-\+]?\d+)?'

    if '.' in t.value or 'e' in t.value:
        t.value = Value(float(t.value))
    else:
        t.value = Value(int(t.value))

    return t

def t_STRING_DOUBLE(t):
    r'\".*?\"'

    t.value = Value(t.value[1:-1])
    return t

def t_STRING_SINGLE(t):
    r'\'.*?\''

    t.value = Value(t.value[1:-1])
    return t

# Characters that can be ignored.
t_ignore = " \n\t\r"

def t_error(token):
    """
    Handle an unknown token.
    :type token: LexToken
    """
    raise RuntimeError("Unexpected token %s." % token.value)


# Build the lexer.
lex.lex()
