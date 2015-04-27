% `COUNT()` -- Count records

    count(<expression>)

expression
  : Any expression that is to be evaluated on each record.

There is a special syntax:

    SELECT count(*)
    FROM foo

This will count all records without needing to provide an expression.
