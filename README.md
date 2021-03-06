[![Build Status](https://travis-ci.org/elliotchance/tesseract.svg?branch=master)](https://travis-ci.org/elliotchance/tesseract)
[![Coverage Status](https://coveralls.io/repos/elliotchance/tesseract/badge.svg?branch=master)](https://coveralls.io/r/elliotchance/tesseract?branch=master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/elliotchance/tesseract/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/elliotchance/tesseract/?branch=master)

**tesseract** is a SQL object database with Redis as the backend, think of it
like a document store that you run SQL statements against.

Since it is backed by Redis and queries are compiled to Lua it makes running
complex queries on complex data very fast (all considered). The entire server is
written in Python and uses an [extremely simply client protocol](https://github.com/elliotchance/tesseract/blob/master/doc/4_Appendix/Server_Protocol.md).


Installation
------------

Since tesseract is very alpha I have not uploaded releases yet to `pip` so the
easiest way get it is to clone out the repo and run off the stable `master`
branch.

```bash
git clone https://github.com/elliotchance/tesseract.git
```


Running the Server
------------------

You must have Redis running locally on the standard port. If not, run:

```bash
redis-server &
```

Then start the tesseract server. It's not wise to run it in the background so
you can pay attension to errors and crashes during this wonderful time of
testing.

```bash
bin/tesseract
```

Remember that if you pull the latest changes for tesseract you will have to
restart the server for those changes to take effect. Simply CTRL+C and run the
command above again.


Examples
--------

```sql
insert into people {
  "first_name": "Bob",
  "last_name": "Smith",
  "children": [ "Sally", "Bob Jnr." ]
};

insert into people {
  "first_name": "John",
  "last_name": "Williams",
  "children": [ "Bill" ]
};
         
select * from people;
```

```json
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
select first_name || ' ' || last_name as name,
    children,
    len(children) as total
from people
where first_name like "B%";
```

```json
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
select *
from people.children as child
order by child;
```

```json
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
select first_name + " " + last_name as rownum, children
from people;
```

```json
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
insert into customer
    {"id": 123, "name": "Bob the Builder"};
insert into item
    {"id": 100, "name": "Wood"},
    {"id": 101, "name": "Hammer"},
    {"id": 102, "name": "Nails"};
insert into order
    {"id": 456, "customer_id": 123, "items": [101, 102]},
    {"id": 789, "customer_id": 123, "items": [100]};
```

If we did a SQL-like join:

```sql
select *
from customer
join order on customer.id = order.customer_id
join items on item.id = each(order.items);
```

```json
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
select id as rownum, name, (
      select order.id as rownum, (
         select * from item where id in order.items
      ) as items
      where order.customer_id = customer.id
   ) as orders
from customer;
```

```json
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
