from loguru import logger
from redis.asyncio import Redis

from src.app.config.settings import settings


async def init_redis() -> Redis | None:
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    try:
        await redis.ping()
        logger.info("Соединение с Redis активно")
        return redis
    except Exception as e:
        logger.error(f"Ошибка при соединении с Redis: {e}")
        raise
