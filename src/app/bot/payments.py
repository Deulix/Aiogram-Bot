import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from src.app.bot import keyboards as kb
from src.app.config.settings import settings
from src.app.database.models import OrderItem
from src.app.database.sqlite_db import AsyncSQLiteDatabase

payments_router = Router()


@payments_router.callback_query(F.data == "test_payment_link")
async def payment(message: Message):
    prices = [
        LabeledPrice(label="Пицца ТЕСТ", amount=50000),
        LabeledPrice(label="Доставка ТЕСТ", amount=2000),
    ]
    await message.bot.send_invoice(
        chat_id=message.from_user.id,
        title="Заказ пиццы ТЕСТ",
        description="Пицца c доставкой ТЕСТ",
        payload="order_123",
        provider_token=settings.TEST_PAYMENT_KEY,
        currency="byn",
        prices=prices,
    )


@payments_router.callback_query(F.data.startswith("payment_link_"))
async def payment(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    order_id = callback.data.split("_")[-1]
    order = await db.get_order_by_id(order_id)
    order_items = await db.get_order_items(order_id)
    prices = []

    for item in order_items:
        item: OrderItem
        product = await db.get_product_by_id(item.product_id)
        prices.append(
            LabeledPrice(
                label=f"{product.emoji} {product.name} {product.get_size_text(item.size)} -- {item.quantity} шт.",
                amount=item.price * item.quantity * 100,
            )
        )

    if order.status == "pending":
        invoice_message = await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Заказ #{order_id}",
            description="Доставка осуществляется бесплатно",
            payload=f"order_{order_id}",
            provider_token=settings.TEST_PAYMENT_KEY,
            currency="byn",
            prices=prices,
            need_name=True,
            need_phone_number=True,
        )
        asyncio.create_task(
            delete_invoice_with_delay(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=invoice_message.message_id,
                delay=600,
            )
        )
    elif order.status == "done":
        await callback.message.edit_text(
            f"✅ Заказ #{order.id} уже был оплачен. Ожидайте доставку.",
            reply_markup=await kb.main_menu(),
        )
    elif order.status == "cancelled":
        await callback.message.edit_text(
            f"❌ Заказ #{order.id} был отменён. Оплата невозможна.",
            reply_markup=await kb.main_menu(),
        )
    else:
        await callback.message.edit_text(
            "❌ Неизвестная ошибка. Попробуйте позже.",
            reply_markup=await kb.main_menu(),
        )


async def delete_invoice_with_delay(bot, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(e)


# # TEST
# @payments_router.pre_checkout_query()
# async def TEST_pre_checkout(pre_checkout_query: PreCheckoutQuery):
#     await pre_checkout_query.bot.answer_pre_checkout_query(
#         pre_checkout_query.id, ok=True
#     )


# # TEST
# @payments_router.message(F.successful_payment)
# async def TEST_successful_payment(message: Message):
#     await message.answer(
#         '(TEST) ✅ Оплата прошла успешно! Ваш заказ готовится.\nПосмотреть статус заказа можно в меню "Мои заказы"',
#         reply_markup=await kb.main_menu(),
#     )


@payments_router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery, db: AsyncSQLiteDatabase):
    order_id = pre_checkout_query.invoice_payload.split("_")[-1]
    order = await db.get_order_by_id(order_id)
    if order.status == "pending":
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=True
        )
    elif order.status == "done":
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=False, error_message="Этот заказ уже был оплачен."
        )
    elif order.status == "cancelled":
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=False, error_message="Этот заказ был отменён."
        )
    else:
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Неизвестная ошибка. Попробуйте позже.",
        )


@payments_router.message(F.successful_payment)
async def successful_payment(message: Message, db: AsyncSQLiteDatabase):
    payment = message.successful_payment
    order_id = payment.invoice_payload.split("_")[-1]
    await db.order_set_done(order_id)

    await message.answer(
        '✅ Оплата прошла успешно! Ваш заказ готовится.\nПосмотреть статус заказа можно в меню "Мои заказы"',
        reply_markup=await kb.main_menu(),
    )
