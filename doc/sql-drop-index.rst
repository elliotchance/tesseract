% DROP INDEX

`DROP INDEX` deletes an already defined index.

Syntax
======

```sql
DROP INDEX <index_name>
```

index_name
  : The name of the index must already exist. Index names must be globally
    unique - that is different tables cannot have a index with the same name.
