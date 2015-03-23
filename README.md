[![Build Status](https://travis-ci.org/elliotchance/tesseract.svg?branch=master)](https://travis-ci.org/elliotchance/tesseract)

**tesseract** is a distributed SQL object database with Redis as the backend,
think of it like a document store that you run SQL statements against.

It is distributed in that there is no central server, every client is a server
and every client can connect to multiple Redis nodes so there is no single point
of failure.

Since it is backed by Redis and queries are compiled to Lua it makes running
complex queries on complex data very fast and so the entire client can be
written in Python with no (practical) impact on speed.

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
   {
      "first_name":"Bob",
      "last_name":"Smith",
      "children":[
         "Sally",
         "Bob Jnr."
      ]
   },
   {
      "first_name":"John",
      "last_name":"Williams",
      "children":[
         "Bill"
      ]
   }
]
```

OK, great, nothing special there. Let's just dive straight into it:

```sql
tesseract> select first_name || ' ' || last_name as name,
         >     children,
         >     len(children) as total
         > from people
         > where first_name like "B%";
[
   {
      "name":"Bob Smith",
      "children":[
         "Sally",
         "Bob Jnr."
      ],
      "total":2
   }
]
```

Since we are dealing with objects (that may contain several levels) and not
simple rows, we can focus queries to subitems:

```sql
tesseract> select *
         > from people.children as child
         > order by child;
[
   {
      "child":"Bill"
   },
   {
      "child":"Bob Jnr."
   },
   {
      "child":"Sally"
   }
]
```

Unless otherwise specified you will always get an array of objects. However, you
can specify a custom `rownum`:

```sql
tesseract> select first_name + " " + last_name as rownum, children
         > from people;
{
   "Bob Smith":{
      "children":[
         "Sally",
         "Bob Jnr."
      ],
   },
   "John Williams":{
      "children":[
         "Bill"
      ]
   }
}
```

Here are some more complex examples:

```sql
tesseract> insert into customer
         >     {"id": 123, "name": "Bob the Builder"};
tesseract> insert into item
         >     {"id": 100, "name": "Wood"},
         >     {"id": 101, "name": "Hammer"},
         >     {"id": 102, "name": "Nails"};
tesseract> insert into order
         >     {"id": 456, "customer_id": 123, "items": [101, 102]},
         >     {"id": 789, "customer_id": 123, "items": [100]};
```

If we did a SQL-like join:

```sql
tesseract> select *
         > from customer
         > join order on customer.id = order.customer_id
         > join items on item.id = each(order.items);
[
   {
      "customer_id":123,
      "customer_name":"Bob the Builder",
      "order_id":456,
      "items":[101, 102],
      "item_id":101,
      "item_name":"Hammer"
   },
   {
      "customer_id":123,
      "customer_name":"Bob the Builder",
      "order_id":456,
      "items":[101, 102],
      "item_id":102,
      "item_name":"Nails"
   },
   {
      "customer_id":123,
      "customer_name":"Bob the Builder",
      "order_id":789,
      "items":[100],
      "item_id":100,
      "item_name":"Wood"
   },
]
```

The results that come back are not in a very good format for traversing. In most
cases you will want a more hierarchical response. The most basic way to handle
this is with sub-selects:

```sql
tesseract> select id as rownum, name, (
         >       select order.id as rownum, (
         >          select * from item where id in order.items
         >       ) as items
         >       where order.customer_id = customer.id
         >    ) as orders
         > from customer;
{
   "123":{
      "name":"Bob the Builder",
      "orders":{
         "456": {"items": ["Hammer", "Nails"]},
         "789": {"items": ["Wood"]}
      }
   }
}
```
