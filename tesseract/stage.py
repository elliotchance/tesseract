import abc
import redis


class StageManager(object):
    """The `StageManager` is used to create the plan for the SQL query. This
    query does not have to be a `SELECT`. Once all the stages have been added
    to the manager it is then run which will cause each stage to run
    sequentially using the return value of the last stage as the input page for
    the next stage.

    The first stage must take an input page which in most cases is the input
    table and each of the stages must return a key that points to the location
    of another temporary table that will be fed into the subsequent stage.

    Attributes:
        stages (list of tesseract.engine.stage.stage.Stage): The stages to be
            run. This will be empty when you create a new `StageManager`.
    """
    def __init__(self, redis_connection):
        assert isinstance(redis_connection, redis.StrictRedis)
        self.stages = {}
        self.redis = redis_connection
        self.job = 'default'

    def add(self, stage_class, args=()):
        assert isinstance(stage_class, object)
        assert isinstance(args, (list, tuple))

        if self.job not in self.stages:
            self.stages[self.job] = []

        self.stages[self.job].append({
            "class": stage_class,
            "args": args,
        })

    def compile_lua(self, offset, table_name):
        from tesseract import table

        lua = ''
        input_table = table.PermanentTable(self.redis, str(table_name))
        for stage_details in self.stages['default']:
            stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
            input_table, stage_lua, offset = stage.compile_lua()
            lua += stage_lua + "\n"

        lua += "return '%s'\n" % input_table.table_name
        return lua

    def explain(self, table_name):
        offset = 0

        from tesseract import table

        input_table = table.PermanentTable(self.redis, str(table_name))

        if len(self.stages) == 1:
            steps = []
            for stage_details in self.stages['default']:
                stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
                steps.append(stage.explain())
        else:
            steps = {}
            for job in self.stages:
                steps[job] = []
                for stage_details in self.stages[job]:
                    stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
                    steps[job].append(stage.explain())

        return steps


class Stage(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_table, offset, r):
        from tesseract import table
        assert isinstance(input_table, table.Table)
        assert isinstance(offset, int)
        assert isinstance(r, redis.StrictRedis)

        self.input_table = input_table
        self.offset = offset
        self.redis = r

    @abc.abstractmethod
    def explain(self): # pragma: no cover
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

        self.lua.append(self.input_table.lua_iterate())
        self.lua.extend(lua)
        self.lua.append(self.input_table.lua_end_iterate())
