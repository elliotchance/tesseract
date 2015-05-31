Changelog
=========


v1.0.0-alpha3 (Comet)
---------------------

**Major**

#. Support for indexes. At the moment only exact lookups are supported.

**SQL**

#. Added support for ``LIMIT`` and ``OFFSET``.
 
#. Added support for ``EXPLAIN`` on ``SELECT`` queries.
 
#. Added ``CREATE INDEX`` and ``DROP INDEX``.

**New Functions**
 
 * ``COS()``
 * ``SIN()``
 * ``SQRT()``
 * ``TAN()``

**Miscelanious**

#. The query planner now understands some basic impossible ``WHERE`` clauses.


v1.0.0-alpha2 (Binary Star)
---------------------------

**Major**

#. ``GROUP BY`` single column for ``SELECT``.
    [[#10](https://github.com/elliotchance/tesseract/pull/10)]

#. Added aggregate functions ``AVG()``, ``COUNT()``, ``MAX()``, ``MIN()`` and ``SUM()``.
    [[#10](https://github.com/elliotchance/tesseract/pull/10)]
    
**Operators**

#. Added string concatenation (``||``) operator.
    [[#9](https://github.com/elliotchance/tesseract/pull/9)]

#. Added ``ILIKE`` and ``NOT ILIKE`` operators.
    [[#11](https://github.com/elliotchance/tesseract/pull/11)]

**Improvements**
    
#. Reformatted documentation to work with Rippledoc.
    [[#11](https://github.com/elliotchance/tesseract/pull/11)]


v1.0.0-alpha1 (Aurora)
----------------------

This was the initial release and its goal was to get the most basic
implementations of ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE`` working.

**SQL Syntax**

#. ``SELECT`` statement supports single expression from a single table, with
   support for ``ORDER BY`` on a single column. [`#6`_]
 
#. ``DELETE`` statement with ``WHERE`` clause. [`#7`_]
 
#. ``UPDATE`` statement with ``WHERE`` clause. [`#8`_]
 
#. ``INSERT`` statement.
 
#. ``CREATE NOTIFICATION`` and ``DROP NOTIFICATION``. [`#3`_]

.. _#3: https://github.com/elliotchance/tesseract/pull/3
.. _#6: https://github.com/elliotchance/tesseract/pull/6
.. _#7: https://github.com/elliotchance/tesseract/pull/7
.. _#8: https://github.com/elliotchance/tesseract/pull/8

**SQL Operators**
 
#. Added logical operators: ``AND``, ``OR`` and ``NOT``.
 
#. Added containment operators: ``BETWEEN`` and ``NOT BETWEEN``.
 
#. Added mathematical operators: ``+``, ``-``, ``*``, ``/``, ``^`` and ``%``.
 
#. Added comparison operators: ``=``, ``<>``, ``<``, ``>``, ``<=``, ``>=`` and alias ``!=``.
 
#. Added set membership operators ``IN`` and ``NOT IN``.
 
#. Added type checking operators: ``IS`` and ``IS NOT``.
    [[#2](https://github.com/elliotchance/tesseract/pull/2)]
 
#. Added pattern matching operators: ``LIKE`` and ``NOT LIKE`` operators.
    [[#1](https://github.com/elliotchance/tesseract/pull/1)]
    
**Other Improvements**
    
#. Added functions: ``ABS()``, ``BIT_LENGTH()``, ``CEIL()``, ``CHAR_LENGTH()``,
    ``FLOOR()``, ``OCTET_LENGTH()``.
    [[#4](https://github.com/elliotchance/tesseract/pull/4)]
