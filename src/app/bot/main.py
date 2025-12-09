import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from src.app.bot.handlers.handlers import handlers_router
from src.app.bot.payments.payments import payments_router
from src.app.config.logger import logger, setup_logging
from src.app.config.settings import settings
from src.app.database.redis_db import init_redis
from src.app.database.sqlite_db import init_async_sqlite


async def main():
    load_dotenv()
    setup_logging()
    logger.info("Логирование бота запущено")
    bot = Bot(settings.BOT_TOKEN)
    dp = Dispatcher()
    redis = await init_redis()
    sqlite_db = await init_async_sqlite()
    dp["redis"] = redis
    dp["db"] = sqlite_db
    dp.include_router(handlers_router)
    dp.include_router(payments_router)
    logger.info("Все сервисы запущены")
    logger.info("FastAPI доступен по адресу http://localhost:8000/")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
