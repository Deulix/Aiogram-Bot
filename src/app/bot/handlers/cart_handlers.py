from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from redis.asyncio import Redis

from src.app.bot.keyboards import nav_kb
from src.app.bot.services.cart_service import Cart, get_cart_items, getall
from src.app.database.models import Product
from src.app.database.sqlite_db import AsyncSQLiteDatabase

cart_router = Router()


@cart_router.callback_query(F.data.startswith("add_"))
async def cmd_add_to_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )

    await cart.increase_prod_count(full_callback)
    quantity += 1
    products: list[Product] = await db.get_products_by_category(product.category)
    text = f"{product.category_rus.capitalize()} {product.name} {product.large_size_text if size == 'large' else product.small_size_text} ({quantity} шт) добавлен(а) в корзину"
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    await callback.message.edit_text(
        f"{'Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см' if product.category == 'pizza' else ''}\n\n{text}\n\nОбщая стоимость корзины: {cart_amount:.2f} BYN\n\nДля продолжения заказа выбери пункт меню:",
        reply_markup=await nav_kb.init_category_menu(products),
    )


@cart_router.callback_query(F.data == "cart")
async def cmd_cart_menu(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.clear()
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id, redis, db)
    cart = Cart(user_id, redis)
    try:
        cart_amount = await cart.get_current_amount()
    except TypeError:
        cart_amount = None
    await callback.message.edit_text(
        ("КОРЗИНА:" if cart_items else "В корзине нет товаров."),
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(F.data.startswith("plus_"))
async def cmd_plus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, _) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.increase_prod_count(full_callback)
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(F.data.startswith("minus_"))
async def cmd_minus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    if int(quantity) > 1:
        await cart.decrease_prod_count(full_callback)
    else:
        await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(F.data.startswith("del_"))
async def cmd_delete_from_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size) * quantity)
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(F.data == "erase_cart")
async def cmd_erase_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    user_id = callback.from_user.id
    user = await db.get_user_by_id(user_id)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        "Корзина была очищена.",
        reply_markup=await nav_kb.main_menu(user),
    )
    await cart.clear()
