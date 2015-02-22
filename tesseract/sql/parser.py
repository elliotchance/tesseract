import ply.yacc as yacc
from tesseract.sql.objects import *
import tesseract.sql.lexer as lexer

tokens = lexer.tokens

# Parser
# ======

# Set precedence for operators. We do not need these yet.
precedence = ()


# statement
# ---------
def p_statement(p):
    """
        statement : delete_statement
                  | insert_statement
                  | select_statement
    """

    # Which ever statement matches can be passed straight through.
    p.parser.statement = p[1]


# delete_statement
# ----------------
def p_delete_statement(p):
    """
        delete_statement : DELETE FROM
                         | DELETE
    """

    #     DELETE
    if len(p) == 2:
        raise RuntimeError("Expected FROM after DELETE.")

    #     DELETE FROM
    raise RuntimeError("Expected table name after FROM.")


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
    # Build the parser.
    parser = yacc.yacc()
    parser.statement = None
    parser.warnings = []

    # Run the parser.
    parser.parse(data)

    # Return the base AST tree.
    return parser
