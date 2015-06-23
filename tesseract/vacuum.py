"""
Overview
--------

Vacuuming is the process of freeing up space for dead rows. The way MVCC
works for transactions means that rows are marked as expired but are not
actually deleted at the time. The act of *vacuuming* to to sweep through the
database and permanently delete (hence freeing up) the memory.

The process of vacuuming is actually more broad as it uses this time to also
clean up old cached and other items that keep the database in its' neatest form.

A separate and dedicated thread (just one thread) handles the vacuuming. To
prevent the vacuuming from getting in the way python uses the SCAN command,
checks the records for expiry then send the bulk delete commands to Redis. This
is very fast and can be throttled later if the vacuum process is consuming too
much I/O.

Using the vacuum Module
-----------------------

By including the ``vacuum`` module you will prepare (but not start) the
vacuuming thread. This is because other packages may include it like Sphinx
causing it to hang. Since it will not have the Redis connection straight away
you must set it before you invoke ``thread.start()``. The vacuum sweep will not
start until ``needs_running`` has been set to ``True``.
"""

import json
import re
import threading
import time
from tesseract import transaction

class Vacuum(object):
    """
    Attributes:
      redis (redis.StrictRedis): The Redis connection.

      needs_running (bool): Set this at anytime to ``True`` to notify the vacuum
        process it's time to start.

      stay_alive (bool): Once this is set to ``False`` the vacuum thread will
        shutdown gracefully.

      deleted_temp_tables (int): The number of temporary tables that were
        removed. There are transient tables used in the multi-stage processing
        of complex requests. Most of there are cleaned up with the query itself
        except that the last stage transient table will have to remain after the
        query to provide the result to the server. Also if the server crashed.
        In any case if the transient table does not belong to an active
        transaction it will be cleaned up now.

        This is from when the server was launched, not just the previous vacuum
        sweep.

      deleted_rows (int): Records are are expired and no longer belong to a
        transaction can be removed permanently. This is from when the server was
        launched, not just the previous vacuum sweep.
    """
    def __init__(self):
        self.redis = None
        self.needs_running = False
        self.stay_alive = True
        self.deleted_temp_tables = 0
        self.deleted_rows = 0

    def start(self):
        """Entry point for the vacuum thread.

        The vacuum sweep will only run if``needs_running`` is ``True``.
        Otherwise it will try again in 1 second. This process will go on
        indefinitely until ``stay_alive`` is ``False``.

        There is always a grace period of at least 1 second after the vacuum has
        completed. Until ``needs_running`` is set to ``True`` once again. It is
        important to note that setting ``needs_running`` while the vacuum is
        running will *not* trigger another vacuum after this one has completed
        because ``needs_running`` is set to ``False`` at the end of each vacuum
        sweep.

        It is impossible for multiple vacuums to be running at the same time.
        """
        while self.stay_alive:
            if self.redis and self.needs_running:
                self._run()
            time.sleep(1)

    def _run(self):
        """Run a vacuum.

        This should never be triggered manually and is invoked by the
        ``start()`` method. After this method is finished it will set
        ``needs_running`` to ``False``.
        """
        scan = self.redis.scan(match='tesseract:table:*')
        while scan[0] != 0:
            self._process_keys(scan[1])
            scan = self.redis.scan(match='tesseract:table:*', cursor=scan[0])
        self._process_keys(scan[1])

        self.needs_running = False

    def _process_keys(self, keys):
        """Process an array of keys for vacuuming.

        As each of the keys are processed they fall into three categories that
        determine how the vacuuming is handled.

        1. A transient table.
        2. A permanent table.
        3. Anything else.

        In the case of a transient table it is checked to see if it no longer
        belongs to a transaction and if so is removed.

        In the case of a permanent table the rows must be scanned for
        permanently expired rows to be removed.

        Anything else is ignored.

        Arguments:
          keys (list)
        """
        assert isinstance(keys, list)

        manager = transaction.TransactionManager.get_instance(self.redis)
        active_xids = manager.active_transaction_ids()

        for key in keys:
            # Delete left over temp tables.
            if re.match(r'^tesseract:table:tmp_\d+_[a-z]{8}$', key):
                self.__vacuum_temp_table(active_xids, key)

            # Scan for rows to be deleted in transactional tables.
            elif re.match(r'^tesseract:table:[^:]+$', key):
                self.__vacuum_real_table(active_xids, key)

    def __vacuum_real_table(self, active_xids, key):
        scan = self.redis.zscan(key)
        while scan[0] != 0:
            for row in scan[1]:
                raw = json.loads(row[0])
                if ':xex' in raw and raw[':xex'] != 0 \
                        and raw[':xex'] not in active_xids:
                    self.redis.zremrangebyscore(key, raw[':id'], raw[':id'])
                    self.deleted_rows += 1
            scan = self.redis.zscan(key, cursor=scan[0])

    def __vacuum_temp_table(self, active_xids, key):
        xid = int(key.split('_')[1])
        if xid not in active_xids:
            self.redis.delete(key, '%s:rowid' % key)
            self.deleted_temp_tables += 1


# Prepare the vacuum thread.
vacuum = Vacuum()
thread = threading.Thread(target=vacuum.start)
