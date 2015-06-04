ROLLBACK
========

Syntax
------

.. code-block:: sql

   ROLLBACK [ WORK | TRANSACTION ]

WORK
  Optional keyword. It has no effect.

TRANSACTION
  Optional keyword. It has no effect.


Overview
--------

``ROLLBACK`` rolls back the current transaction and causes all the updates made
by the transaction to be discarded.

Use ``COMMIT`` to successfully terminate a transaction.

Issuing ``ROLLBACK`` when not inside a transaction does no harm, but it will
provoke a warning message.

Compatibility
-------------

The SQL standard only specifies the two forms ``ROLLBACK`` and
``ROLLBACK WORK``.

See Also
--------

 * :ref:`transactions`
