SELECT
======

`SELECT` is used to receive data.

Syntax
------

    SELECT <column_definitions>
    FROM <table_name>
    WHERE <condition>

**_column_definitions_**

This can be an asterisk (`*`) to represent that the entire object should be
retrieved without modification or a list of expressions.

**_table_name_**

The table name to fetch the objects from. If the table does not exist (i.e. has
no records) then no records will be returned since tables only come into
existence when they have objects added to them.

**_condition_**

A filter expression.
