import asyncio
import logging
from src.app.config.settings import settings

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from src.app.bot.handlers import handlers_router
from src.app.bot.payments import payments_router
from src.app.database.redis_db import init_redis
from src.app.database.sqlite_db import init_async_sqlite


async def main():
    load_dotenv()
    bot = Bot(settings.BOT_TOKEN)
    dp = Dispatcher()
    redis = await init_redis()
    sqlite_db = await init_async_sqlite()
    dp["redis"] = redis
    dp["db"] = sqlite_db
    dp.include_router(handlers_router)
    dp.include_router(payments_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
