from tesseract.server_result import ServerResult


class Delete:
    def execute(self, result, redis):
        redis.delete(result.statement.table_name)
        return ServerResult(True)
