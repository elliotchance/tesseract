% SELECT

`SELECT` is used to receive data.

Syntax
======

    SELECT <column_definitions>
    [ FROM <table_name> ]
    [ WHERE <condition> ]
    [ GROUP BY <group_field> ]
    [ ORDER BY <order_field> ]


column_definitions
  : This can be an asterisk (`*`) to represent that the entire object should be
    retrieved without modification or a list of expressions.

table_name
  : The table name to fetch the objects from. If the table does not exist (i.e.
    has no records) then no records will be returned since tables only come into
    existence when they have objects added to them.

    You may omit the table just to parse expressions that do no need a table
    like:

    ```sql
    SELECT 3 + 4
    ```

condition
  : A filter expression.

group_field
  : Rows will be collapsed into groups of distinct values of this field.

order_field
  : This can be any field you wish to sort by. If field does not exist in a
    given record it will be sorted as if the value were `null`.

    There are two modifiers for a column; `ASC` and `DESC` which represent
    **asc**ending and **desc**ending respectively. If no sort order is specified
    then `ASC` is assumed.

    When data is sorted it is separated into four types:

     * Booleans. Explicit `true` and `false`.
     * Numbers. Integers and floating point, not including strings that look
       like numbers like `"123"`.
     * Strings.
     * Nulls.
     
    Data will sorted by type, then value in the same order as above. That is to
    say:
    
     * Any number is considered greater than a boolean.
     * Any string is considered greater than a number.
     * `null` is considered to be greater than any non-`null` value.
