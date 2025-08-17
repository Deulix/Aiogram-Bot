from typing import List

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.products import Product

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Каталог", callback_data="catalog")],
        [
            InlineKeyboardButton(text="Корзина", callback_data="cart"),
            InlineKeyboardButton(text="Контакты", callback_data="contacts"),
        ],
    ]
)

settings = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="YouTube", url="https://www.youtube.com/")]
    ]
)


async def catalog():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🍕 Пиццы", callback_data="pizzas"))
    keyboard.add(InlineKeyboardButton(text="🍟 Закуски", callback_data="snacks"))
    keyboard.add(InlineKeyboardButton(text="🥤 Напитки", callback_data="drinks"))
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="main menu")
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
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text=f"Стандарт 25 см",
                    callback_data=f"add_pizza_{pizza.callback_name}_s",
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text=f"Большая 35 см",
                    callback_data=f"add_pizza_{pizza.callback_name}_l",
                )
            )
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog")
    )
    keyboard.add(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu")
    )
    return keyboard.adjust(3).as_markup()


async def init_snacks(products: List[Product]):
    keyboard = InlineKeyboardBuilder()
    for snack in products:
        if snack.category == "snack":
            keyboard.add(
                InlineKeyboardButton(
                    text=f"🍟 {snack.name}", callback_data=f"{snack.callback_name}_none"
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text=f"Добавить в корзину",
                    callback_data=f"add_snack_{snack.callback_name}_none",
                )
            )

    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog")
    )
    keyboard.add(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu")
    )
    return keyboard.adjust(2).as_markup()


async def init_drinks(products: List[Product]):
    keyboard = InlineKeyboardBuilder()
    for drink in products:
        if drink.category == "drink":
            keyboard.add(
                InlineKeyboardButton(
                    text=f"🥤 {drink.name}", callback_data=drink.callback_name
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text=f"+ 0,5 литра",
                    callback_data=f"add_drink_{drink.callback_name}_0,5",
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text=f"+ 1 литр",
                    callback_data=f"add_drink_{drink.callback_name}_1",
                )
            )
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog")
    )
    keyboard.add(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu")
    )
    return keyboard.adjust(3).as_markup()


async def init_cart(list_cart_items):
    keyboard = InlineKeyboardBuilder()
    for item in list_cart_items:
        match item[1]:
            case "s":
                size = "стандартная (25 см)"
            case "l":
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
            InlineKeyboardButton(text=f"+1", callback_data=f"plus_{item[0].callback_name}_{item[1]}"),
            InlineKeyboardButton(text=f"-1", callback_data=f"minus_{item[0].callback_name}_{item[1]}"),
            InlineKeyboardButton(text=f"❌", callback_data=f"del_{item[0].callback_name}_{item[1]}"),
        )
    keyboard.row(
        InlineKeyboardButton(text="🗑️ Очистить корзину 🗑️", callback_data="erase_cart")
    )
    keyboard.row(
        InlineKeyboardButton(text=" ⬅️ Назад в каталог  ", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
    )
    return keyboard.as_markup()
