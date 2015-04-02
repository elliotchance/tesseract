Testing
=======

[TOC]


Introduction
------------

Tesseract generates tests from YAML files. This makes it very easy to read,
maintain and organise.

These files can be found in the `tests` directory. The most simple file may look
like:

```yml
tests:
  my_test:
    sql: SELECT 1 + 2
    result:
    - {"col1": 3}
```

In the example above we have created one test called `my_test` that will run the
SQL statement and confirm that the server returns one row containing that exact
data.

Parser
------

All tests that contain a `sql` attribute will be run through the parser and the
statement will be rendered. This rendered statement is expected to be the same
as this `sql` value. If you expect a different rendered string then you specify
what the result should be through `as`:

```yml
tests:
  alternate_operator:
    sql: 'SELECT null != 123'
    as: 'SELECT null <> 123'
    result:
    - {"col1": null}
```

Expecting Errors
----------------

Use the `error` to test for an expected error:

```yml
tests:
  incompatible_types:
    sql: SELECT false AND 3.5
    error: No such operator boolean AND number.
```

Errors will be raised by the parser or by executing the SQL statement(s).

Expecting Warnings
------------------

You can assert one or more warnings are raised:

```yml
tests:
  json_object_duplicate_item_raises_warning:
    sql: 'SELECT {"foo": "bar", "foo": "baz"}'
    as: 'SELECT {"foo": "baz"}'
    warning: Duplicate key "foo", using last value.

  multiple_warnings_can_be_raised:
    sql: 'SELECT {"foo": "bar", "foo": "baz", "foo": "bax"}'
    as: 'SELECT {"foo": "bax"}'
    warning:
    - Duplicate key "foo", using last value.
    - Duplicate key "foo", using last value.
```

Data Sets
---------

It is common that you will want to test against an existing data fixture.
Instead of inserting the data you need manually you can use fixtures:

```yml
data:
  table1:
  - {"foo": 125}
  - {"foo": 124}
  - {"foo": 123}

tests:
  where:
    data: table1
    sql: SELECT * FROM table1 WHERE foo = 124
    result:
    - {"foo": 124}
```

Ignoring the Parser
-------------------

Sometimes the SQL rendered from the SQL provided is not predictable, so we have
to disable the parser test:

```
tests:
  json_object_with_two_elements:
    sql: 'SELECT {"foo": "bar", "baz": 123}'
    parse: false
    result:
    - {"col1": {"foo": "bar", "baz": 123}}
```
