CREATE NOTIFICATION
===================

`CREATE NOTIFICATION` tells the tesseract server to publish changes to the Redis
pub/sub model.

Syntax
------

    CREATE NOTIFICATION <notification_name>
    ON <table_name>

**_notification_name_**

The name of the notification must be unique and non-existent. It follows the
same rules as naming an entity like a table.

**_table_name_**

The table to watch for changes.
