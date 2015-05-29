Aggregate Functions
===================

Aggregate functions calculate a single value based ona set of values (this set
may be zero values).


``AVG()`` -- Average
--------------------

.. code-block:: sql

   avg(<number>)


``COUNT()`` -- Count records
----------------------------

.. code-block:: sql

   count(*)
   count(<any>)

When the argument is `*` it will count all records without needing to provide
any value.


``MAX()`` -- Maximum value
--------------------------

.. code-block:: sql

   max(<number>)


``MIN()`` -- Minimum value
--------------------------

.. code-block:: sql

   min(<number>)


``SUM()`` -- Total
------------------

.. code-block:: sql

   sum(<number>)
