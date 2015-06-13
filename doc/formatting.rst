Formatting
==========

The tesseract manual is written in reStructuredText and processed with Sphinx.
This document does not intend to outline how the documentation is generated.
Only to provide a style guidelines and samples that are used through the rest of
the manual.

There are some general rules to follow:

 * Keep all documentation to 80 columns unless it cannot be avoided (for
   example, long tables or code snippets).

 * The documentation here is intended to be easily read and maintained. Do not
   use fancy features that make the reStructuredText less readable simply to
   make the result HTML look more pretty.


Basic
-----

Always H1 for first level headings and always use an underlined heading rather
than hashes::

   Heading 1
   =========

   Heading 2
   ---------

   Heading 3
   ^^^^^^^^^

Each heading of any strength should have two blank lines above it (unless it is
the first line of the file.)


SQL Examples
------------

SQL examples should be used in fenced blocks and not include the following
semi-colon:

.. code-block:: none

   .. code-block:: sql

      SELECT foo FROM bar

.. code-block:: sql

   SELECT foo FROM bar

If you would like to show the result of the SQL it must be in a separate block
for JSON:


.. code-block:: none

   .. code-block:: json

      {"foo": "bar"}

.. code-block:: json

   {"foo": "bar"}


Syntax Descriptions
-------------------

When describing SQL syntax use a SQL block:

.. code-block:: none

   .. code-block:: sql

      SELECT <some_columns>
      FROM <table>

.. code-block:: sql

   SELECT <some_columns>
   FROM <table>

For each of the placeholders use a definition style with a blank line between
each definition:

.. code-block:: none

   some_columns
     Lots of nice description here.

   table
     Even more wonderful information!

some_columns
  Lots of nice description here.

table
  Even more wonderful information!


Notes
-----

Notes are meant to stand out from other text and contain important information.

.. code-block:: none

   .. highlights::

   This is important information.

.. highlights::

   This is important information.


Tables
------

There are two types of table syntax that make the table as small as possible
around the text or type to span as much space as possible. Always use the
greater span syntax:

.. code-block:: none

   .. table::

      =========  =============
      full span  syntax
      =========  =============
      for        tables
      with       multiple rows
      =========  =============

.. table::

   =========  =============
   full span  syntax
   =========  =============
   for        tables
   with       multiple rows
   =========  =============
