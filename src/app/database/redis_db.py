from redis.asyncio import Redis
from src.app.config.settings import settings


async def init_redis():
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    try:
        await redis.ping()
        print("REDIS CONNECTED")
        return redis
    except Exception as e:
        print(f"CONNECTION DENIED: {e}")
        raise
