from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.database.sqlite_db import Product, User


async def admin():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="✙ Добавить продукт", callback_data="product_create"),
        InlineKeyboardButton(text="🖍️ Изменить продукт", callback_data="product_edit"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(
            text="🛑 Права суперпользователя 🛑", callback_data="admin_list"
        ),
        InlineKeyboardButton(text="🛠️ Тесты", callback_data="tests"),
        InlineKeyboardButton(text="👤 В меню пользователя", callback_data="main menu"),
    )
    return keyboard.adjust(1).as_markup()


async def create_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пицца", callback_data="product_create_pizza"),
        InlineKeyboardButton(text="🍟 Закуска", callback_data="product_create_snack"),
        InlineKeyboardButton(text="🥤 Напиток", callback_data="product_create_drink"),
        InlineKeyboardButton(text="🍰 Тортик", callback_data="product_create_cake"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()


async def cancel_admin_action(action=""):
    """
    вызов без аргумента -> "Отмена"

    "creation" -> "Отмена создания"

    "addition" -> "Отмена добавления"

    "edit" -> "Отмена изменения"

    """
    keyboard = InlineKeyboardBuilder()
    text_map = {
        "": "",
        "creation": "создания",
        "addition": "добавления",
        "edit": "изменения",
    }
    keyboard.add(
        InlineKeyboardButton(
            text=f"🛑 Отмена {text_map[action]}", callback_data="admin"
        ),
    )
    return keyboard.adjust().as_markup()


async def admin_list(admins: list[User], callback_user: User):
    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        text = f"{admin.id} - {admin.username} - {admin.first_name}{' (Вы)' if admin.id == callback_user.id else ''}"
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"admin_id_{admin.id}")
        )
    keyboard.add(
        InlineKeyboardButton(
            text="Добавить нового администратора", callback_data="admin_create"
        ),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()


async def product_delete(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=f"product_delete_{product.id}",
            )
        )
    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"))
    return keyboard.as_markup()


async def product_confirmed_delete(id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="❌ УДАЛИТЬ ❌",
            callback_data=f"product_confirmed_delete_{id}",
        ),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="product_delete"),
    )

    return keyboard.as_markup()


async def product_edit(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=f"product_edit_{product.id}",
            )
        )
    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"))
    return keyboard.as_markup()


async def product_edit_choose(product: Product):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=f"НАЗВАНИЕ ({product.name})",
            callback_data=f"product_parameter_edit_name_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА СТАНДАРТ ({product.price_small} BYN)",
            callback_data=f"product_parameter_edit_price-small_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА БОЛЬШОЙ(УЮ) ({f'{product.price_large} BYN' if product.price_large else '---'})",
            callback_data=f"product_parameter_edit_price-large_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"КАТЕГОРИЯ ({product.emoji} {product.category_rus})",
            callback_data=f"product_parameter_edit_category_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ОПИСАНИЕ ({product.description or '---'})",
            callback_data=f"product_parameter_edit_description_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ИНГРЕДИЕНТЫ ({product.ingredients or '---'})",
            callback_data=f"product_parameter_edit_ingredients_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"КБЖУ ({product.nutrition or '---'})",
            callback_data=f"product_parameter_edit_nutrition_{product.id}",
        ),
    )

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="product_edit"),
        InlineKeyboardButton(text="⏪ Админпанель", callback_data="admin"),
    )

    return keyboard.as_markup()


async def back_to_admin_list(can_dismiss, admin_id):
    keyboard = InlineKeyboardBuilder()
    if can_dismiss:
        keyboard.add(
            InlineKeyboardButton(
                text="❌ Лишить прав администратора",
                callback_data=f"dismiss_admin_{admin_id}",
            )
        )
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_list"))
    return keyboard.adjust(1).as_markup()
