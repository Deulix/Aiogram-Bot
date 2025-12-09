from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from src.app.bot.keyboards import navigation_keyboards as nav_kb
from src.app.bot.services.cart_service import Cart
from src.app.database.models import Product
from src.app.database.sqlite_db import AsyncSQLiteDatabase

navigation_router = Router()


@navigation_router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSQLiteDatabase, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    if not (db_user := await db.get_user_by_id(message.from_user.id)):
        db_user = await db.add_user(
            user_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
    else:
        db_user = await db.update_user(tg_user)

    await message.answer(
        f"Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await nav_kb.main_menu(db_user),
    )


@navigation_router.callback_query(F.data == "main menu")
async def cmd_main_menu(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    await state.clear()
    tg_user = callback.from_user
    db_user = await db.update_user(tg_user)
    await callback.message.edit_text(
        f"Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await nav_kb.main_menu(db_user),
    )


@navigation_router.callback_query(F.data.in_(["catalog", "pizza", "snack", "drink"]))
async def cmd_category_menu(
    callback: CallbackQuery, db: AsyncSQLiteDatabase, redis: Redis
):
    category = callback.data
    products: list[Product] = await db.get_products_by_category(category)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    try:
        cart_amount = await cart.get_current_amount()
    except:  # noqa: E722
        cart_amount = None
    await callback.message.edit_text(
        (
            f"{'Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см\n\n' if category == 'pizza' else ''}{f'Общая стоимость корзины: {cart_amount:.2f} BYN\n\n' if cart_amount else ''}Для продолжения заказа выбери пункт меню:"
        ),
        reply_markup=(
            await nav_kb.catalog()
            if callback.data == "catalog"
            else await nav_kb.init_category_menu(products)
        ),
    )


@navigation_router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)


@navigation_router.callback_query(F.data.startswith("info_"))
async def product_info(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.answer(
        f"{product.category_rus.capitalize()} {product.name}\n{f'\n{product.description}\n' if product.description else ''}\
        {f'\nСостав: \n{product.ingredients}\n' if product.ingredients else ''}{f'\n{product.nutrition}' if product.nutrition else ''}",
        show_alert=True,
    )


@navigation_router.message(F.photo)
async def cmd_handle_photo(message: Message):
    await message.reply(message.photo[-1].file_id)
