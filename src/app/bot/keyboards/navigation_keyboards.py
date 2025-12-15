from typing import Literal

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.bot.core.callbacks import (
    CartCallback,
    CategoryNavigationCallback,
    MenuNavigationCallback,
    ProductCallback,
)
from src.app.database.sqlite_db import Product, User


async def main_menu(user: User):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="📋 Каталог", callback_data=MenuNavigationCallback.CATALOG()
        ),
        InlineKeyboardButton(
            text="👤 Мои заказы", callback_data=MenuNavigationCallback.ORDERS()
        ),
        InlineKeyboardButton(
            text="🛒 Корзина", callback_data=MenuNavigationCallback.CART()
        ),
        InlineKeyboardButton(
            text="📞 Контакты", callback_data=MenuNavigationCallback.CONTACTS()
        ),
    )
    keyboard.adjust(1, 1, 2, 1)
    if user.is_admin:
        keyboard.row(
            InlineKeyboardButton(
                text="👺 АДМИНПАНЕЛЬ", callback_data=MenuNavigationCallback.ADMIN()
            )
        )
    return keyboard.as_markup()


async def catalog():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="🍕 Пиццы", callback_data=CategoryNavigationCallback.PIZZAS()
        ),
        InlineKeyboardButton(
            text="🍟 Закуски", callback_data=CategoryNavigationCallback.SNACKS()
        ),
        InlineKeyboardButton(
            text="🥤 Напитки", callback_data=CategoryNavigationCallback.DRINKS()
        ),
        InlineKeyboardButton(
            text="⏪ Главное меню", callback_data=MenuNavigationCallback.MAIN_MENU()
        ),
    )
    return keyboard.adjust(1, 2, 1).as_markup()


async def init_category_menu(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        name_btn = InlineKeyboardButton(
            text=f"{product.emoji} {product.name}",
            callback_data=ProductCallback.view_product_details(product.id),
        )
        small_size_btn = InlineKeyboardButton(
            text=f"{product.small_size_text} {product.price_small} BYN",
            callback_data=ProductCallback.add_small_size(product.id),
        )
        large_size_btn = InlineKeyboardButton(
            text=f"{product.large_size_text} {product.price_large} BYN",
            callback_data=ProductCallback.add_large_size(product.id),
        )

        if not product.has_only_small_size:
            keyboard.row(name_btn, small_size_btn, large_size_btn)
        else:
            keyboard.row(name_btn, small_size_btn)

    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.CATALOG()
        ),
        InlineKeyboardButton(
            text="⏪ Главное меню", callback_data=MenuNavigationCallback.MAIN_MENU()
        ),
    )
    return keyboard.as_markup()


async def init_cart(cart_items: tuple, cart_amount: float):
    keyboard = InlineKeyboardBuilder()

    if cart_items and cart_amount:
        for product, product_size, quantity in cart_items:
            product: Product
            product_size: Literal["small", "large"]
            quantity: str
            price_by_count = product.get_size_price(product_size) * int(quantity)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{product.emoji} {product.name} {product.get_size_text(product_size)} - {quantity} шт -- {price_by_count:.2f} BYN",
                    callback_data=ProductCallback.view_product_details(product.id),
                )
            )
            keyboard.row(
                InlineKeyboardButton(
                    text="+1",
                    callback_data=CartCallback.increase(product.id, product_size),
                ),
                InlineKeyboardButton(
                    text="-1",
                    callback_data=(
                        CartCallback.decrease(product.id, product_size)
                        if int(quantity) > 1 or len(cart_items) > 1
                        else CartCallback.ERASE_ALL()
                    ),
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=(
                        CartCallback.delete(product.id, product_size)
                        if len(cart_items) > 1
                        else CartCallback.ERASE_ALL()
                    ),
                ),
            )
        keyboard.row(
            InlineKeyboardButton(
                text=f"✅ Оформить заказ ({float(cart_amount):.2f} BYN)",
                callback_data=CartCallback.MAKE_ORDER(),
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text="🗑️ Очистить корзину", callback_data=CartCallback.ERASE_ALL()
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text="📋 Каталог", callback_data=MenuNavigationCallback.CATALOG()
            ),
            InlineKeyboardButton(
                text="⏪ Главное меню ",
                callback_data=MenuNavigationCallback.MAIN_MENU(),
            ),
        )
    else:
        keyboard.add(
            InlineKeyboardButton(
                text="📋 Каталог", callback_data=MenuNavigationCallback.CATALOG()
            ),
            InlineKeyboardButton(
                text="⏪ Главное меню ",
                callback_data=MenuNavigationCallback.MAIN_MENU(),
            ),
        )
        keyboard.adjust(1)
    return keyboard.as_markup()
