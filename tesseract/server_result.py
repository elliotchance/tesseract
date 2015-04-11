import json


class ServerResult:
    def __init__(self, success, data=None, error=None, warnings=None):
        self.success = success
        self.data = data
        self.error = error
        self.warnings = warnings


    def __str__(self):
        obj = {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
        }
        return json.dumps(obj)
