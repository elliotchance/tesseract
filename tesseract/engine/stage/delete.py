from tesseract.engine.stage.where import WhereStage


class DeleteStage(WhereStage):
    def action_on_match(self):
        return "redis.call('HDEL', '%s', rowid)" % self.input_page
