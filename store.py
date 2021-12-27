import redis

from secret import get_redis_url

redis_url = get_redis_url()
db = redis.from_url(redis_url)
