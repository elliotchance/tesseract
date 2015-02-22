import ply.yacc as yacc
import ply.lex as lex
import json

# Lexer
# =====

# SQL keywords.
sql_keywords = (
    'FALSE',
    'FROM',
    'INSERT',
    'INTO',
    'NULL',
    'SELECT',
    'TRUE',
)

# Operators.
operators = (
    'ASTERISK',
    'COLON',
    'COMMA',
    'CURLY_CLOSE',
    'CURLY_OPEN',
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
t_ASTERISK = r'\*'
t_COLON = ':'
t_COMMA = ','
t_CURLY_CLOSE = '}'
t_CURLY_OPEN = '{'
t_FLOAT = '[0-9]+.[0-9]+'
t_INTEGER = '[0-9]+'
t_STRING = r'\".*?\"'

def t_IDENTIFIER(t):
    # Expression for an identifier or keyword.
    r'[a-zA-Z_][a-zA-Z_0-9]*'

    # Check for reserved words. Be sure to convert all identifiers to upper
    # case.
    if t.value.upper() in sql_keywords:
        t.type = t.value.upper()

    return t

# Characters that can be ignored, at the moment it is only a space.
t_ignore = " "

def t_error(token):
    """
    Handle an unknown token.
    :type token: LexToken
    """
    raise RuntimeError("Unexpected token %s." % token.value)

# Parser
# ======

# Set precedence for operators. We do not need these yet.
precedence = ()


# statement
# ---------
def p_statement(p):
    """
        statement : insert_statement
                  | select_statement
    """

    # Which ever statement matches can be passed straight through.
    p.parser.statement = p[1]


# select_statement
# ----------------
def p_select_statement(p):
    """
        select_statement : SELECT ASTERISK FROM IDENTIFIER
                         | SELECT ASTERISK FROM
                         | SELECT ASTERISK
                         | SELECT
    """

    #     SELECT
    if len(p) == 2:
        raise RuntimeError("Expected expression after SELECT.")

    #     SELECT ASTERISK
    if len(p) == 3:
        raise RuntimeError("Missing FROM clause.")

    #     SELECT ASTERISK FROM
    if len(p) == 4:
        raise RuntimeError("Expected table name after FROM.")

    #     SELECT ASTERISK FROM IDENTIFIER
    # This looks like a valid `SELECT`
    p[0] = SelectStatement(p[4])


# insert_statement
# ----------------
def p_insert_statement(p):
    """
        insert_statement : INSERT INTO IDENTIFIER json_object
                         | INSERT INTO IDENTIFIER
                         | INSERT INTO
                         | INSERT
    """

    #     INSERT INTO IDENTIFIER
    if len(p) == 4:
        raise RuntimeError("Expected record after table name or before INTO.")

    #     INSERT INTO
    elif len(p) == 3:
        raise RuntimeError("Expected table name after INTO.")

    #     INSERT
    elif len(p) == 2:
        raise RuntimeError("Expected table name after INSERT.")

    #     INSERT INTO IDENTIFIER json_object
    # We have a working `INSERT` statement.
    p[0] = InsertStatement(p[3], p[4])


# json_object
# -----------
def p_json_object(p):
    """
        json_object : CURLY_OPEN CURLY_CLOSE
                    | CURLY_OPEN json_object_items CURLY_CLOSE
    """

    #     CURLY_OPEN CURLY_CLOSE
    if len(p) == 3:
        p[0] = {}
        return

    #     CURLY_OPEN json_object_items CURLY_CLOSE
    p[0] = p[2]


# json_object_items
# -----------------
def p_json_object_items(p):
    """
        json_object_items : json_object_item
                          | json_object_items COMMA json_object_item
    """

    #     json_object_item
    if len(p) == 2:
        p[0] = p[1]
        return

    #     json_object_items COMMA json_object_item

    # Intersect to find any duplicate keys.
    intersection = list(set(p[1].keys()) & set(p[3].keys()))

    # Duplicate keys will raise warning, but are not a fatal error.
    for key in intersection:
        message = 'Duplicate key "%s", using last value.' % key
        p.parser.warnings.append(message)

    # Regardless of duplicates, we will now combine the dictionaries.
    p[0] = dict(p[1].items() + p[3].items())


# expression
# ----------
def p_expression(p):
    """
        expression : NULL
                   | TRUE
                   | FALSE
                   | FLOAT
                   | INTEGER
                   | STRING
    """

    #     NULL
    if p[1].upper() == 'NULL':
        # `NULL` is represented as `None`.
        p[0] = None

    #     TRUE
    elif p[1].upper() == 'TRUE':
        p[0] = True

    #     FALSE
    elif p[1].upper() == 'FALSE':
        p[0] = False

    #     STRING
    elif p[1][0] == '"':
        # Prune the double-quotes off the STRING value.
        p[0] = p[1][1:-1]

    #     FLOAT
    elif '.' in p[1]:
        p[0] = float(p[1])

    #     INTEGER
    else:
        p[0] = int(p[1])


# json_object_item
# ----------------
def p_json_object_item(p):
    """
        json_object_item : STRING COLON expression
    """

    # Remove the trailing and proceeding double-quotes around the STRING key.
    key = p[1][1:-1]

    # Create the key-value item.
    p[0] = {key: p[3]}


# error
# -----
def p_error(p):
    # This is really bad error, we cannot recover from this.
    raise RuntimeError("Not valid SQL.")


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


# Objects
# =======

class Statement:
    """
    Represents a SQL statement.
    """

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


class InsertStatement(Statement):
    """
    Represents an `INSERT` statement.
    """
    def __init__(self, table_name, fields):
        """
            :param table_name: str
            :param fields: dict
        """
        self.table_name = table_name
        self.fields = fields

        self.assert_type('table_name', str)
        self.assert_type('fields', dict)

    def __str__(self):
        return "INSERT INTO %s %s" % (self.table_name, json.dumps(self.fields))


class SelectStatement(Statement):
    """
    Represents an `SELECT` statement.
    """
    def __init__(self, table_name):
        """
            :param table_name: str
        """
        self.table_name = table_name

        self.assert_type('table_name', str)

    def __str__(self):
        return "SELECT * FROM %s" % self.table_name
