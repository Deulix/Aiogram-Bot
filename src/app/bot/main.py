import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from src.app.bot.handlers.admin_handlers import admin_router
from src.app.bot.handlers.cart_handlers import cart_router
from src.app.bot.handlers.navigation_handlers import navigation_router
from src.app.bot.handlers.order_handlers import order_router
from src.app.bot.handlers.payment_handlers import payment_router
from src.app.config.logger import logger, setup_logging
from src.app.config.settings import settings
from src.app.database.redis_db import init_redis
from src.app.database.sqlite_db import init_async_sqlite

routers = [navigation_router, payment_router, admin_router, cart_router, order_router]


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
    dp.include_routers(*routers)
    logger.info("Все сервисы запущены")
    logger.info("FastAPI доступен по адресу http://localhost:8000/")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
