% Testing


Basic Test (`sql`)
------------------

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

### Result (`result`)

Specify the expected output of the last `sql` statement. The data returned from
the server must be exacly the same (including order) as the `result` items.

### Result in Any Order (`result-unordered`)

If the order in which the records isn't imporant or is unpredictable you can use
`result-unordered` instead of `result`.

```yml
tests:
  two_columns:
    data: table1
    sql: "SELECT foo, foo * 2 FROM table1"
    result-unordered:
    - {"foo": 123, "col2": 246}
    - {"foo": 124, "col2": 248}
    - {"foo": 125, "col2": 250}
```

### Parser (`as`)

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

### Ignoring the Parser (`parse`)

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

### Commenting (`comment`)

Test can have an optional comment, this is preferred over using YAML inline
comments so that comments can be injected is creating reports in the future.

```yml
tests:
  my_test:
    comment: Test everything!
    sql: 'SELECT 123'
```

### Repeating Tests (`repeat`)

If a test lacks some predictability or you need to test the outcome multiple
times for another reason you can use the `repeat`. This will still generate one
test but it will loop through the `repeat` many times.

```yml
tests:
  my_test:
    sql: 'SELECT 123'
    repeat: 20
    result:
    - {"col1": 123}
```

Failures
--------

### Expecting Errors (`error`)

Use the `error` to test for an expected error:

```yml
tests:
  incompatible_types:
    sql: SELECT false AND 3.5
    error: No such operator boolean AND number.
```

Errors will be raised by the parser or by executing the SQL statement(s).

### Expecting Warnings (`warning`)

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

Data Sets (`data`)
------------------

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

### Randomizing Data (`data-randomized`)

For some tests you may want to randomize the order in which the records are
loaded in. It is often used in conjunction with `repeat`.

```yml
data:
  table1:
  - {"foo": 125}
  - {"foo": 124}
  - {"foo": 123}
```


Verifying Notifications
-----------------------

When under test all notifications throughout the entire test case will be
recorded. They can be asserted after all the SQL is executed. To test for a
single notification:

```yml
tests:
  notification_will_be_fired_for_insert:
    sql:
    - CREATE NOTIFICATION foo ON some_table
    - 'INSERT INTO some_table {"a": "b"}'
    notification:
      to: foo
      with: {"a": "b"}
```

If you need to assert more than one notification:

```yml
tests:
  multiple_notifications_can_be_fired_from_a_single_select:
    sql:
    - CREATE NOTIFICATION foo1 ON some_table WHERE a = "b"
    - CREATE NOTIFICATION foo2 ON some_table WHERE a = "b"
    - 'INSERT INTO some_table {"a": "b"}'
    notification:
      -
        to: foo1
        with: {"a": "b"}
      -
        to: foo2
        with: {"a": "b"}
```

Or validate that no notifications have been fired:

```yml
tests:
  notification_will_respect_where_clause:
    sql:
    - CREATE NOTIFICATION foo ON some_table WHERE a = "c"
    - 'INSERT INTO some_table {"a": "b"}'
    notification: []
```
