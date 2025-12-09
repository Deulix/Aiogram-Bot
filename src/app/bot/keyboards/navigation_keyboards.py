from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.database.sqlite_db import Product, User


async def main_menu(user: User):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
        InlineKeyboardButton(text="👤 Мои заказы", callback_data="orders"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts"),
    )
    if user.is_admin:
        keyboard.add(InlineKeyboardButton(text="👺 АДМИНПАНЕЛЬ", callback_data="admin"))
    return keyboard.adjust(1, 1, 2, 1).as_markup()


async def catalog():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пиццы", callback_data="pizza"),
        InlineKeyboardButton(text="🍟 Закуски", callback_data="snack"),
        InlineKeyboardButton(text="🥤 Напитки", callback_data="drink"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(1, 2, 1).as_markup()


async def init_category_menu(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        name_btn = InlineKeyboardButton(
            text=f"{product.emoji} {product.name}",
            callback_data=f"info_{product.id}",
        )
        small_size_btn = InlineKeyboardButton(
            text=f"{product.small_size_text} {product.price_small} BYN",
            callback_data=f"add_{product.id}_small",
        )
        large_size_btn = InlineKeyboardButton(
            text=f"{product.large_size_text} {product.price_large} BYN",
            callback_data=f"add_{product.id}_large",
        )

        if not product.has_only_small_size:
            keyboard.row(name_btn, small_size_btn, large_size_btn)
        else:
            keyboard.row(name_btn, small_size_btn)

    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.as_markup()


async def init_cart(cart_items: tuple, cart_amount: float):
    keyboard = InlineKeyboardBuilder()

    if cart_items and cart_amount:
        for product, size, quantity in cart_items:
            product: Product
            size: str
            quantity: str
            price_by_count = product.get_size_price(size) * int(quantity)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{product.emoji} {product.name} {product.get_size_text(size)} - {quantity} шт -- {price_by_count:.2f} BYN",
                    callback_data="1",
                )
            )
            keyboard.row(
                InlineKeyboardButton(
                    text="+1",
                    callback_data=f"plus_{product.id}_{size}",
                ),
                InlineKeyboardButton(
                    text="-1",
                    callback_data=(
                        f"minus_{product.id}_{size}"
                        if int(quantity) > 1 or len(cart_items) > 1
                        else "erase_cart"
                    ),
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=(
                        f"del_{product.id}_{size}"
                        if len(cart_items) > 1
                        else "erase_cart"
                    ),
                ),
            )
        keyboard.row(
            InlineKeyboardButton(
                text=f"✅ Оформить заказ ({float(cart_amount):.2f} BYN)",
                callback_data="make_order",
            )
        )
        keyboard.row(
            InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="erase_cart")
        )
        keyboard.row(
            InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
            InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
        )
    else:
        keyboard.add(
            InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
            InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
        )
        keyboard.adjust(1)
    return keyboard.as_markup()
