Comparison Expressions
======================

[TOC]


Equality
--------

    a = b

For inequality:

    a != b
    a <> b

`a` and `b` must be the same type, and accepted types are:

* `null`
* `number`
* `string`
* `array`
* `object`

In the case of an `array` both arrays must be the same length and contain
exactly the same element in the same order:

    SELECT [1, 2] = [1, 2]

> `true`

    SELECT [1, 2] = [1, "2"]

> `false`

    SELECT [1, 2] = [2, 1]

> `false`

In the case of an `object` both objects must contain the same amount of keys and
each key must exist in both objects with the exact same value.

    SELECT {"foo": 123} = {"foo": 123}

> `true`

    SELECT {"foo": 123} = {"foo": 123, "bar": null}

> `false`

Inequality has all the same rules but in reverse.


Greater or Less Than
--------------------

Greater than:

    a > b

Greater than or equal to:

    a >= b

Less than:

    a < b

Less than or equal to:

    a <= b

`a` and `b` must be the same type, and accepted types are:

* `null`
* `number`
* `string`

When comparing strings it follows the same rules as how Lua compares strings.


Logical
-------

For all logical operations `a` and `b` are only allowed to be `null` or
`boolean`.

Logical AND:

    a AND b

Results:

AND     | `true`  | `false`
------- | ------- | -------
`true`  | `true`  | `false`
`false` | `false` | `false`

Logical OR:

    a OR b

Results:

OR      | `true`  | `false`
------- | ------- | -------
`true`  | `true`  | `true`
`false` | `true`  | `false`
