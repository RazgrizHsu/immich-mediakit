import pickle
import redis
from util import log

lg = log.get(__name__)


class RedisCache:
    def __init__(self, redisUrl, prefix='cache:'):
        self.client = redis.from_url(redisUrl)
        self.prefix = prefix

    def get(self, key):
        try:
            val = self.client.get(f"{self.prefix}{key}")
            return pickle.loads(val) if val else None
        except Exception as e:
            lg.error(f"RedisCache get error: {e}")
            return None

    def set(self, key, val, expire=3600):
        try:
            self.client.setex(f"{self.prefix}{key}", expire, pickle.dumps(val))
        except Exception as e:
            lg.error(f"RedisCache set error: {e}")

    def delete(self, key):
        try:
            self.client.delete(f"{self.prefix}{key}")
        except Exception as e:
            lg.error(f"RedisCache delete error: {e}")
