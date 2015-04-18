import ply.yacc as yacc
from tesseract.sql.clause.order_by import OrderByClause
from tesseract.sql.expressions import *
import tesseract.sql.lexer as lexer
from tesseract.sql.statements.create_notification import \
    CreateNotificationStatement
from tesseract.sql.statements.delete import DeleteStatement
from tesseract.sql.statements.drop_notification import DropNotificationStatement
from tesseract.sql.statements.insert import InsertStatement
from tesseract.sql.statements.select import SelectStatement

# Parser
# ======

# Load in the tokens from lexer.
from tesseract.sql.statements.update import UpdateStatement

tokens = lexer.tokens

# Set precedence for operators.
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQUAL', 'NOT_EQUAL'),
    ('left', 'GREATER', 'LESS', 'GREATER_EQUAL', 'LESS_EQUAL'),
    ('left', 'LIKE'),
    ('right', 'BETWEEN'),
    ('right', 'IN'),
    ('right', 'IS'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('left', 'CARET'),
)


# statement
# ---------
def p_statement(p):
    """
        statement : delete_statement
                  | insert_statement
                  | select_statement
                  | create_notification_statement
                  | drop_notification_statement
                  | update_statement
    """

    # Which ever statement matches can be passed straight through.
    p.parser.statement = p[1]


# update_set_list
# ---------------
def p_update_set_list(p):
    """
        update_set_list : IDENTIFIER EQUAL expression
                        | update_set_list COMMA IDENTIFIER EQUAL expression
    """

    # We use an array like [key, value] instead of an object because we need to
    # maintain the order in which the assignments happen - and be able to render
    # them back to SQL in the same order.
    
    if len(p) == 4:
        p[0] = [ [ str(p[1]), p[3] ] ]
    else:
        p[1].append([ str(p[3]), p[5] ])
        p[0] = p[1]


# update_statement
# ----------------
def p_update_statement(p):
    """
        update_statement : UPDATE IDENTIFIER SET update_set_list optional_where_clause
    """

    p[0] = UpdateStatement(p[2], p[4], p[5])


# drop_notification_statement
# ---------------------------
def p_drop_notification_statement(p):
    """
        drop_notification_statement : DROP NOTIFICATION IDENTIFIER
    """

    p[0] = DropNotificationStatement(p[3])


# create_notification_statement
# -----------------------------
def p_create_notification_statement(p):
    """
        create_notification_statement : CREATE NOTIFICATION IDENTIFIER ON IDENTIFIER
                                      | CREATE NOTIFICATION IDENTIFIER ON IDENTIFIER WHERE expression
    """

    #     CREATE NOTIFICATION IDENTIFIER ON IDENTIFIER
    if len(p) == 6:
        p[0] = CreateNotificationStatement(p[3], p[5])

    #     CREATE NOTIFICATION IDENTIFIER ON IDENTIFIER WHERE expression
    else:
        p[0] = CreateNotificationStatement(p[3], p[5], p[7])



# delete_statement
# ----------------
def p_delete_statement(p):
    """
        delete_statement : DELETE FROM IDENTIFIER optional_where_clause
                         | DELETE FROM
                         | DELETE
    """

    #     DELETE
    if len(p) == 2:
        raise RuntimeError("Expected FROM after DELETE.")

    #     DELETE FROM
    elif len(p) == 3:
        raise RuntimeError("Expected table name after FROM.")

    #     DELETE FROM IDENTIFIER optional_where_clause
    # A valid `DELETE` statement
    p[0] = DeleteStatement(p[3], p[4])


# empty
# -----
def p_empty(p):
    'empty :'
    pass


# optional_from_clause
# --------------------
def p_optional_from_clause(p):
    """
        optional_from_clause : empty
                             | FROM IDENTIFIER
    """

    #     FROM IDENTIFIER
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


# optional_where_clause
# ---------------------
def p_optional_where_clause(p):
    """
        optional_where_clause : empty
                              | WHERE expression
    """

    #     WHERE expression
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


# optional_order_clause
# ---------------------
def p_optional_order_clause(p):
    """
        optional_order_clause : empty
                              | ORDER BY IDENTIFIER optional_order_direction
    """

    #     ORDER BY IDENTIFIER optional_order_direction
    if len(p) > 3:
        p[0] = OrderByClause(p[3], p[4])
    else:
        p[0] = None


# select_statement
# ----------------
def p_select_statement(p):
    """
        select_statement : SELECT expression optional_from_clause optional_where_clause optional_order_clause
                         | SELECT
    """

    #     SELECT
    if len(p) == 2:
        raise RuntimeError("Expected expression after SELECT.")

    if not p[3]:
        p[3] = SelectStatement.NO_TABLE

    p[0] = SelectStatement(table_name=p[3], columns=p[2], where=p[4], order=p[5])


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


