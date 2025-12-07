import asyncio
import sys

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger

from src.app.bot.handlers import handlers_router
from src.app.bot.payments import payments_router
from src.app.config.settings import settings
from src.app.database.redis_db import init_redis
from src.app.database.sqlite_db import init_async_sqlite


def setup_logging():
    logger.remove()

    logger.add(
        sink=sys.stderr,
        level="INFO",
        colorize=True,
        format="<green>{time:DD-MM-YYYY HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    logger.add(
        sink="/bot_app/logs/bot_history.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )


async def main():
    load_dotenv()
    setup_logging()
    logger.info("Логирование запущено")
    bot = Bot(settings.BOT_TOKEN)
    dp = Dispatcher()
    redis = await init_redis()
    sqlite_db = await init_async_sqlite()
    dp["redis"] = redis
    dp["db"] = sqlite_db
    dp.include_router(handlers_router)
    dp.include_router(payments_router)
    logger.info("Все сервисы запущены")
    logger.debug("Debug")
    logger.info("Info")
    logger.warning("Warning")
    logger.error("Error")
    logger.critical("Critical")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
