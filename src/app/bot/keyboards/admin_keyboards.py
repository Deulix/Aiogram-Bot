from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.bot.core.callbacks import AdminCallback, MenuNavigationCallback
from src.app.database.sqlite_db import Product, User


async def admin():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✙ Добавить продукт", callback_data=AdminCallback.ADD_PRODUCTS()
        ),
        InlineKeyboardButton(
            text="🖍️ Изменить продукт", callback_data=AdminCallback.EDIT_PRODUCTS()
        ),
        InlineKeyboardButton(
            text="❌ Удалить продукт", callback_data=AdminCallback.DELETE_PRODUCTS()
        ),
        InlineKeyboardButton(
            text="🛑 Права суперпользователя 🛑",
            callback_data=AdminCallback.ADMIN_LIST(),
        ),
        InlineKeyboardButton(
            text="🛠️ Тесты", callback_data=AdminCallback.TEST_FUNCTIONS()
        ),
        InlineKeyboardButton(
            text="👤 В меню пользователя",
            callback_data=MenuNavigationCallback.MAIN_MENU(),
        ),
    )
    return keyboard.adjust(1).as_markup()


async def create_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="🍕 Пицца",
            callback_data=AdminCallback.add_product("pizza"),
        ),
        InlineKeyboardButton(
            text="🍟 Закуска",
            callback_data=AdminCallback.add_product("snack"),
        ),
        InlineKeyboardButton(
            text="🥤 Напиток",
            callback_data=AdminCallback.add_product("drink"),
        ),
        InlineKeyboardButton(
            text="🍰 Тортик",
            callback_data=AdminCallback.add_product("cake"),
        ),
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.ADMIN()
        ),
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
            text=f"🛑 Отмена {text_map[action]}",
            callback_data=MenuNavigationCallback.ADMIN(),
        ),
    )
    return keyboard.adjust().as_markup()


async def admin_list(admins: list[User], callback_user: User):
    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        text = f"{admin.id} - {admin.username} - {admin.first_name}{' (Вы)' if admin.id == callback_user.id else ''}"
        keyboard.add(
            InlineKeyboardButton(
                text=text, callback_data=AdminCallback.get_admin_info(admin.id)
            )
        )
    keyboard.add(
        InlineKeyboardButton(
            text="Добавить нового администратора",
            callback_data=AdminCallback.CREATE_ADMIN(),
        ),
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.ADMIN()
        ),
    )
    return keyboard.adjust(1).as_markup()


async def product_delete(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=AdminCallback.delete_product(product.id),
            )
        )
    keyboard.adjust(2)
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.ADMIN()
        )
    )
    return keyboard.as_markup()


async def confirm_deleting_product(product_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="❌ УДАЛИТЬ ❌",
            callback_data=AdminCallback.confirm_deleting_product(product_id),
        ),
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback.DELETE_PRODUCTS()
        ),
    )

    return keyboard.as_markup()


async def product_edit(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=AdminCallback.edit_product(product.id),
            )
        )
    keyboard.adjust(2)
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.ADMIN()
        )
    )
    return keyboard.as_markup()


async def product_edit_choose(product: Product):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=f"НАЗВАНИЕ ({product.name})",
            callback_data=AdminCallback.edit_field(product.id, "name"),
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА СТАНДАРТ ({product.price_small} BYN)",
            callback_data=AdminCallback.edit_field(product.id, "price_small"),
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА БОЛЬШОЙ(УЮ) ({f'{product.price_large} BYN' if product.price_large else '---'})",
            callback_data=AdminCallback.edit_field(product.id, "price_large"),
        ),
        InlineKeyboardButton(
            text=f"КАТЕГОРИЯ ({product.emoji} {product.category_rus})",
            callback_data=AdminCallback.edit_field(product.id, "category"),
        ),
        InlineKeyboardButton(
            text=f"ОПИСАНИЕ ({product.description or '---'})",
            callback_data=AdminCallback.edit_field(product.id, "description"),
        ),
        InlineKeyboardButton(
            text=f"ИНГРЕДИЕНТЫ ({product.ingredients or '---'})",
            callback_data=AdminCallback.edit_field(product.id, "ingredients"),
        ),
        InlineKeyboardButton(
            text=f"КБЖУ ({product.nutrition or '---'})",
            callback_data=AdminCallback.edit_field(product.id, "nutrition"),
        ),
    )

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback.EDIT_PRODUCTS()
        ),
        InlineKeyboardButton(
            text="⏪ Админпанель", callback_data=MenuNavigationCallback.ADMIN()
        ),
    )

    return keyboard.as_markup()


async def back_to_admin_list(can_dismiss, admin_id):
    keyboard = InlineKeyboardBuilder()
    if can_dismiss:
        keyboard.add(
            InlineKeyboardButton(
                text="❌ Лишить прав администратора",
                callback_data=AdminCallback.dismiss_admin(admin_id),
            )
        )
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCallback.ADMIN_LIST())
    )
    return keyboard.adjust(1).as_markup()
