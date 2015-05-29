Aggregate Functions
===================

Aggregate functions calculate a single value based ona set of values (this set
may be zero values).


``AVG()`` -- Average
------------------

```sql
avg(<number>)
```


``COUNT()`` -- Count records
----------------------------

```sql
count(*)
count(<any>)
```

When the argument is `*` it will count all records without needing to provide
any value.


`MAX()` -- Maximum value
========================

```sql
max(<number>)
```


`MIN()` -- Minimum value
========================

```sql
min(<number>)
```


`SUM()` -- Total
================

```sql
sum(<number>)
```
