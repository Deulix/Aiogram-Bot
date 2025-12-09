from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def tests():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="Проверить соединение с БД", callback_data="db_check"
        ),
        InlineKeyboardButton(text="Тестовый платёж", callback_data="test_payment_link"),
    )
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()
