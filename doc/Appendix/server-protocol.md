% Server Protocol

The server protocol used by tesseract is pure JSON. This makes it very easy for
any language or system to interact with - even `telnet` if you don't mind typing
the JSON.


Connect
=======

There is currently no authentication required for connecting. So simply knowing
the host and port is sufficient for making a connection.

It is a plain TCP connection that normally runs on port 3679.


Request
=======

The request is a JSON object:

```json
{
  "sql": "SELECT 1 + 2"
}
```


Response
========

If the response is successful:

```json
{
  "success": true,
  "data": [
    {
      "col1": 3
    }
  ]
}
```

If the response is an error:

```json
{
  "success": false,
  "error": "Oh noes!"
}
```

Warnings are not considered a failure, so a prudent client should check to see
if the `warnings` is present in the response:

```json
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
```
