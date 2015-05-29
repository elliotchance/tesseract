DELETE
======

``DELETE`` is used to remove data.

Syntax
------

.. code-block:: sql

   DELETE FROM <table_name>
   [ WHERE <where_clause> ]

table_name
  The table name to remove the objects from. If the table does not exist then
  the statement will have no effect.

where_clause
  An expression that determines which records should be removed. If the
  ``WHERE`` clause is omitted all records will be deleted.
