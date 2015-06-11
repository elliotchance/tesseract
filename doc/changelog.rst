.. _changelog:

Changelog
=========

Each release is named after space stuff, with each release starting with a
successive alphabet letter.


v1.0.0-alpha1 (Aurora)
----------------------

This was the initial release and its goal was to get the most basic
implementations of `SELECT`_, `INSERT`_, `UPDATE`_ and `DELETE`_ working.

#. `SELECT`_ statement supports single expression from a single table, with
   support for `ORDER BY`_ on a single column. [`#6`_]

#. `DELETE`_ statement with ``WHERE`` clause. [`#7`_]

#. `UPDATE`_ statement with ``WHERE`` clause. [`#8`_]

#. `INSERT`_ statement.

#. `CREATE NOTIFICATION`_ and `DROP NOTIFICATION`_. [`#3`_]

#. Added `logical operators`_: ``AND``, ``OR`` and ``NOT``.

#. Added `containment operators`_: ``BETWEEN`` and ``NOT BETWEEN``.

#. Added `mathematical operators`_: ``+``, ``-``, ``*``, ``/``, ``^`` and ``%``.

#. Added `comparison operators`_: ``=``, ``<>``, ``<``, ``>``, ``<=``, ``>=``
   and alias ``!=``.

#. Added `set membership operators`_: ``IN`` and ``NOT IN``.

#. Added `type checking operators`_: ``IS`` and ``IS NOT``. [`#2`_]

#. Added `pattern matching operators`_: ``LIKE`` and ``NOT LIKE``. [`#1`_]

#. Added functions: ``ABS()``, ``BIT_LENGTH()``, ``CEIL()``, ``CHAR_LENGTH()``,
   ``FLOOR()``, ``OCTET_LENGTH()``. [`#4`_]

.. _#1: https://github.com/elliotchance/tesseract/pull/1
.. _#2: https://github.com/elliotchance/tesseract/pull/2
.. _#3: https://github.com/elliotchance/tesseract/pull/3
.. _#4: https://github.com/elliotchance/tesseract/pull/4
.. _#6: https://github.com/elliotchance/tesseract/pull/6
.. _#7: https://github.com/elliotchance/tesseract/pull/7
.. _#8: https://github.com/elliotchance/tesseract/pull/8
.. _SELECT: https://tesseractdb.readthedocs.org/en/latest/sql-select.html
.. _INSERT: https://tesseractdb.readthedocs.org/en/latest/sql-insert.html
.. _UPDATE: https://tesseractdb.readthedocs.org/en/latest/sql-update.html
.. _DELETE: https://tesseractdb.readthedocs.org/en/latest/sql-delete.html
.. _ORDER BY: https://tesseractdb.readthedocs.org/en/latest/sql-select.html
.. _CREATE NOTIFICATION: https://tesseractdb.readthedocs.org/en/latest/sql-create-notification.html
.. _DROP NOTIFICATION: https://tesseractdb.readthedocs.org/en/latest/sql-drop-notification.html
.. _logical operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#logical
.. _containment operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#containment
.. _mathematical operators: https://tesseractdb.readthedocs.org/en/latest/math-functions.html
.. _comparison operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#greater-or-less-than
.. _set membership operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#set-membership
.. _type checking operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#checking-types
.. _pattern matching operators: https://tesseractdb.readthedocs.org/en/latest/operators.html#regular-expressions


v1.0.0-alpha2 (Binary Star)
---------------------------

The focus of this release was on `GROUP BY`_ and aggregate functions.

#. `GROUP BY`_ single column for `SELECT`_. [`#10`_]

#. Added aggregate functions `AVG()`_, `COUNT()`_, `MAX()`_, `MIN()`_ and
   `SUM()`_. [`#10`_]

#. Added `string concatenation`_ (``||``) operator. [`#9`_]

#. Added `ILIKE`_ and `NOT ILIKE`_ operators. [`#11`_]

#. Reformatted documentation to work with `Rippledoc`_. [`#11`_]

.. _#9: https://github.com/elliotchance/tesseract/pull/9
.. _#10: https://github.com/elliotchance/tesseract/pull/10
.. _#11: https://github.com/elliotchance/tesseract/pull/11
.. _GROUP BY: https://tesseractdb.readthedocs.org/en/latest/sql-select.html
.. _AVG(): https://tesseractdb.readthedocs.org/en/latest/aggregate-functions.html#avg-average
.. _COUNT(): https://tesseractdb.readthedocs.org/en/latest/aggregate-functions.html#count-count-records
.. _MAX(): https://tesseractdb.readthedocs.org/en/latest/aggregate-functions.html#max-maximum-value
.. _MIN(): https://tesseractdb.readthedocs.org/en/latest/aggregate-functions.html#min-minimum-value
.. _SUM(): https://tesseractdb.readthedocs.org/en/latest/aggregate-functions.html#sum-total
.. _Rippledoc: https://github.com/uvtc/rippledoc
.. _string concatenation: https://tesseractdb.readthedocs.org/en/latest/operators.html#concatenation
.. _ILIKE: https://tesseractdb.readthedocs.org/en/latest/operators.html#regular-expressions
.. _NOT ILIKE: https://tesseractdb.readthedocs.org/en/latest/operators.html#regular-expressions


v1.0.0-alpha3 (Comet)
---------------------

This releases theme was *indexing*. At the moment only exact lookups are
supported.

#. Added support for `LIMIT`_ and `OFFSET`_. [`#12`_]
 
#. Added support for `EXPLAIN`_ on `SELECT`_ queries. [`#14`_]
 
#. Added `CREATE INDEX`_ and `DROP INDEX`_. [`#15`_]

#. Added ``COS()``. [`#13`_]

#. Added ``SIN()``. [`#13`_]

#. Added ``SQRT()``. [`#13`_]

#. Added ``TAN()``. [`#13`_]

#. The query planner now understands some basic impossible ``WHERE`` clauses.

.. _#12: https://github.com/elliotchance/tesseract/pull/12
.. _#13: https://github.com/elliotchance/tesseract/pull/13
.. _#14: https://github.com/elliotchance/tesseract/pull/14
.. _#15: https://github.com/elliotchance/tesseract/pull/15
.. _CREATE INDEX: https://tesseractdb.readthedocs.org/en/latest/sql-create-index.html
.. _DROP INDEX: https://tesseractdb.readthedocs.org/en/latest/sql-drop-index.html
.. _LIMIT: https://tesseractdb.readthedocs.org/en/latest/sql-select.html
.. _OFFSET: https://tesseractdb.readthedocs.org/en/latest/sql-select.html
.. _EXPLAIN: https://tesseractdb.readthedocs.org/en/latest/sql-select.html


v1.0.0-alpha4 (D...)
--------------------

The focus of this release was on supporting *transactions*.

#. Support for `START TRANSACTION`_, `COMMIT`_ and `ROLLBACK`_. [`#16`_]
   [`#17`_]

#. Refactored documentation for `Sphinx`_, hosted on
   `tesseractdb.readthedocs.org`_.

.. _#16: https://github.com/elliotchance/tesseract/pull/16
.. _#17: https://github.com/elliotchance/tesseract/pull/17
.. _tesseractdb.readthedocs.org: http://tesseractdb.readthedocs.org
.. _Sphinx: http://sphinx-doc.org
.. _START TRANSACTION: https://tesseractdb.readthedocs.org/en/latest/sql-start-transaction.html
.. _COMMIT: https://tesseractdb.readthedocs.org/en/latest/sql-commit.html
.. _ROLLBACK: https://tesseractdb.readthedocs.org/en/latest/sql-rollback.html
