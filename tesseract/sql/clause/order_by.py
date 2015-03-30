from tesseract.sql.expressions import Identifier


class OrderByClause:
    def __init__(self, field_name, ascending):
        assert isinstance(field_name, Identifier)
        assert ascending is None or isinstance(ascending, bool)

        self.field_name = field_name
        self.ascending = ascending

    def __str__(self):
        direction = ''
        if self.ascending:
            direction = ' ASC'

        return 'ORDER BY %s%s' % (self.field_name, direction)
