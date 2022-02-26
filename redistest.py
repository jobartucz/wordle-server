import os
import redis

r = redis.from_url(os.environ.get("REDIS_URL"))
