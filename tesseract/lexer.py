"""This is the lexer for the SQL parser. It handle converting the SQL into a
stream of tokens that are ingested with the parser.py module.
"""

import ply.lex as lex
from tesseract.ast import Value, Identifier

sql_keywords = (
    'ALL',
    'AND',
    'ASC',
    'BEGIN',
    'BETWEEN',
    'BY',
    'COMMIT',
    'CREATE',
    'DELETE',
    'DESC',
    'DROP',
    'EXPLAIN',
    'FROM',
    'GROUP',
    'IN',
    'INDEX',
    'INSERT',
    'INTO',
    'IS',
    'ILIKE',
    'LIKE',
    'LIMIT',
    'NOT',
    'NOTIFICATION',
    'OFFSET',
    'ON',
    'OR',
    'ORDER',
    'ROLLBACK',
    'SELECT',
    'SET',
    'START',
    'TABLE',
    'TRANSACTION',
    'UPDATE',
    'WHERE',
    'WORK',
)

operators = (
    'CARET',
    'COLON',
    'COMMA',
    'CONCAT',
    'CURLY_CLOSE',
    'CURLY_OPEN',
    'DIVIDE',
    'EQUAL',
    'GREATER',
    'GREATER_EQUAL',
    'LESS',
    'LESS_EQUAL',
    'MINUS',
    'MODULO',
    'NOT_EQUAL',
    'PARAM_CLOSE',
    'PARAM_OPEN',
    'PLUS',
    'SQUARE_CLOSE',
    'SQUARE_OPEN',
    'TIMES',
)

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
t_CARET = r'\^'
t_COLON = ':'
t_COMMA = ','
t_CONCAT = r'\|\|'
t_CURLY_CLOSE = '}'
t_CURLY_OPEN = '{'
t_DIVIDE = r'\/'
t_EQUAL = '='
t_GREATER = '>'
t_GREATER_EQUAL = '>='
t_LESS = '<'
t_LESS_EQUAL = '<='
t_MINUS = r'\-'
t_MODULO = '%'
t_NOT_EQUAL = '(<>)|(!=)'
t_PARAM_CLOSE = r'\)'
t_PARAM_OPEN = r'\('
t_PLUS = r'\+'
t_SQUARE_CLOSE = r'\]'
t_SQUARE_OPEN = r'\['
t_TIMES = r'\*'

def t_IDENTIFIER(t):
    # Expression for an identifier or keyword.
    r'[a-zA-Z_][a-zA-Z_0-9]*'

    assert isinstance(t, lex.LexToken)
    v = str(t.value).upper()

    # Check for value keywords.
    if v == 'NULL':
        t.value = Value(None)
    elif v == 'TRUE':
        t.value = Value(True)
    elif v == 'FALSE':
        t.value = Value(False)

    # Check for reserved words. Be sure to convert all identifiers to upper
    # case.
    elif v in sql_keywords:
        t.type = v
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
    """Handle an unknown token."""
    assert isinstance(token, lex.LexToken)
    raise RuntimeError("Unexpected token %s." % token.value)

# Build the lexer.
lex.lex()
