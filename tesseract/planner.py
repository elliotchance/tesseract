from tesseract import ast
from tesseract import group
from tesseract import index
from tesseract import select
from tesseract import stage
from tesseract import table
import redis
import re


class SelectPlanner(object):
    def __init__(self, select_stmt, redis_connection):
        assert isinstance(select_stmt, select.SelectStatement)
        assert isinstance(redis_connection, redis.StrictRedis)
        self._select = select_stmt
        self._redis = redis_connection

    def plan(self):
        stages = stage.StageManager(self._redis)
        return self._compile_select(stages, self._select)

    def compile_lua(self):
        offset = 2
        args = []

        lua = """
-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end
"""

        stages = self.plan()
        lua += stages.compile_lua(offset, self._select.table_name)

        return (lua, args, stages)

    def _compile_select(self, stages, select_stmt):
        if isinstance(select_stmt, select.SelectStatement) and \
                isinstance(select_stmt.table_name, ast.AliasExpression):
            subquery = select_stmt.table_name.expression
            assert isinstance(subquery, select.SubqueryExpression)
            stages.job = str(select_stmt.table_name.alias)
            select_stmt.table_name = ast.Identifier('<%s>' % stages.job)
            self._compile_select(stages, subquery.select)
            stages.job = 'default'

        self.__compile_from_and_where(stages, select_stmt)
        self.__compile_group(stages, select_stmt)
        self.__compile_order(stages, select_stmt)
        self.__compile_columns(stages, select_stmt)
        self.__compile_limit(stages, select_stmt)

        return stages

    @staticmethod
    def __is_to_value(e):
        if e.right.value == 'null':
            return [ast.Value(None)]
        if e.right.value == 'true':
            return [ast.Value(True)]
        if e.right.value == 'false':
            return [ast.Value(False)]

        return []

    def __index_matches(self, stages, rule, index_name, select_stmt):
        # noinspection PyCallingNonCallable
        looking_for = rule['index_name'](select_stmt.where)
        if self._redis.hget('indexes', index_name).decode() == looking_for:
            # noinspection PyCallingNonCallable
            args = rule['args'](select_stmt.where)
            if len(args) > 0:
                args.insert(0, index_name)
                stages.add(index.IndexStage, args)
                return True

    def __find_index(self, stages, select_stmt):
        """Try and find an index that can be used for the WHERE expression. If
        and index is found it is added to the query plan.

        Returns:
          If an index was found True is returned, else False.
        """
        rules = self.__index_rules(select_stmt.table_name)
        signature = select_stmt.where.signature()
        rule = None
        for r in rules.keys():
            if re.match(r, signature):
                rule = r
                break

        if rule:
            index_manager = index.IndexManager.get_instance(self._redis)
            table_name = str(select_stmt.table_name)
            indexes = index_manager.get_indexes_for_table(table_name)
            for index_name in indexes:
                if self.__index_matches(stages, rules[rule], index_name, select_stmt):
                    return True

        return False

    def __index_rules(self, tn):
        return {
            '^@I = @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': lambda e: [e.right],
            },
            '^@V. = @I$': {
                'index_name': lambda e: '%s.%s' % (tn, e.right),
                'args': lambda e: [e.left],
            },
            '^@I IS @V.$': {
                'index_name': lambda e: '%s.%s' % (tn, e.left),
                'args': self.__is_to_value,
            },
        }

    def __compile_from_and_where(self, stages, select_stmt):
        """When compiling the WHERE clause we need to do a few things:

        1. Verify the WHERE clause is not impossible. This is when the
           expression will always be false like 'x = null'.

        2. See if there is an available index with __find_index() - hopefully
           there is.

        3. Otherwise we fall back to a full table scan.
        """
        if str(select_stmt.table_name) == str(select.SelectStatement.NO_TABLE):
            stages.add(select.NoTableStage)
        elif select_stmt.where:
            if select_stmt.where.signature() == '@I = @Vn':
                stages.add(select.ImpossibleWhereStage)
            else:
                index_found = self.__find_index(stages, select_stmt)
                if not index_found:
                    stages.add(table.FullTableScan, (select_stmt.table_name,))
                    stages.add(select.WhereStage, (select_stmt.where,))
        else:
            stages.add(table.FullTableScan, (select_stmt.table_name,))

    def __compile_group(self, stages, select_stmt):
        if select_stmt.group or select_stmt.contains_aggregate():
            stages.add(group.GroupStage, (select_stmt.group, select_stmt.columns))

    def __compile_order(self, stages, select_stmt):
        if select_stmt.order:
            stages.add(select.OrderStage, (select_stmt.order,))

    def __compile_columns(self, stages, select_stmt):
        """Compile the `SELECT` columns."""
        if len(select_stmt.columns) > 1 or str(select_stmt.columns[0]) != '*':
            stages.add(select.ExpressionStage, (select_stmt.columns,))

    def __compile_limit(self, stages, select_stmt):
        if select_stmt.limit:
            stages.add(select.LimitStage, (select_stmt.limit,))
