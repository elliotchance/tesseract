import ply.yacc as yacc
from tesseract.sql.statements import *
from tesseract.sql.expressions import *
import tesseract.sql.lexer as lexer

# Parser
# ======

# Load in the tokens from lexer.
tokens = lexer.tokens

# Set precedence for operators. We do not need these yet.
precedence = (
    ('left', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE'),
    ('left', 'AND', 'OR'),
    ('left', 'EQUAL', 'NOT_EQUAL'),
    ('left', 'GREATER', 'LESS', 'GREATER_EQUAL', 'LESS_EQUAL'),
)


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
        delete_statement : DELETE FROM IDENTIFIER
                         | DELETE FROM
                         | DELETE
    """

    #     DELETE
    if len(p) == 2:
        raise RuntimeError("Expected FROM after DELETE.")

    #     DELETE FROM
    elif len(p) == 3:
        raise RuntimeError("Expected table name after FROM.")

    #     DELETE FROM IDENTIFIER
    # A valid `DELETE` statement
    p[0] = DeleteStatement(p[3])


# select_statement
# ----------------
def p_select_statement(p):
    """
        select_statement : SELECT TIMES FROM IDENTIFIER WHERE expression
                         | SELECT TIMES FROM IDENTIFIER
                         | SELECT TIMES FROM
                         | SELECT expression
                         | SELECT expression FROM IDENTIFIER
                         | SELECT TIMES
                         | SELECT
    """

    #     SELECT
    if len(p) == 2:
        raise RuntimeError("Expected expression after SELECT.")

    #     SELECT TIMES
    if len(p) == 3 and p[2] == '*':
        raise RuntimeError("Missing FROM clause.")

    #     SELECT expression
    if len(p) == 3:
        p[0] = SelectStatement(SelectStatement.NO_TABLE, p[2])
        return

    #     SELECT TIMES FROM
    if len(p) == 4:
        raise RuntimeError("Expected table name after FROM.")

    # Only valid `SELECT`s beyond this point.

    #     SELECT expression FROM IDENTIFIER
    if len(p) == 5:
        p[0] = SelectStatement(p[4], p[2])
        return

    #     SELECT TIMES FROM IDENTIFIER WHERE expression
    if len(p) == 7:
        p[0] = SelectStatement(p[4], '*', p[6])
        return

    #     SELECT TIMES FROM IDENTIFIER
    p[0] = SelectStatement(p[4], '*')


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
        raise RuntimeError("Expected JSON object after table name.")

    #     INSERT INTO
    elif len(p) == 3:
        raise RuntimeError("Expected table name after INTO.")

    #     INSERT
    elif len(p) == 2:
        raise RuntimeError("Expected table name after INSERT.")

    #     INSERT INTO IDENTIFIER json_object
    # We have a working `INSERT` statement.
    p[0] = InsertStatement(p[3], p[4].value)


# json_array
# ----------
def p_json_array(p):
    """
        json_array : SQUARE_OPEN SQUARE_CLOSE
                   | SQUARE_OPEN expression_list SQUARE_CLOSE
    """

    #     SQUARE_OPEN SQUARE_CLOSE
    if len(p) == 3:
        p[0] = Value([])
        return

    #     SQUARE_OPEN expression_list SQUARE_CLOSE
    p[0] = Value(p[2])


# expression_list
# ---------------
def p_expression_list(p):
    """
        expression_list : expression
                        | expression_list COMMA expression
    """

    #     expression
    if len(p) == 2:
        p[0] = [ p[1] ]
        return

    #     expression_list COMMA expression

    # Append the expression to the list.
    p[0] = p[1] + [ p[3] ]


# json_object
# -----------
def p_json_object(p):
    """
        json_object : CURLY_OPEN CURLY_CLOSE
                    | CURLY_OPEN json_object_items CURLY_CLOSE
    """

    #     CURLY_OPEN CURLY_CLOSE
    if len(p) == 3:
        p[0] = Value({})
        return

    #     CURLY_OPEN json_object_items CURLY_CLOSE
    p[0] = Value(p[2])


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
    p[1].update(p[3])
    p[0] = p[1]


# string
# ------
def p_string(p):
    """
        string : STRING_SINGLE
               | STRING_DOUBLE
    """

    p[0] = p[1]



# value
# -----
def p_value(p):
    """
        value : json_object
              | json_array
              | string
              | NUMBER
              | MINUS NUMBER
              | PLUS NUMBER
              | IDENTIFIER
    """

    #     MINUS NUMBER
    if p[1] == '-':
        p[0] = Value(-p[2].value)

    #     PLUS NUMBER
    elif p[1] == '+':
        p[0] = p[2]

    # All other conditions are single entity and can be passed through directly.
    else:
        p[0] = p[1]



# expression
# ----------
def p_expression(p):
    """
        expression : arithmetic_expression
                   | comparison_expression
                   | logic_expression
                   | value
    """

    p[0] = p[1]


# expression
# ----------
def p_comparison_expression(p):
    """
        comparison_expression : expression EQUAL expression
                              | expression NOT_EQUAL expression
                              | expression GREATER expression
                              | expression GREATER_EQUAL expression
                              | expression LESS expression
                              | expression LESS_EQUAL expression
    """

    #     expression GREATER expression
    if p[2] == '>':
        p[0] = GreaterExpression(p[1], p[3])

    #     expression GREATER_EQUAL expression
    elif p[2] == '>=':
        p[0] = GreaterEqualExpression(p[1], p[3])

    #     expression LESS_EQUAL expression
    elif p[2] == '<=':
        p[0] = LessEqualExpression(p[1], p[3])

    #     expression LESS expression
    elif p[2] == '<':
        p[0] = LessExpression(p[1], p[3])

    #     expression EQUAL expression
    elif p[2] == '=':
        add_requirement(p, 'operator/equal')
        p[0] = EqualExpression(p[1], p[3])

    else:
        #     expression NOT_EQUAL expression
        p[0] = NotEqualExpression(p[1], p[3])


# logic_expression
# ----------------
def p_logic_expression(p):
    """
        logic_expression : expression AND expression
                         | expression OR expression
    """

    #     expression AND expression
    if p[2] == 'AND':
        p[0] = AndExpression(p[1], p[3])

    #     expression OR expression
    else:
        p[0] = OrExpression(p[1], p[3])


# arithmetic_expression
# ---------------------
def p_arithmetic_expression(p):
    """
        arithmetic_expression : expression PLUS expression
                              | expression MINUS expression
                              | expression TIMES expression
                              | expression DIVIDE expression
    """

    #     expression PLUS expression
    if p[2].upper() == '+':
        add_requirement(p, 'operator/plus')
        p[0] = AddExpression(p[1], p[3])

    #     expression TIMES expression
    elif p[2].upper() == '*':
        add_requirement(p, 'operator/times')
        p[0] = MultiplyExpression(p[1], p[3])

    #     expression DIVIDE expression
    elif p[2].upper() == '/':
        add_requirement(p, 'operator/divide')
        p[0] = DivideExpression(p[1], p[3])

    #     expression MINUS expression
    else:
        add_requirement(p, 'operator/minus')
        p[0] = SubtractExpression(p[1], p[3])


# json_object_item
# ----------------
def p_json_object_item(p):
    """
        json_object_item : string COLON expression
    """

    key = p[1].value

    # Create the key-value item.
    p[0] = {key: p[3]}


# error
# -----
def p_error(p):
    # This is really bad error, we cannot recover from this.
    raise RuntimeError("Not valid SQL.")


def add_requirement(p, function_name):
    p.parser.lua_requirements.add(function_name)


def parse(data):
    # Build the parser.
    parser = yacc.yacc()
    parser.statement = None
    parser.warnings = []
    parser.lua_requirements = set()

    # Run the parser.
    parser.parse(data)

    # Return the base AST tree.
    return parser
