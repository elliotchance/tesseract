Tesseract
=========

.. image:: https://travis-ci.org/elliotchance/tesseract.svg?branch=master
   :target: https://travis-ci.org/elliotchance/tesseract

.. image:: https://coveralls.io/repos/elliotchance/tesseract/badge.svg?branch=master
   :target: https://coveralls.io/r/elliotchance/tesseract?branch=master

.. image:: https://scrutinizer-ci.com/g/elliotchance/tesseract/badges/quality-score.png?b=master
   :target: https://scrutinizer-ci.com/g/elliotchance/tesseract/?branch=master

**tesseract** is a SQL object database with Redis as the backend, think of it
like a document store that you run SQL statements against.

Since it is backed by Redis and queries are compiled to Lua it makes running
complex queries on complex data very fast (all considered). The entire server is
written in Python and uses an
[extremely simply client protocol](server-protocol.html).

.. toctree::
   :maxdepth: 1
   :numbered:

   getting-started
   sql-reference
   functions-operators
   engine
   testing
   client-libraries
   changelog
   faq
   appendix
