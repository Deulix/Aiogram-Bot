from aiogram.types import CallbackQuery
from redis.asyncio import Redis

from src.app.bot.core.callbacks import ProductCallback
from src.app.database.sqlite_db import AsyncSQLiteDatabase


class Cart:
    def __init__(self, user_id: int, redis: Redis, db: AsyncSQLiteDatabase):
        self.user_id = user_id
        self.db = db
        self.redis = redis
        self.cart_key = f"cart:{user_id}"
        self.amount_key = f"cart_amount:{user_id}"

    async def get_cart_items(self):
        dict_cart_items: dict[str, str] = await self.redis.hgetall(self.cart_key)
        cart_items = []
        for item_key, quantity in dict_cart_items.items():
            _, product_id, size = item_key.split(":")
            quantity = int(quantity)
            product = await self.db.get_product_by_id(product_id)
            cart_items.append((product, size, quantity))
        category_order = ["pizza", "snack", "cake", "drink"]
        return tuple(
            sorted(
                cart_items,
                key=lambda x: (category_order.index(x[0].category), x[0].name),
            )
        )

    async def get_current_price_amount(self):
        current_amount = await self.redis.get(self.amount_key)
        return float(current_amount) if current_amount else 0.0

    async def add_price_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def sub_price_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, -price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def clear(self):
        await self.redis.delete(self.cart_key)
        await self.redis.delete(self.amount_key)

    async def delete_product(self, product_id: str, size: str):
        await self.redis.hdel(self.cart_key, f"product:{product_id}:{size}")

    async def increase_prod_count(self, product_id: str, size: str):
        await self.redis.hincrby(self.cart_key, f"product:{product_id}:{size}", 1)

    async def decrease_prod_count(self, product_id: str, size: str):
        await self.redis.hincrby(self.cart_key, f"product:{product_id}:{size}", -1)


async def getall(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    user_id = callback.from_user.id
    cart = Cart(user_id, redis, db)
    product = await db.get_product_by_id(callback_data.product_id)
    size = callback_data.size
    product_key = f"product:{product.id}:{size}"

    products = await db.get_products_by_category(product.category)

    return (
        cart,
        product,
        size,
        products,
        product_key,
    )
