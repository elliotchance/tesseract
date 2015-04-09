CREATE NOTIFICATION
===================

`CREATE NOTIFICATION` tells the tesseract server to publish changes to the Redis
pub/sub model.

Syntax
------

    CREATE NOTIFICATION <notification_name>
    ON <table_name>
    [ WHERE <where_clause> ]

**_notification_name_**

The name of the notification must be unique and non-existent. It follows the
same rules as naming an entity like a table.

**_table_name_**

The table to watch for changes.

**_where_clause_**

Any expression which will cause the notification to fire only if it evaluates to
true:

```sql
CREATE NOTIFICATION bobs
ON people
WHERE first_name = 'Bob'
```

Notes
-----

Multiple notifications can be fired for a single insert but is limited to one
notification per `NOTIFICATION` defined.
