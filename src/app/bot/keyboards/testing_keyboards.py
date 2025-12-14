from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.app.bot.core.callbacks import AdminCallback, MenuNavigationCallback


async def tests():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="Проверить соединение с БД", callback_data=AdminCallback.CHECK_DB
        ),
        InlineKeyboardButton(
            text="Тестовый платёж", callback_data=AdminCallback.TEST_PAYMENT
        ),
    )
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuNavigationCallback.ADMIN
        ),
    )
    return keyboard.adjust(1).as_markup()
