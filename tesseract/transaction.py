"""
Overview
--------

A transaction is a block of work that will not be visible until a ``COMMIT``
has been issued. Or alternatively a ``ROLLBACK`` issued will completely undo any
changes for the entire block.

Tesseract uses a `MVCC`_ (Multiversion Concurrency Control) methodology for
record visibility. There is a lot of information on how MVCC works so for the
purpose of the following example I will cover the important bits.

Most people that have used a database before expect "autocommit" where any
statement that is not explicitly in a transaction is automatically committed.
This is different to what the SQL standard states where ``START TRANSACTION`` is
implicit but the ``COMMIT`` is not.

Internals
---------

Following on, rather than surrounding every non-explicit transaction with a
``START TRANSACTION`` and ``COMMIT`` we define two states; in or not in a
transaction.

Each connection maintains its current transaction ID. The ``TransactionManager``
maintains a set of all the transaction ID for all the connections that are
explicitly in a transaction. Another way to look at it is when we say "in a
transaction" we mean the current connection's transaction ID is in this set.

Each record has two special properties (amongst others) - prefixed with a colon:

  * ``xid``: The transaction ID when the record was created.
  * ``xex``: The transaction ID when the record was deleted. This will be ``0``
    initially.

A record is visible only when all the following are true:

  1. The ``xid`` is not in the active transactions.
  2. The ``xex`` is ``0`` OR ``xex`` is not in the active transactions.

Collisions
----------

One implicit limitation of transactions is that a connection must see the same
database state, no matter how long it has been running or how many modifications
to the databases have been made. But at the same time it must guarantee that
multiple transactions are editing the most recent version of rows (updating an
expired row would have the changes lost).

At the moment tesseract handles collisions by simply throwing the error::

    Transaction failed. Will ROLLBACK.

For the transaction that does not hold the lock for the row. This is crude
solution as we should wait for that lock to be released but that's an
improvement for another day.

.. _MVCC: http://en.wikipedia.org/wiki/Multiversion_concurrency_control
"""

import redis
from tesseract import protocol
from tesseract import statement


class TransactionManager(object):
    """The TransactionManager coordinates the MVCC implementation of
    transactions in tesseract.
    """

    __instance = None

    def __init__(self, redis_connection):
        """This is for internal use only. See get_instance()."""
        assert isinstance(redis_connection, redis.StrictRedis)
        self.__next_transaction_id = 1
        self.__active_transactions = set()
        self.__redis = redis_connection
        self.__rollback_actions = []

    def active_transaction_ids(self):
        return self.__active_transactions

    def start_transaction(self):
        self.__active_transactions.add(self.__transaction_id())

    def commit(self):
        self.__end_transaction()

    def rollback(self):
        for action in self.__rollback_actions:
            self.__redis.execute_command(action)
        self.__end_transaction()

    def in_transaction(self):
        return self.__transaction_id() in self.__active_transactions

    def record(self, action):
        self.__rollback_actions.append(action)

    def next_transaction_id(self):
        self.__next_transaction_id += 1
        return self.__next_transaction_id

    @staticmethod
    def get_instance(redis_connection):
        """This is the correct way to get the transaction manager singleton
        instance.

        Arguments:
          redis_connection (redis.StrictRedis): The Redis connection.

        Returns:
          A TransactionManager instance.
        """
        assert isinstance(redis_connection, redis.StrictRedis)
        if not TransactionManager.__instance:
            TransactionManager.__instance = TransactionManager(redis_connection)

        assert isinstance(TransactionManager.__instance, TransactionManager)
        return TransactionManager.__instance

    def lua_transaction_info(self):
        from tesseract import connection

        xids = []
        for xid in self.active_transaction_ids():
            xids.append("[%d]=true" % xid)

        xid = connection.Connection.current_connection().transaction_id

        lua = " local xids = {%s} " % ' ,'.join(xids)
        lua += "local xid = %s " % xid

        return lua

    def __transaction_id(self):
        from tesseract import connection
        return connection.Connection.current_connection().transaction_id

    def __end_transaction(self):
        self.__rollback_actions = []
        try:
            self.__active_transactions.remove(self.__transaction_id())
        except KeyError:
            # COMMIT or ROLLBACK was called when not in a transaction.
            pass


class StartTransactionStatement(statement.Statement):
    def __str__(self):
        return 'START TRANSACTION'

    def execute(self, result, instance):
        manager = TransactionManager.get_instance(instance.redis)
        warnings = None

        if manager.in_transaction():
            warnings = [
                'START TRANSACTION called inside a transaction. '
                'This will be ignored.'
            ]
        else:
            manager.start_transaction()

        return protocol.Protocol.successful_response(warnings=warnings)


class CommitTransactionStatement(statement.Statement):
    def __str__(self):
        return 'COMMIT'

    def execute(self, result, instance):
        manager = TransactionManager.get_instance(instance.redis)
        warnings = None

        if manager.in_transaction():
            manager.commit()
        else:
            warnings = ['COMMIT used after transaction is complete. '
                        'This will be ignored.']

        return protocol.Protocol.successful_response(warnings=warnings)


class RollbackTransactionStatement(statement.Statement):
    def __str__(self):
        return 'ROLLBACK'

    def execute(self, result, instance):
        manager = TransactionManager.get_instance(instance.redis)
        warnings = None

        if manager.in_transaction():
            manager.rollback()
        else:
            warnings = ['ROLLBACK used after transaction is complete. '
                        'This will be ignored.']

        return protocol.Protocol.successful_response(warnings=warnings)
