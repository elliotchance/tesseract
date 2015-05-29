INSERT
======

``INSERT`` is used to add an object to a table.

Syntax
------

.. code-block:: sql

   INSERT INTO <table_name>
   <json_object>

table_name
  The table name to insert the object into. This table will be created by
  simply adding an object into it if it has never been inserted into.

json_object
  A JSON object.


Examples
--------

.. code-block:: sql

   INSERT INTO people
   { "first_name": "John", "last_name": "Smith" }
