**tesseract** is a database that combines the power of SQL with the flexibility
of JSON storage. A hybrid, taking the best from seamingly incompatible
technologies.

It is backed by Redis as the storage engine and the processor of the the hard
work meaning it can be very fast and written in pure python.

Enough talk, show me!

```sql
tesseract> insert into people {
         >   "first_name": "Bob",
         >   "last_name": "Smith",
         >   "children": [ "Sally", "Bob Jnr." ]
         > };
         
tesseract> insert into people {
         >   "first_name": "John",
         >   "last_name": "Williams",
         >   "children": [ "Bill" ]
         > };
         
tesseract> select * from people;
[
  {"first_name": "Bob", "last_name": "Smith", "children": ["Sally", "Bob Jnr."]}
  {"first_name": "John", "last_name": "Williams", "children": ["Bill"]}
]
```

Friendly `WHERE` clause:

```sql
tesseract> select * from people where first_name like "B%";
[
  {"first_name": "Bob", "last_name": "Smith", "children": ["Sally", "Bob Jnr."]}
]
```

Some basic manipulation...

```sql
tesseract> select first_name, len(children) as children, children[0] as first
         > from people;
[
  {"first_name": "Bob", "children": 2, "first": "Sally"}
  {"first_name": "John", "children": 1, "first": "Bill"}
]
```

Aggregation:

```sql
tesseract> select sort(sum(children)) from people;
[
  {"col1": ["Bill", "Bob Jnr.", "Sally"]}
]
```

Unless otherwise specified you will always get an array of objects. However, in
some cases you will want to customise the output to be an object with a
key/value pair:

```sql
tesseract> select first_name + " " + last_name as _key,
         >     {"has": count(children)} as _value
         > from people;
{
  "Bob Smith": {"has": 2},
  "John Williams": {"has": 1},
}
```

Joining:

```sql
tesseract> insert into customer {"id": 123, "name": "Bob the Builder"};
tesseract> insert into order {"id": 456, "customer_id": 123, "items": ["Hammer", "Nails"]};
tesseract> select *
         > from customer
         > join order on customer.id = customer_id;
{
    {"id": 456, "name": "Bob the Builder", "customer_id": 123, "items": ["Hammer", "Nails"]}
}

tesseract> select order.*, customer
         > from customer
         > join order on customer.id = customer_id;
{
    {"id": 456, "customer_id": 123, "items": ["Hammer", "Nails"], "customer": {"id": 123, "name": "Bob the Builder"}}
}
```
