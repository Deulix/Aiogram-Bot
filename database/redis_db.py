from redis.asyncio import Redis


async def init_redis():
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    try:
        await redis.ping()
        print("REDIS CONNECTED")
        return redis
    except Exception as e:
        print(f"CONNECTION DENIED: {e}")
        raise
