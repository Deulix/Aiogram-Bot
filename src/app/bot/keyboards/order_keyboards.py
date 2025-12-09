from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.database.sqlite_db import Order


async def orders(orders: list[Order]):
    keyboard = InlineKeyboardBuilder()
    mark = {"done": "✅", "pending": "⚠️", "cancelled": "❌"}
    for order in orders:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{mark[order.status]} Заказ #{order.id} от {order.created_at_local}",
                callback_data=f"order_{order.id}",
            )
        )
    keyboard.adjust(1)
    if not orders:
        keyboard.row(
            InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
        )
        keyboard.row(
            InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main menu"),
        )
    return keyboard.as_markup()


async def order_info(order: Order):
    keyboard = InlineKeyboardBuilder()
    if order.status == "pending":
        keyboard.row(
            InlineKeyboardButton(
                text="✅ Оплатить заказ", callback_data=f"payment_link_{order.id}"
            ),
        )
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="orders"),
    )
    keyboard.row(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(1).as_markup()


async def cancel_order(value=""):
    """
    Передаём value если нужны дополнительные поля

    "change_street" -> "↩️ Повторно ввести улицу"
    """
    keyboard = InlineKeyboardBuilder()
    if value == "change_street":
        keyboard.add(
            InlineKeyboardButton(
                text="↩️ Повторно ввести улицу", callback_data="change_street"
            ),
        )
    keyboard.add(
        InlineKeyboardButton(text="🛑 Отмена", callback_data="cart"),
    )
    return keyboard.adjust(1).as_markup()


async def order_confirm(order_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="✅ Оплатить заказ", callback_data=f"payment_link_{order_id}"
        ),
    )
    keyboard.row(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(2).as_markup()
