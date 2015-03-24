SELECT
======

`SELECT` is used to receive data.

Syntax
------

<code>
> SELECT **_columndefinitions_**<br/>
> FROM **_tablename_**<br/>
> [ WHERE **_condition_** ]
</code>

**_columndefinitions_**

> This can be an asterisk (`*`) to represent that the entire object should be
> retrieved without modification or a list of expressions.

**_tablename_**

> The table name to fetch the objects from. If the table does not exist (i.e.
> has no records) then no records will be returned since tables only come into
> existence when they have objects added to them.

**_condition_**

> A filter expression.