# optional_order_direction
# ------------------------
def p_optional_order_direction(p):
    """
        optional_order_direction : empty
                                 | ASC
                                 | DESC
    """

    if p[1] == 'ASC':
        p[0] = True
    elif p[1] == 'DESC':
        p[0] = False
    else:
        p[0] = None


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
                   | function_call
                   | like_expression
                   | is_expression
                   | in_expression
                   | between_expression
                   | group_expression
                   | value
                   | TIMES
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
        add_requirement(p, 'operator/greater')
        p[0] = GreaterExpression(p[1], p[3])

    #     expression GREATER_EQUAL expression
    elif p[2] == '>=':
        add_requirement(p, 'operator/greater_equal')
        p[0] = GreaterEqualExpression(p[1], p[3])

    #     expression LESS_EQUAL expression
    elif p[2] == '<=':
        add_requirement(p, 'operator/less_equal')
        p[0] = LessEqualExpression(p[1], p[3])

    #     expression LESS expression
    elif p[2] == '<':
        add_requirement(p, 'operator/less')
        p[0] = LessExpression(p[1], p[3])

    #     expression EQUAL expression
    elif p[2] == '=':
        add_requirement(p, 'operator/equal')
        p[0] = EqualExpression(p[1], p[3])

    else:
        #     expression NOT_EQUAL expression
        add_requirement(p, 'operator/not_equal')
        p[0] = NotEqualExpression(p[1], p[3])


# group_expression
# ----------------
def p_group_expression(p):
    """
        group_expression : PARAM_OPEN expression PARAM_CLOSE
    """

    p[0] = GroupExpression(p[2])


# function_call
# -------------
def p_function_call(p):
    """
        function_call : IDENTIFIER PARAM_OPEN expression PARAM_CLOSE
    """

    # Function names are not case sensitive.
    function_name = str(p[1]).lower()

    add_requirement(p, 'function/%s' % function_name)
    p[0] = FunctionCall(function_name, p[3])


# between_expression
# ------------------
def p_between_expression(p):
    """
        between_expression : expression BETWEEN expression AND expression
                           | expression NOT BETWEEN expression AND expression
    """

    if p[2] == 'BETWEEN':
        add_requirement(p, 'operator/between')
        p[0] = BetweenExpression(p[1], Value([p[3], p[5]]), False)
    else:
        add_requirement(p, 'operator/not_between')
        p[0] = BetweenExpression(p[1], Value([p[4], p[6]]), True)


# in_expression
# -------------
def p_in_expression(p):
    """
        in_expression : expression IN PARAM_OPEN expression_list PARAM_CLOSE
                      | expression NOT IN PARAM_OPEN expression_list PARAM_CLOSE
    """

    # Notice that the 'operator/equal' dependency must come before 'operator/in'
    add_requirement(p, 'operator/equal')

    if p[2] == 'IN':
        add_requirement(p, 'operator/in')
        p[0] = InExpression(p[1], Value(p[4]), False)
    else:
        add_requirement(p, 'operator/not_in')
        p[0] = InExpression(p[1], Value(p[5]), True)


# is_expression
# -------------
def p_is_expression(p):
    """
        is_expression : expression IS IDENTIFIER
                      | expression IS NOT IDENTIFIER
    """

    if len(p) == 4:
        add_requirement(p, 'operator/is')
        p[0] = IsExpression(p[1], Value(str(p[3]).lower()), False)
    else:
        add_requirement(p, 'operator/is_not')
        p[0] = IsExpression(p[1], Value(str(p[4]).lower()), True)


# like_expression
# ---------------
def p_like_expression(p):
    """
        like_expression : expression LIKE expression
                        | expression NOT LIKE expression
    """

    #     expression LIKE expression
    if p[2] == 'LIKE':
        add_requirement(p, 'operator/like')
        p[0] = LikeExpression(p[1], p[3], False)

    #     expression NOT LIKE expression
    else:
        add_requirement(p, 'operator/not_like')
        p[0] = LikeExpression(p[1], p[4], True)


# logic_expression
# ----------------
def p_logic_expression(p):
    """
        logic_expression : expression AND expression
                         | expression OR expression
                         | NOT expression
    """

    #     NOT expression
    if p[1] == 'NOT':
        add_requirement(p, 'operator/not')
        p[0] = NotExpression(p[2])

    #     expression AND expression
    elif p[2] == 'AND':
        add_requirement(p, 'operator/and')
        p[0] = AndExpression(p[1], p[3])

    #     expression OR expression
    else:
        add_requirement(p, 'operator/or')
        p[0] = OrExpression(p[1], p[3])


# arithmetic_expression
# ---------------------
def p_arithmetic_expression(p):
    """
        arithmetic_expression : expression PLUS expression
                              | expression MINUS expression
                              | expression TIMES expression
                              | expression DIVIDE expression
                              | expression CARET expression
                              | expression MODULO expression
                              | expression CONCAT expression
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

    #     expression CARET expression
    elif p[2].upper() == '^':
        add_requirement(p, 'operator/power')
        p[0] = PowerExpression(p[1], p[3])

    #     expression MODULO expression
    elif p[2].upper() == '%':
        add_requirement(p, 'operator/modulo')
        p[0] = ModuloExpression(p[1], p[3])

    #     expression CONCAT expression
    elif p[2].upper() == '||':
        add_requirement(p, 'operator/concat')
        p[0] = ConcatExpression(p[1], p[3])

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
    raise RuntimeError("Could not parse SQL. Error at or near: " + str(p.value))


def add_requirement(p, function_name):
    # Check if it already exists.
    if function_name not in p.parser.lua_requirements:
        # Add new unique operator.
        p.parser.lua_requirements.append(function_name)


def parse(data):
    # Build the parser.
    parser = yacc.yacc()
    parser.statement = None
    parser.warnings = []

    # It might make sense to use a set() for unique operators but we need to
    # retain the order in which they are required.
    parser.lua_requirements = []

    # Run the parser.
    parser.parse(data)

    # Return the base AST tree.
    return parser
