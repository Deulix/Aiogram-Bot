from unittest.mock import AsyncMock

import pytest

from src.app.bot.services.cart_service import Cart

# self.cart_key = f"cart:{user_id}"
# self.amount_key = f"cart_amount:{user_id}"


@pytest.mark.asyncio
async def test_cart_clear():
    mock_redis = AsyncMock()
    mock_db = AsyncMock()

    cart = Cart(user_id=123, redis=mock_redis, db=mock_db)

    await cart.clear()
    mock_redis.delete.assert_any_call("cart:123")
    mock_redis.delete.assert_any_call("cart_amount:123")

    # async def add_price_amount(self, price: float):
    #     await self.redis.incrbyfloat(self.amount_key, price)
    #     await self.redis.expire(self.amount_key, 3600 * 12)
    #     await self.redis.expire(self.cart_key, 3600 * 12)


@pytest.mark.asyncio
async def test_cart_hincrby():
    mock_redis = AsyncMock()
    mock_db = AsyncMock()

    cart = Cart(user_id=123, redis=mock_redis, db=mock_db)

    await cart.add_price_amount(123.45)
    mock_redis.incrbyfloat.assert_any_call("cart_amount:123", 123.45)
    mock_redis.expire.assert_any_call("cart_amount:123", 3600 * 12)
    mock_redis.expire.assert_any_call("cart:123", 3600 * 12)


@pytest.mark.asyncio
async def test_get_cart_items():
    mock_redis = AsyncMock()
    mock_db = AsyncMock()

    mock_redis.hgetall.return_value = {
        "product:1:large": "1",
        "product:2:small": "2",
        "product:3:small": "3",
        "product:4:small": "4",
    }

    mock_product_1 = AsyncMock()
    mock_product_1.category = "pizza"
    mock_product_1.name = "Пепперони"

    mock_product_2 = AsyncMock()
    mock_product_2.category = "snack"
    mock_product_2.name = "Картошка фри"

    mock_product_3 = AsyncMock()
    mock_product_3.category = "drink"
    mock_product_3.name = "Coca-Cola"

    mock_product_4 = AsyncMock()
    mock_product_4.category = "cake"
    mock_product_4.name = "Чизкейк"

    mock_db.get_product_by_id.side_effect = [
        mock_product_1,
        mock_product_2,
        mock_product_3,
        mock_product_4,
    ]

    cart = Cart(user_id=123, redis=mock_redis, db=mock_db)

    items = await cart.get_cart_items()

    assert len(items) == 4

    mock_db.get_product_by_id.assert_any_call("1")
    mock_db.get_product_by_id.assert_any_call("2")
    mock_db.get_product_by_id.assert_any_call("3")
    mock_db.get_product_by_id.assert_any_call("4")

    assert items[0][0].category == "pizza"
    assert items[1][0].category == "snack"
    assert items[2][0].category == "cake"
    assert items[3][0].category == "drink"
