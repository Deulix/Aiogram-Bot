import asyncio
import logging
import os

from aiogram import Bot, Dispatcher

from app.handlers import router
from database.redis_db import init_redis

if not os.getenv("BOT_TOKEN"):
    from dotenv import load_dotenv

    load_dotenv()


async def main():
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    redis = await init_redis()
    dp["redis"] = redis
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("BOT STOP")
