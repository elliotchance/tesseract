import redis
from tesseract import vacuum

class Instance:
    """An instance contains all the state of one instance. It is the job of the
    Server to create, maintain and interact with one instance. It is possible
    in the future we will let the Server utilise several instances for
    sharding against multiple Redis nodes - but for now lets keep it simple.
    """

    def __init__(self, server, redis_host=None):
        assert redis_host is None or isinstance(redis_host, str)

        self.server = server

        # The default Redis host is `localhost` if it is not provided.
        if not redis_host:
            redis_host = 'localhost'

        # The Redis host must be a `str`.
        assert isinstance(redis_host, str)

        # Attempt to connect.
        self.redis = redis.StrictRedis(host=redis_host, port=6379, db=0)
        self.redis.set('tesseract_server', 1)

        # Start vacuum
        vacuum.vacuum.redis = self.redis
        vacuum.thread.start()

        self.notifications = {}
        self.reset_warnings()

    def publish(self, name, value):
        self.redis.publish(name, value)

    def log(self, message):
        print(message)

    def reset_warnings(self):
        self.warnings = []

    def exit(self):
        vacuum.vacuum.stay_alive = False
        self.log("Server shutting down.")
