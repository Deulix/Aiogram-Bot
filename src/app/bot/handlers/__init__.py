from src.app.bot.handlers.admin_handlers import admin_router
from src.app.bot.handlers.cart_handlers import cart_router
from src.app.bot.handlers.navigation_handlers import navigation_router
from src.app.bot.handlers.order_handlers import order_router
from src.app.bot.handlers.payment_handlers import payment_router

__all__ = [
    "navigation_router",
    "payment_router",
    "admin_router",
    "cart_router",
    "order_router",
]
