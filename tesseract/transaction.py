"""This module handles SQL transactions. A transaction is a block of work that
will not be visible until a COMMIT has been issued. Or alternatively a ROLLBACK
issued will completely undo any changes for the entire block.
"""

import redis
from tesseract import client
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
        self.__rollback_action = None

    def start_transaction(self):
        self.__active_transactions.add(self.__connection_id())

    def commit(self):
        self.__end_transaction()

    def rollback(self):
        self.__end_transaction()
        if self.__rollback_action:
            self.__redis.execute_command(self.__rollback_action)

    def in_transaction(self):
        return self.__connection_id() in self.__active_transactions

    def record(self, action):
        self.__rollback_action = action

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

    def __connection_id(self):
        from tesseract import connection
        return connection.Connection.current_connection().connection_id

    def __end_transaction(self):
        try:
            self.__active_transactions.remove(self.__connection_id())
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

        return client.Protocol.successful_response(warnings=warnings)


class CommitTransactionStatement(statement.Statement):
    def __str__(self):
        return 'COMMIT'

    def execute(self, result, instance):
        manager = TransactionManager.get_instance(instance.redis)
        manager.commit()

        return client.Protocol.successful_response()


class RollbackTransactionStatement(statement.Statement):
    def __str__(self):
        return 'ROLLBACK'

    def execute(self, result, instance):
        manager = TransactionManager.get_instance(instance.redis)
        manager.rollback()

        return client.Protocol.successful_response()
