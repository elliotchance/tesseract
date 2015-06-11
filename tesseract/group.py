r"""Grouping (``GROUP BY``).

Extract Expressions
-------------------

Gather up all the aggregate columns in the query and make their expressions
unique, for example:

.. code-block:: sql

   SELECT value, sum(a), sum(a + 2), sum(a) * 2
   FROM some_table

The unique aggregates would be (in no particular order)::

    sum(a)
    sum(a + 2)

It is important they are unique because we don't want to calculate them twice.
Even if we didn't care about the performance hit it is still critical they are
unique because these expressions become the key as we aggregate and so multiple
expressions would cause all values to be run twice through all the aggregate
functions.

Each unique expression becomes a key and is rendered so ``sum(x + 1)`` is the
same as ``sum(x+1)``. However, ``sum(x + 1)`` and ``sum(1 + x)`` are not the
same thing.

Grouping
--------

As we iterate the records we maintain a Redis hash called ``group`` which
contains keys that represent JSON strings and a value of `1`.

Since a query does not need to have a `GROUP BY` clause this effectively means
that all the rows in the set belong to the same group. So we give this master
group a ``true`` value to group on.

In any case the value is encoded to JSON - this ensures the value is both a
string and unique across values and equivalent values in different data types.

The following records (grouped by ``a``)::

    {"a": 123}
    {"a": true}
    {"a": "123"}
    {"a": 123}

Would be::

    "true"
    "123"
    "\"123\""

A query could contain multiple aggregate expressions and we want to keep them
independent. Our two possible solutions is to maintain a different hash for each
expression, or use a single hash but have a prefix/suffix to the keys. I chose
to use the latter separated by a colon. The hash in Redis will look like this:

.. _redis-grouping-hash:

======================  =====
Key                     Value
======================  =====
``count(*):"true"``     1
``count(*):"123"``      2
``count(*):"\"123\""``  1
======================  =====

The value is an integer that is incremented with each unique key. The number
`123` appears twice.

Lua Processing
--------------

There are two Lua functions required to produce the final result. Lets take
``AVG()`` as an example. The two Lua functions would be::

    function_avg(group, value)
    function_avg_post(unique_group, group)

``function_avg`` is run with each value as it's encountered. This is an
opportunity to track values that may be needed for post processing::

    function_avg('count(*)', 123)
    function_avg('count(*)', true)
    function_avg('count(*)', "123")
    function_avg('count(*)', 123)

Once the grouping is complete we use a post processing Lua function to calculate
the final result::

    function_avg_post('agg_key', 'count(*)')

The first argument is the Redis key that contains the
:ref:`original grouping hash <redis-grouping-hash>` so you can lookup the
original count if you need to.

Ensure Single Row
-----------------

If there is no `GROUP BY` clause we must return one row, even if the original
set did not have any rows. At the moment the default value will always be ``0``,
except in the case of ``MIN()`` and ``MAX()`` which is hard-coded to return
``null``.
"""

from tesseract import ast
from tesseract import stage
from tesseract import table


