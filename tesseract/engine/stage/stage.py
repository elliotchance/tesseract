from redis import StrictRedis
from tesseract.engine.table import Table
import abc


class Stage(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_table, offset, redis):
        assert isinstance(input_table, Table)
        assert isinstance(offset, int)
        assert isinstance(redis, StrictRedis)

        self.input_table = input_table
        self.offset = offset
        self.redis = redis

    @abc.abstractmethod
    def explain(self):
        pass

    def iterate_page(self, lua):
        """Iterate a page and run some lua against each record.

        For each record read from the page there will be several initialized lua
        variables:

          * `rowid` - A unique integer that is an ID for the record. You cannot
            rely on this value staying the same for the same records against
            multiple sets - for instance it may change once or more between each
            stage.
          * `data` - The raw JSON (as a string) that is the record.
          * `row` - The decoded JSON (as a Lua table).

        Arguments:
          lua (list of str): Lua code to be executed for each page.

        """
        assert isinstance(lua, list)

        self.lua.append(self.input_table.lua_iterate(decode=True))
        self.lua.extend(lua)
        self.lua.append("end")
