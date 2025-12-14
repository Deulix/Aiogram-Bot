from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from redis.asyncio import Redis

from app.bot.core.callbacks import CartCallback, MenuNavigationCallback, ProductCallback
from src.app.bot.keyboards import nav_kb
from src.app.bot.services.cart_service import Cart, getall
from src.app.database.sqlite_db import AsyncSQLiteDatabase

cart_router = Router()


@cart_router.callback_query(ProductCallback.filter(action="add_to_cart"))
async def cmd_add_to_cart(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    (cart, product, size, products, quantity, product_key) = await getall(
        callback, callback_data, redis, db
    )
    await cart.increase_prod_count(product_key)

    cart_amount = await cart.get_current_price_amount()

    text = f"{product.category_rus.capitalize()} {product.name} {product.large_size_text if size == 'large' else product.small_size_text} ({quantity} шт) добавлен(а) в корзину"
    await callback.message.edit_text(
        f"{'Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см' if product.category == 'pizza' else ''}\n\n{text}\n\nОбщая стоимость корзины: {cart_amount:.2f} BYN\n\nДля продолжения заказа выбери пункт меню:",
        reply_markup=await nav_kb.init_category_menu(products),
    )


@cart_router.callback_query(MenuNavigationCallback.filter(action="cart"))
async def cmd_cart_menu(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.clear()

    user_id = callback.from_user.id
    cart = Cart(user_id, redis)

    cart_items = await cart.get_cart_items()
    cart_amount = await cart.get_current_price_amount()

    await callback.message.edit_text(
        ("КОРЗИНА:" if cart_items else "В корзине нет товаров."),
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(CartCallback.filter(action="increase"))
async def cmd_plus_quantity(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    (cart, product, size, _, _, product_key) = await getall(
        callback, callback_data, redis, db
    )
    await cart.increase_prod_count(product_key)
    await cart.add_price_amount(product.get_size_price(size))

    cart_amount = await cart.get_current_price_amount()
    cart_items = await cart.get_cart_items()

    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(CartCallback.filter(action="decrease"))
async def cmd_minus_quantity(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    (cart, product, size, _, quantity, product_key) = await getall(
        callback, callback_data, redis, db
    )
    if int(quantity) > 1:
        await cart.decrease_prod_count(product_key)
    else:
        await cart.delete_product(product_key)
    await cart.sub_price_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_price_amount()
    cart_items = await cart.get_cart_items()
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(CartCallback.filter(action="delete"))
async def cmd_delete_from_cart(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    (cart, product, size, _, quantity, product_key) = await getall(
        callback, callback_data, redis, db
    )
    await cart.delete_product(product_key)
    await cart.sub_price_amount(product.get_size_price(size) * quantity)
    cart_amount = await cart.get_current_price_amount()
    cart_items = await cart.get_cart_items()
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await nav_kb.init_cart(cart_items, cart_amount),
    )


@cart_router.callback_query(CartCallback.filter(action="erase_all"))
async def cmd_erase_cart(
    callback: CallbackQuery,
    redis: Redis,
    db: AsyncSQLiteDatabase,
):
    user_id = callback.from_user.id
    user = await db.get_user_by_id(user_id)
    cart = Cart(callback.from_user.id, redis=redis)

    await cart.clear()
    await callback.message.edit_text(
        "Корзина была очищена.",
        reply_markup=await nav_kb.main_menu(user),
    )
