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

There are two modifiers for a column; `ASC` and `DESC`. If no sort order is
specified then `ASC` is assumed.

Data will be sorted numerically if and only if all the values in the sort set
are numbers with the exclusion of `null`. If a set contains only numbers and one
or more `null` values the `null` values will appear at the end.
