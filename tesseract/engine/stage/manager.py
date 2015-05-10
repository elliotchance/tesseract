from redis import StrictRedis
from tesseract.engine.stage.order import OrderStage
from tesseract.engine.table import PermanentTable


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
    def __init__(self, redis):
        assert isinstance(redis, StrictRedis)

        self.stages = []
        self.redis = redis

    def add(self, stage_class, args):
        assert isinstance(stage_class, object)
        assert isinstance(args, (list, tuple))

        self.stages.append({
            "class": stage_class,
            "args": args,
        })

    def compile_lua(self, offset, table_name):
        lua = ''
        input_table = PermanentTable(self.redis, str(table_name))
        for stage_details in self.stages:
            stage = stage_details['class'](input_table, offset, self.redis, *stage_details['args'])
            input_table, stage_lua, offset = stage.compile_lua()
            lua += stage_lua + "\n"

        lua += "return '%s'\n" % input_table.table_name
        return lua
