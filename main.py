import asyncio
import logging
import os

from aiogram import Bot, Dispatcher

from app.handlers import router
from database.redis_db import init_redis
from database.sqlite_db import init_async_sqlite


async def main():
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    redis = await init_redis()
    sqlite_db = await init_async_sqlite()
    dp["redis"] = redis
    dp["db"] = sqlite_db
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
    
