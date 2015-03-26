Testing
=======

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
