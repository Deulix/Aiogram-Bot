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


async def init_pizzas(products: List[Product]):
    keyboard = InlineKeyboardBuilder()
    for pizza in products:
        if pizza.category == "pizza":
            keyboard.add(
                InlineKeyboardButton(
                    text=f"🍕 {pizza.name}",
                    callback_data=f"pizza_{pizza.callback_name}",
                ),
                InlineKeyboardButton(
                    text=f"Стандарт 25 см",
                    callback_data=f"add_pizza_{pizza.callback_name}_small",
                ),
                InlineKeyboardButton(
                    text=f"Большая 35 см",
                    callback_data=f"add_pizza_{pizza.callback_name}_large",
                ),
            )
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(3).as_markup()


async def init_category_menu(products: List[Product], category):
    keyboard = InlineKeyboardBuilder()
    if category == "пицца":
        for product in products:

            keyboard.add(
                InlineKeyboardButton(
                    text=f"🍕 {product.name}", callback_data=product.callback_name
                ),
                InlineKeyboardButton(
                    text=f"Стандарт {product.price_small} BYN",
                    callback_data="add_pizza_" + product.callback_name + "_small",
                ),
                InlineKeyboardButton(
                    text=f"Большая {product.price_large} BYN",
                    callback_data="add_pizza_" + product.callback_name + "_large",
                ),
            )
            keyboard.adjust(3)

    elif category == "закуска":
        pass

    else:
        pass

    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.as_markup()


async def init_cart(list_cart_items):
    keyboard = InlineKeyboardBuilder()
    if list_cart_items:
        for item in list_cart_items:
            match item[1]:
                case "small":
                    size = "стандартная (25 см)"
                case "large":
                    size = "большая (35 см)"
                case "1":
                    size = "1 литр"
                case "0,5":
                    size = "0,5 литра"
                case _:
                    size = ""

            keyboard.row(
                InlineKeyboardButton(
                    text=f"{item[0].name} {size} - {item[2]} шт", callback_data="1"
                )
            )
            keyboard.row(
                InlineKeyboardButton(
                    text=f"+1", callback_data=f"plus_{item[0].callback_name}_{item[1]}"
                ),
                InlineKeyboardButton(
                    text=f"-1",
                    callback_data=(
                        f"minus_{item[0].callback_name}_{item[1]}"
                        if int(item[2]) > 1 or len(list_cart_items) > 1
                        else "erase_cart"
                    ),
                ),
                InlineKeyboardButton(
                    text=f"❌",
                    callback_data=(
                        f"del_{item[0].callback_name}_{item[1]}"
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
