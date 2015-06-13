SELECT
======

``SELECT`` is used to receive data.

Syntax
------

.. code-block:: sql

   [ EXPLAIN ]
   SELECT <column_definitions>
   [ FROM <table_name> ]
   [ WHERE <condition> ]
   [ GROUP BY <group_field> ]
   [ ORDER BY <order_field> ]
   [ LIMIT <limit> ]

EXPLAIN
  If the ``EXPLAIN`` keyword is present the SQL query is not actually run - but
  rather the query plan (the internal steps required to carry out the task) are
  returned. This is very useful for debugging slow queries and otherwise
  examining what tesseract is doing with a particular query.

column_definitions
  This can be an asterisk (``*``) to represent that the entire object should be
  retrieved without modification or a list of expressions.

  Each column definition can have an attached alias which is case sensitive:

  .. code-block:: sql

     SELECT 3 + 4 AS total

table_name
  The table name to fetch the objects from. If the table does not exist (i.e.
  has no records) then no records will be returned since tables only come into
  existence when they have objects added to them.

  You may omit the table just to parse expressions that do no need a table like:

  .. code-block:: sql

     SELECT 3 + 4

condition
  A filter expression.

group_field
  Rows will be collapsed into groups of distinct values of this field.

order_field
  This can be any field you wish to sort by. If field does not exist in a
  given record it will be sorted as if the value were ``null``.

  There are two modifiers for a column; ``ASC`` and ``DESC`` which represent
  **asc**\ ending and **desc**\ ending respectively. If no sort order is
  specified then ``ASC`` is assumed.

  When data is sorted it is separated into four types:

    * Booleans. Explicit ``true`` and ``false``.
    * Numbers. Integers and floating point, not including strings that look
      like numbers like ``"123"``.
    * Strings.
    * Nulls.

  Data will sorted by type, then value in the same order as above. That is to
  say:
    
    * Any number is considered greater than a boolean.
    * Any string is considered greater than a number.
    * ``null`` is considered to be greater than any non-``null`` value.

limit
  Limit the amount of records to be returned. This is performed after all
  operations on the sets are finished (such as ordering and grouping).

  If you specify a ``LIMIT`` higher than the total number of records it will be
  the same as not specifying the limit at all (all records). Alternatively you
  can use ``LIMIT ALL`` to return all records.

  You may also skip rows before the limit with ``OFFSET``:
    
  .. code-block:: sql

     SELECT * FROM bla LIMIT 20 OFFSET 10
    
  This will skip the first 10 rows and return a maximum of 20 rows - the limit
  is exclusive of the offset.

  ``LIMIT`` is optional like ``OFFSET``:
    
  .. code-block:: sql

    SELECT * FROM bla OFFSET 10
    
  If the offset is larger than the available rows then no rows will be returned.
    
  It is important to note that all the rows up to the ``LIMIT`` + the ``OFFSET``
  must be calculated internally so using a large ``OFFSET`` can be expensive.
  In some cases all records of the entire set must be calculated before the
  limit can be applied - such as when there is an ``ORDER BY`` or ``GROUP BY``
  clauses.
