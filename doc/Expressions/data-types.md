% Data Types

There are six distinct data types in tesseract:

* `null`
* `boolean`
* `number`
* `string`
* `array`
* `object`


To allow tesseract to be more confomitive to the SQL standard it uses the same
meaning for the value of `null`. In short, all operations using the value `null`
will also return `null`:

    SELECT null = null

> `null`


An important note is that when an object does not contain a key the value for
that key is assumed to be `null` and all the normal rules apply to it.


Booleans have a value of `true` or `false` and tesseract sees each as a distinct
value, different from any other truthy or falsy value like in most other
scripting languages:

    SELECT 0 = false

> Error: No such operator number = boolean.


Numbers are both integers and floating-point values. Strings that represent
numbers do not mean the same thing:

    SELECT "123" = 123

> Error: No such operator string = number.
