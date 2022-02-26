import os
import redis

r = redis.from_url(os.environ.get("REDIS_URL"))

r.set('foo', 'bar')
value = r.get('foo')
print(value)
