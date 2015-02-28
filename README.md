**tesseract** is a database that combines the power of SQL with the flexibility
of JSON storage. A hybrid, taking the best from seamingly incompatible
technologies.

It is backed by Redis as the storage engine and the processor of the the hard
work meaning it can be very fast and written in pure python.

Enough talk, show me!

```
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

```
tesseract> select * from people where first_name like "B%";
[
  {"first_name": "Bob", "last_name": "Smith", "children": ["Sally", "Bob Jnr."]}
]
```

tesseract> select first_name, len(children) as children, children[0] as first
         > from people;
[
  {"first_name": "Bob", "children": 2, "first": "Sally"}
  {"first_name": "John", "children": 1, "first": "Bill"}
]

tesseract> select sort(sum(children)) from people;
[
  {"sort(sum(children))": ["Bill", "Bob Jnr.", "Sally"]}
]

tesseract> select first_name + " " + last_name as _key, {"has": count(children)} as _value
         > from people;
{
  "Bob Smith": {"has": 2},
  "John Williams": {"has": 1},
}
```
