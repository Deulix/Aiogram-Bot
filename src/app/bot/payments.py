from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment,
)
from src.app.config.settings import settings

payments_router = Router()

TEST_PAYMENT_KEY = settings.TEST_PAYMENT_KEY


@payments_router.callback_query(F.data == "payment")
async def payment(callback: CallbackQuery):
    pass
