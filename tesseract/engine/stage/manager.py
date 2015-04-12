class StageManager:
    def __init__(self):
        self.stages = []

    def add(self, stage_class, args):
        assert isinstance(stage_class, object)
        assert isinstance(args, (list, tuple)), '%r' % args

        self.stages.append({
            "class": stage_class,
            "args": args,
        })

    def compile_lua(self, offset, table_name):
        lua = ''
        input_page = table_name
        for stage_details in self.stages:
            stage = stage_details['class'](str(input_page), offset, *stage_details['args'])
            input_page, stage_lua, offset = stage.compile_lua()
            lua += stage_lua + "\n"

        lua += "return '%s'\n" % input_page
        return lua
