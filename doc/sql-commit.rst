COMMIT
======

Syntax
------

.. code-block:: sql

   COMMIT [ WORK | TRANSACTION ]

WORK
  Optional keyword. It has no effect.

TRANSACTION
  Optional keyword. It has no effect.


Overview
--------

``COMMIT`` commits the current transaction. All changes made by the transaction
become visible to others.

Compatibility
-------------

The SQL standard only specifies the two forms ``COMMIT`` and ``COMMIT WORK``.
