from aiogram.types import CallbackQuery
from redis.asyncio import Redis

from src.app.database.models import Product
from src.app.database.sqlite_db import AsyncSQLiteDatabase


async def getall(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[Product, str, "Cart", str, int, list]:
    id = callback.data.split("_")[-2]
    product = await db.get_product_by_id(id)
    size = callback.data.split("_")[-1]
    cart_key = f"cart:{callback.from_user.id}"
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    full_callback = f"{id}_{size}"
    quantity = await redis.hget(cart_key, full_callback) or 0

    return (
        product,
        size,
        cart,
        full_callback,
        int(quantity),
    )


class Cart:
    def __init__(self, user_id: int, redis: Redis):
        self.user_id = user_id
        self.redis = redis
        self.cart_key = f"cart:{user_id}"
        self.amount_key = f"cart_amount:{user_id}"

    async def get_current_amount(self):
        current_amount = await self.redis.get(self.amount_key)
        return float(current_amount) if current_amount else None

    async def add_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def sub_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, -price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def clear(self):
        await self.redis.delete(self.cart_key)
        await self.redis.delete(self.amount_key)

    async def delete_product(self, full_callback: str):
        await self.redis.hdel(self.cart_key, full_callback)

    async def increase_prod_count(self, full_callback: str):
        await self.redis.hincrby(self.cart_key, full_callback, 1)

    async def decrease_prod_count(self, full_callback: str):
        await self.redis.hincrby(self.cart_key, full_callback, -1)


async def get_cart_items(
    user_id: int, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[tuple[Product, str, int]]:
    cart_key = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart_key)
    cart_items = []
    for item_key, quantity in dict_cart_items.items():
        id = item_key.split("_")[0]
        size = item_key.split("_")[-1]
        product = await db.get_product_by_id(id)
        cart_items.append((product, size, int(quantity)))
    category_order = ["pizza", "snack", "cake", "drink"]
    return tuple(
        sorted(
            cart_items,
            key=lambda x: (category_order.index(x[0].category), x[0].name.lower()),
        )
    )
