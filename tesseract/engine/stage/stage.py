class Stage(object):
    """This is just a container class for all stages.

    """

    def iterate_page(self, page, lua):
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
          page (string): The name of the page to iterate.
          lua (list of str): Lua code to be executed for each page.

        """
        assert isinstance(page, str)
        assert isinstance(lua, list)

        self.lua.extend([
            "local records = hgetall('%s')" % page,
            "for rowid, data in pairs(records) do",
            "    local row = cjson.decode(data)",
        ])

        self.lua.extend(lua)

        self.lua.append("end")