class GroupStage(stage.Stage):
    def __init__(self, input_table, offset, redis, field, columns):
        stage.Stage.__init__(self, input_table, offset, redis)
        assert field is None or isinstance(field, ast.Identifier)
        assert isinstance(columns, list)

        self.field = field
        self.columns = columns
        self.lua = []
        self.output_table = table.TransientTable(redis)

    def explain(self):
        return {
            "description": "Grouping by %s" % self.field
        }

    def __unique_group_value(self):
        """The unique group value is a name for the group contain the same
        values.

        Since a query does not need to have a `GROUP BY` clause this effectively
        means that all the rows in the set belong to the same group. So we give
        this master group a `true` value to group on.

        In any case the value is encoded to JSON - this ensure the value is both
        a string and unique across values and equivalent values in different
        data types.

        Returns:
          Lua expression that will setup a variable called `unique_group`.
        """
        unique_group = "cjson.encode(row['%s'])" % self.field
        if self.field is None:
            unique_group = "'true'"

        return "local unique_group = %s" % unique_group

    def __group_name(self, value, expression):
        """Generate a unique key when a query contains multiple expressions.

        As explained in `__lua_args()` a query could contain multiple aggregate
        expressions and we want to keep them independent. Our two possible
        solutions is to maintain a different hash for each expression, or use a
        single hash but have a prefix/suffix to the keys. I chose to use the
        latter separated by a colon.

        Arguments:
          value (str): Must be raw Lua.
          expression (Expression): The expression.

        Returns:
          Lua code to generate the key.
        """
        assert isinstance(value, str)
        assert isinstance(expression, ast.Expression)

        return '%s .. ":%s"' % (value, str(expression))

    def __lua_args(self):
        """Gather up all the aggregate columns in the query and make their
        expressions unique, for example:

            SELECT value, sum(a), sum(a + 2), sum(a) * 2
            FROM some_table

        The unique aggregates would be (in no particular order):

            sum(a)
            sum(a + 2)

        It is important they are unique because we don't want to calculate them
        twice. Even if we didn't care about the performance hit it is still
        critical they are unique because these expressions become the key as we
        aggregate and so multiple expressions would cause all values to be run
        twice through all the aggregate functions.
        """
        unique_aggregates = {}
        for col in self.columns:
            if not col.is_aggregate():
                continue

            aggregate = str(col)
            if aggregate not in unique_aggregates:
                unique_aggregates[aggregate] = col

        lua = []
        for col in unique_aggregates.values():
            lua.append("local group = %s" % self.__group_name('unique_group', col))
            lua.append(col.compile_lua(0)[0])

        return '\n'.join(lua)

    def __group_records(self):
        """Iterate the table and start grouping.

        As we iterate the records we maintain a Redis hash called `group` which
        contains keys that represent JSON strings and a value of `1`.
        """
        self.iterate_page([
            self.__unique_group_value(),
            "redis.call('HINCRBY', 'group', unique_group, 1)",
            self.__lua_args(),
        ])

    def __ensure_single_row(self):
        """If there is no `GROUP BY` clause we must return one row, even if the
        original set did not have any rows.
        """
        self.lua.extend([
            "if %s == 1 then" % self.output_table.lua_get_next_record_id(),
            "  local row = {}",
        ])

        for col in self.columns:
            if not col.is_aggregate():
                continue

            default_value = 0
            if col.function_name in ('min', 'max'):
                default_value = 'cjson.null'

            self.lua.append("row['%s'] = %s" % (str(col), default_value))

        self.lua.extend([
            self.output_table.lua_add_lua_record('row'),
            "end"
        ])

    def iterate_hash_keys(self, page, lua):
        """Iterate the keys of a hash.

        The keys are not guaranteed to come out in any particular order this
        method uses `HKEYS` to fetch the keys. For each key there will be
        several Lua variables exposed:

         * `rowid` - A simple counter (starting at 0) for each key.
         * `data` - The raw JSON string that is the record.

        Arguments:
          page (string): The name of the page to iterate.
          lua (list of str): Lua code to be executed for each page.
        """
        assert isinstance(page, str)
        assert isinstance(lua, list)

        self.lua.extend([
            "local records = redis.call('HKEYS', '%s')" % page,
            "local rowid = 0",
            "for _, data in ipairs(records) do",
        ])

        self.lua.extend(lua)

        self.lua.extend([
            "    rowid = rowid + 1",
            "end"
        ])

    def __extract_expressions(self):
        """Request all the results of the parsed group expressions.

        After all the records have been iterated and each of the expressions
        have been calculating their result along the way. Now we need to fetch
        back those results and put them into a result page.
        """
        lua = [
            "local row = {}",
            "row['%s'] = cjson.decode(data)" % self.field,
        ]

        for col in self.columns:
            if not col.is_aggregate():
                continue

            key = self.__group_name('tostring(data)', col)
            line = "row['%s'] = function_%s_post(tostring(data), %s)" % (
                str(col),
                col.function_name,
                key
            )
            lua.append(line)

        lua.append(self.output_table.lua_add_lua_record('row'))

        self.iterate_hash_keys('group', lua)

    def __clear_buffers(self):
        """Reset (delete) any buffers we will need to carry out this stage."""
        self.lua.append("redis.call('DEL', 'group')")

    def compile_lua(self):
        self.__clear_buffers()
        self.__group_records()
        self.__extract_expressions()
        self.__ensure_single_row()

        return (self.output_table, '\n'.join(self.lua), self.offset)
