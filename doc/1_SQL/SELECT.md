SELECT
======

`SELECT` is used to receive data.

Syntax
------

    SELECT <column_definitions>
    FROM <table_name>
    WHERE <condition>
    ORDER BY <order_field>

**_column_definitions_**

This can be an asterisk (`*`) to represent that the entire object should be
retrieved without modification or a list of expressions.

**_table_name_**

The table name to fetch the objects from. If the table does not exist (i.e. has
no records) then no records will be returned since tables only come into
existence when they have objects added to them.

**_condition_**

A filter expression.

**_order_field_**

This can be any field you wish to sort by. If field does not exist in a given
record it will be sorted as if the value were `null`.

There are two modifiers for a column; `ASC` and `DESC` which represent
**asc**ending and **desc**ending respectively. If no sort order is specified
then `ASC` is assumed.

When data is sorted it is separated into four types:

 * Booleans. Explicit `true` and `false`.
 * Numbers. Integers and floating point, not including strings that look like
   numbers like `"123"`.
 * Strings.
 * Nulls.
 
Data will sorted by type, then value in the same order as above. That is to say:

 * Any number is considered greater than a boolean.
 * Any string is considered greater than a number.
 * `null` is considered to be greater than any non-`null` value.
