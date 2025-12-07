import logging

from redis.asyncio import Redis

from src.app.config.settings import settings

logger = logging.getLogger(__name__)


async def init_redis() -> Redis | None:
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    try:
        await redis.ping()
        logger.info("REDIS CONNECTED")
        return redis
    except Exception as e:
        logger.error(f"CONNECTION DENIED: {e}")
        raise
