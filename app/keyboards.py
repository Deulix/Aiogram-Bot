from typing import List

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.sqlite_db import Product


async def main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="Каталог", callback_data="catalog"),
        InlineKeyboardButton(text="Корзина", callback_data="cart"),
        InlineKeyboardButton(text="Контакты", callback_data="contacts"),
    )
    return keyboard.adjust(1, 2).as_markup()


async def catalog():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пиццы", callback_data="pizzas"),
        InlineKeyboardButton(text="🍟 Закуски", callback_data="snacks"),
        InlineKeyboardButton(text="🥤 Напитки", callback_data="drinks"),
        InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(1, 2, 1).as_markup()


async def init_category_menu(products: List[Product], category):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        name_btn = InlineKeyboardButton(
            text=f"{product.emoji} {product.name}",
            callback_data=f"info_{product.callback_name}",
        )
        small_size_btn = InlineKeyboardButton(
            text=f"{product.small_size_text} {product.price_small} BYN",
            callback_data=f"add_{category}_{product.callback_name}_small",
        )
        large_size_btn = InlineKeyboardButton(
            text=f"{product.large_size_text} {product.price_large} BYN",
            callback_data=f"add_{category}_{product.callback_name}_large",
        )

        if not product.has_only_one_size():
            keyboard.row(name_btn, small_size_btn, large_size_btn)
        else:
            keyboard.row(name_btn, small_size_btn)

    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.as_markup()


async def init_cart(list_cart_items: List):
    keyboard = InlineKeyboardBuilder()

    if list_cart_items:
        for product, size, quantity in list_cart_items:
            product: Product
            size: str
            quantity: str

            keyboard.row(
                InlineKeyboardButton(
                    text=f"{product.emoji} {product.name} {product.get_current_size_text(size)} - {quantity} шт -- {product.get_current_price(size) * int(quantity)} BYN",
                    callback_data="1",
                )
            )
            keyboard.row(
                InlineKeyboardButton(
                    text=f"+1",
                    callback_data=f"plus_{product.category}_{product.callback_name}_{size}",
                ),
                InlineKeyboardButton(
                    text=f"-1",
                    callback_data=(
                        f"minus_{product.category}_{product.callback_name}_{size}"
                        if int(quantity) > 1 or len(list_cart_items) > 1
                        else "erase_cart"
                    ),
                ),
                InlineKeyboardButton(
                    text=f"❌",
                    callback_data=(
                        f"del_{product.category}_{product.callback_name}_{size}"
                        if len(list_cart_items) > 1
                        else "erase_cart"
                    ),
                ),
            )
        keyboard.row(
            InlineKeyboardButton(
                text="🗑️ Очистить корзину 🗑️", callback_data="erase_cart"
            )
        )
        keyboard.row(InlineKeyboardButton(text=f"", callback_data="cart_amount"))
    keyboard.row(
        InlineKeyboardButton(text=" ⬅️ Назад в каталог  ", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
    )
    return keyboard.as_markup()


#### Админка ####


async def admin():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="✙ Добавить продукт", callback_data="product_create"),
        InlineKeyboardButton(text="🖍️ Изменить продукт", callback_data="product_edit"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(
            text="🛑 Права суперпользователя 🛑", callback_data="set_admin_rights"
        ),
        InlineKeyboardButton(text="👤 В меню пользователя", callback_data="main menu"),
    )
    return keyboard.adjust(1).as_markup()


async def create_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пицца", callback_data="product_create_pizza"),
        InlineKeyboardButton(text="🍟 Закуска", callback_data="product_create_snack"),
        InlineKeyboardButton(text="🥤 Напиток", callback_data="product_create_drink"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()


async def delete_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
    )
    return keyboard.adjust(1).as_markup()


async def cancel_creation():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🛑 Отмена создания", callback_data="admin"),
    )
    return keyboard.adjust().as_markup()
