"""The server protocol used by tesseract is pure JSON. This makes it very easy
for any language or system to interact with - even ``telnet`` if you don't mind
typing the JSON.


Connect
-------

There is currently no authentication required for connecting. So simply knowing
the host and port is sufficient for making a connection.

It is a plain TCP connection that normally runs on port 3679.


Request
-------

The request is a JSON object:

.. code-block:: json

   {
     "sql": "SELECT 1 + 2"
   }


Response
--------

If the response is successful:

.. code-block:: json

   {
     "success": true,
     "data": [
       {
         "col1": 3
       }
     ]
   }

If the response is an error:

.. code-block:: json

   {
     "success": false,
     "error": "Oh noes!"
   }

Warnings are not considered a failure, so a prudent client should check to see
if the ``warnings`` is present in the response:

.. code-block:: json

   {
     "success": true,
     "data": [
       {
         "col1": 3
       }
     ],
     "warnings": [
       "Take note..."
     ]
   }
"""

class Protocol:
    """This class handles the basic protocols that tesseract uses to communicate
    with the server. You can read how the protocol works in the documentation
    under Appendix > Server Protocol.
    """

    @staticmethod
    def successful_response(data=None, warnings=None):
        # If there is no data to be returned (for instance a `DELETE` statement)
        # then you should provide `None`.
        assert data is None or isinstance(data, (list, dict))

        # Warning are of course optional.
        assert warnings is None or isinstance(warnings, list)

        # Build the response.
        response = {
            "success": True
        }
        if data is not None:
            response['data'] = data
        if warnings is not None:
            response['warnings'] = warnings

        return response

    @staticmethod
    def failed_response(error):
        assert isinstance(error, str)
        return {
            "success": False,
            "error": error
        }

    @staticmethod
    def sql_request(sql):
        assert isinstance(sql, str)
        return {
            "sql": sql,
        }
