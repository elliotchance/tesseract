from tesseract.server_result import ServerResult


class Delete:
    def execute(self, result, redis):
        # Delete the whole table.
        redis.delete(result.statement.table_name)

        # Remove the row counter.
        row_id_key = '%s_rowid' % result.statement.table_name
        redis.delete(row_id_key)

        return ServerResult(True)
