.. _sql-start-transaction:

START TRANSACTION
=================

Syntax
------

.. code-block:: sql

   START TRANSACTION
   BEGIN [ WORK | TRANSACTION ]


Overview
--------

``START TRANSACTION`` or the alias ``BEGIN`` starts a transaction.

Compatibility
-------------

In the standard, it is not necessary to issue ``START TRANSACTION`` to start a
transaction block: any SQL command implicitly begins a block. Tesseract's
behavior can be seen as implicitly issuing a ``COMMIT`` after each command that
does not follow ``START TRANSACTION`` (or ``BEGIN``), and it is therefore often
called "autocommit".
