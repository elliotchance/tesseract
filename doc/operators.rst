Operators
=========


Arithmetic
----------


Addition::

    a + b

Subtraction::

    a - b

Multiplication::

    a * b

Division::

    a / b

Modulo (remainder)::

    a % b

Power::

    a ^ b

``a`` and ``b`` must be ``null`` or ``number``.


Equality
--------

Equality::

    a = b

For inequality::

    a != b
    a <> b

``a`` and ``b`` must be the same type, and accepted types are:

* ``null``
* ``number``
* ``string``
* ``array``
* ``object``

In the case of an ``array`` both arrays must be the same length and contain
exactly the same element in the same order:

.. code-block:: sql

   SELECT [1, 2] = [1, 2]

.. code-block:: json

   true


.. code-block:: sql

   SELECT [1, 2] = [1, "2"]

.. code-block:: json

   false


.. code-block:: sql

   SELECT [1, 2] = [2, 1]

.. code-block:: json

   false

In the case of an ``object`` both objects must contain the same amount of keys
and each key must exist in both objects with the exact same value.


.. code-block:: sql

   SELECT {"foo": 123} = {"foo": 123}

.. code-block:: json

   true


.. code-block:: sql

   SELECT {"foo": 123} = {"foo": 123, "bar": null}

.. code-block:: json

   false


Inequality has all the same rules but in reverse.


Greater or Less Than
--------------------

Greater than::

    a > b

Greater than or equal to::

    a >= b

Less than::

    a < b

Less than or equal to::

    a <= b

``a`` and ``b`` must be the same type, and accepted types are:

* ``null``
* ``number``
* ``string``

When comparing strings it follows the same rules as how Lua compares strings.

    
Concatenation
-------------

Concatenation::

    a || b
    
Will concatenate the string representations of both sides. For example
``3 || 5`` is ``35``. Special values will be converted as follows:

.. table::

   =========  =====================
   Value      String Representation
   =========  =====================
   ``null``   ``""``
   ``true``   ``"true"``
   ``false``  ``"false"``
   =========  =====================

You cannot concatenate arrays or objects on either or both sides.


Logical
-------

For all logical operations ``a`` and ``b`` are only allowed to be ``null`` or
``boolean``.

Logical AND::

    a AND b

Results:

.. table::

   =========  =========  =========
   AND        ``true``   ``false``
   =========  =========  =========
   ``true``   ``true``   ``false``
   ``false``  ``false``  ``false``
   =========  =========  =========

Logical OR::

    a OR b

Results:

.. table::

   =========  =========  =========
   OR         ``true``   ``false``
   =========  =========  =========
   ``true``   ``true``   ``true``
   ``false``  ``true``   ``false``
   =========  =========  =========


Regular Expressions
-------------------

Regular Expressions::

    value LIKE regex
    value NOT LIKE regex

``value`` must be a string, but can be of any length.

``regex`` uses the SQL rules for ``LIKE`` expressions.

.. table::

   =========  ==============================
   Character  Description
   =========  ==============================
   ``.``      Match any single character.
   ``%``      Match zero or more characters.
   =========  ==============================


Examples
^^^^^^^^

Test if a string starts with another string:

.. code-block:: sql

   SELECT "Bob Smith" LIKE "Bob %"

Test if a string ends with another string:

.. code-block:: sql

   SELECT "Bob Smith" LIKE "% Smith"


Checking Types
--------------

The following can be used to test the types of a value::

    value IS null
    value IS true
    value IS false
    value IS boolean
    value IS number
    value IS string
    value IS array
    value IS object

Each of the combinations can be used with ``NOT`` like::

    value IS NOT boolean
    
The case of the type (``boolean``) is not important and there is no specific
convention on case.


Set Membership
--------------

To test the existence of a value in a set::

    a IN (b1, b2, ...)
    a NOT IN (b1, b2, ...)

Will return ``true`` if ``a`` exists in one of the ``b`` values. There must be
at least one ``b`` value. Comparison of each element follows the same rules as
the ``=`` operator.

If ``a`` is ``null`` or any of the ``b`` values are ``null`` then the result is
``null``. This is to conform is the SQL standard in dealing with ``null``
values.


Containment
-----------

To test if a value sits between two other values (inclusive)::

    a BETWEEN b AND c
    a NOT BETWEEN b AND c

Is exactly equivalent to::

    a >= b AND a <= c
    a < b OR a > c

If at least one of ``a``, ``b`` or ``c`` is ``null`` then the result will always
be ``null``.


Operator Precedence
-------------------

.. table::

   ==================  =============  ======================================
   Operator/Element    Associativity  Description
   ==================  =============  ======================================
   ``-``               right          unary minus
   ``^``               left           exponentiation
   ``*`` ``/`` ``%``   left           multiplication, division, modulo
   ``+`` ``-``         left           addition, subtraction
   ``IS``                             test for ``true``, ``false``, ``null``
   ``IN``                             set membership
   ``BETWEEN``                        containment
   ``LIKE`` ``ILIKE``                 string pattern  matching
   ``<`` ``>``                        less than, greater than
   ``=``               right          equality, assignment
   ``NOT``             right          logical negation
   ``AND``             left           logical conjunction
   ``OR``              left           logical disjunction
   ==================  =============  ======================================
