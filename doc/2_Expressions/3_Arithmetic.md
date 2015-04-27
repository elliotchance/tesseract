Arithmetic
==========


Addition:

    a + b

Subtraction:

    a - b

Multiplication:

    a * b

Division:

    a / b

Modulo (remainder):

    a % b

Power:

    a ^ b

`a` and `b` must be `null` or `number`.

    
Concatenation
-------------

    a || b
    
Will concatenate the string representations of both sides. For example `3 || 5`
is `35`. Special values will be converted as follows:

Value    | String Representation
-------- | ---------------------
`null`   | `""`
`true`   | `"true"`
`false`  | `"false"`

You cannot concatenate arrays or objects on either or both sides.
