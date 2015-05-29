Mathematical Functions
======================

To comply with the SQL standard in all cases when a ``null`` is passed as an
argument to any function below the result of the expression will be ``null``.
Values that are missing are treated as ``null`` values.


``ABS()`` -- Absolute value
---------------------------

Return the absolute value (positive value) of a number.

    abs(<number>)


``CEIL()`` -- Round up
----------------------

Round up to the next whole number.

    ceil(<number>)


``COS()`` -- Cosine
-------------------

Calculates the cosine of an angle. 

    cos(<number>)


``FLOOR()`` -- Round down
-------------------------

Remove the fractional part of a number. This is often refered to as truncating a
number.

    floor(<number>)


``SIN()`` -- Sine
-----------------

Calculates the sine of an angle. 

    sin(<number>)


``SQRT()`` -- Square root
-------------------------

Calculates the square root of a number. 

    sqrt(<number>)

If the number is negative an error will be thrown:

    Cannot calculate square root with negative number -17


``TAN()`` -- Tangent
--------------------

Calculates the tangent of an angle. 

    tan(<number>)
