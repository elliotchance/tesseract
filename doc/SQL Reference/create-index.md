% CREATE INDEX

`CREATE INDEX` creates a mixed type index on a single column of a table.

Index are used to vastly improve performance when fetching data. By creating
a separate mapping of values in a record that can be used to retrive records
without needing to physically search them.

Syntax
======

```sql
CREATE INDEX <index_name> ON <table_name> (<field>)
```

index_name
  : The name of the index not exist. Index names must be globally unique - that
    is different tables cannot have a index with the same name.
    
table_name
  : The table to create the index on. Every time a record is added, modified or
    deleted it will require all index entries for that row to be updated.
    
field
  : The field to index.


Overview
========

> For those already comfortable with SQL and indexes you need not read must more
> beyond this point. Indexes are intended to work exactly the same way in
> tesseract.

Each index will require space proportional to the amount of data that is in the
original table and how big each entry is to store. As well as the space
consideration every time a record is modified it will have to update all the
indexes for that table with respect to the new or modified record. This is why
it is not wise to create lots of indexes unless you have a specific need to
filter on that attribute.

Lets take a real world example, lets say we have a simple address book that
stores entries like:

```json
{
    "first_name": "Bob",
    "last_name": "Smith",
    "phone": "1234 5678",
}
```

Finding all Bob's is simple:

```sql
SELECT * FROM contacts WHERE first_name = 'Bob'
```

This is fine for a small address book because computer can search very quickly.
But there is a point in which this starts to make less sense and require more
and more resources for the same operation - what if there were thousands or
even million of contacts?

Using the example above we can run an explain to see how tesseract is deciding
to carry out the SQL:

```sql
EXPLAIN SELECT * FROM contacts WHERE first_name = 'Bob'
```

```json
[
    {"description": "Full scan of table 'contacts'"}
    {"description": "Filter: first_name = \"Bob\""}
]
```

It is choosing to do it this wway becuase it has no other choice. But we can
introduce and index on the `first_name`:

```sql
CREATE INDEX contacts_first_name ON contacts (first_name)
```

> Since indexes names must be globally unique it is a good idea (and often
> common practice) to put the table name and column name as the index name for
> both clarity and avoiding naming collisions.

By creating the index it will store all the `first_name`s in a separate place,
in a special order/structure and will automaitcally maintain this index with
every modification.

Now we can run the same `EXPLAIN`:

```sql
EXPLAIN SELECT * FROM contacts WHERE first_name = 'Bob'
```

```json
[
    {"description": "Index lookup using contacts_first_name for value \"Bob\""}
]
```

It does not matter if we have 10 contact records or 10 million the lookup time
will be almost the same (provided the number of Bob's that exists doesn't scale
up with the number of records) - at the cost of slightly more RAM.
