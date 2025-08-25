import os
from redis.asyncio import Redis


async def init_redis():
    redis = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=os.getenv("REDIS_PORT", 6379),
        decode_responses=True,
    )
    try:
        await redis.ping()
        print("REDIS CONNECTED")
        return redis
    except Exception as e:
        print(f"CONNECTION DENIED: {e}")
        raise
