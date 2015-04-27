Aggregate Functions
===================

Aggregate functions are used to calculate a value across a group of values. See
the documentation for the `GROUP BY` clause in the `SELECT` statement for more
information.

The provided aggregate functions are:

    avg(<expression>)
    count(<expression>)
    max(<expression>)
    min(<expression>)
    sum(<expression>)
    
Where **_expression_** is any expression that is to be evaluated on each record.
A simple example:

    SELECT max(age)
    FROM people
    
May return something like:

    {"col1": 80}

There is a special case: `count(*)` that can be used to count all records in the
group that will always return the number of records. Whereas if you used
`count(foo)` will only count the records where `foo` is not `null`.
