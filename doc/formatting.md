% Formatting

The tesseract manual is written in Markdown and processed with Rippledoc and
Pandoc. This document does not intend to outline how the documentation is
generated. Only to provide a style guidelines and samples that are used through
the rest of the manual.

You may use all the features of Markdown and any features specifically
supported by Pandoc. However, in all cases you must follow these rules wherever
approproate:

 * Keep all documentation to 80 columns unless it cannot be avoided (for
   example, long tables or code snippets).

 * The documentation here is intended to be easily read and maintained. Do no
   use fancy features that make the Markdown less readable simply to make the
   result HTML look more pretty.


Basic
=====

Always H1 for first level headings and always use an underlined heading rather
than hashes:

~~~~~~
Heading 1
=========

Heading 2
---------
~~~~~~

If you have to goto the thrid level then include the hashes on *both* sides of
the heading:

~~~~~~
### Heading 3 ###
~~~~~~

Each heading of any strength should have two blank lines above it (unless it is
the first line of the file.)


SQL Examples
============

SQL examples should be used in fenced blocks and not include the following
semi-colon:

~~~~~~
```sql
SELECT foo FROM bar
```
~~~~~~

```sql
SELECT foo FROM bar
```

If you would like to show the result of the SQL it must be in a separate fenced
block for JSON:

~~~~~~
```json
{"foo": "bar"}
```
~~~~~~

```json
{"foo": "bar"}
```


Syntax Descriptions
===================

When describing SQL syntax use a SQL fenced block:

~~~~~~
```sql
SELECT <some_columns>
FROM <table>
```
~~~~~~

```sql
SELECT <some_columns>
FROM <table>
```

For each of the placeholders use a definition style with a blank line between
each definition:

~~~~~~
some_columns
  : Lots of nice decription here.

table
  : Even more wonderful information!
~~~~~~

some_columns
  : Lots of nice decription here.

table
  : Even more wonderful information!


Notes
=====

Notes are meant to stand out from other text and contain important information.

~~~~~~
> This is important information.
~~~~~~

> This is important information.


Tables
======

There are two types of table syntax that make the table as small as possible
around the text or type to span as much space as possible. Always use the
greater span syntax:

~~~~~~
---------  -------------
full span  syntax
---------  -------------
for        tables
with       multiple rows
---------  -------------
~~~~~~

---------  -------------
full span  syntax
---------  -------------
for        tables
with       multiple rows
---------  -------------
