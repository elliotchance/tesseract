FAQ
===

Really? Another SQL Database?
-----------------------------

Yes, but not really. The SQL language was designed to work within a relational
database so not all of the SQL standard makes sense to a document store.
However, this hasn't stopped popular SQL vendors from implementing their own
extensions to the standard that allow the database to be used like this.


I Thought SQL Was Dead?
-----------------------

That is a discussion greater than one product like tesseract can answer. I will
offer my perspective on the issue since it shapes the goals and development of
tesseract.

There is a lot of knowledge in the SQL language and framework that should not
be dismissed simply because "it is old" or that it carries the stigma of only
being usful in a relational model.

Over recent years there has been a fashionable snobbery to existing database
systems in favour of the NoSQL solutions. If you stop and think about it the
only thing categorising these databases is that they do not use the SQL language
(understandable) but there has been no strides into a text based abstract
language. This is less about portability - it's very unlikely that people change
database products - and more about being about to use a product easily and
reliably from the start.


What Are the Goals of Tesseract?
--------------------------------

Based on the discussion above.

1. Follow as much of the SQL standard that makes sense.

2. Provide SQL language extensions to make it easier dealing with objects and
   nested data.

3. `KISS`_.

.. _KISS: http://en.wikipedia.org/wiki/KISS_principle
