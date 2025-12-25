# core_app/redis_client.py
import redis

redis_client = redis.StrictRedis(
    host='redis',  # or container name if using docker-compose
    port=6379,
    db=0,
    decode_responses=True  # so data comes back as str instead of bytes
)
