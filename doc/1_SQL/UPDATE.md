UPDATE
======

`UPDATE` is used to modify data.

Syntax
------

    UPDATE <table_name>
    SET <column_expressions>
    [ WHERE <condition> ]

**_table_name_**

The table that will have its object modified. If the table does not exist (i.e.
has no records) then no records will be updated since tables only come into
existence when they have objects added to them.

**_column_expressions_**

    <column_name1> = <expression1>, ...

A list of columns to be updated by an expression.

    name = "Bob", something_else = 3 + 5 * 2

You may use any value of the record in the expression as well:

    counter = counter + 1, old_value = counter - 1

**_condition_**

A filter expression. If no `WHERE` clause is provided then all objects in the
table will be updated.
