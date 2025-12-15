import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from redis import Redis

from src.app.bot.core.callbacks import (
    CartCallback,
    MenuNavigationCallback,
    OrderCallback,
)
from src.app.bot.keyboards import ord_kb
from src.app.bot.services.cart_service import Cart
from src.app.bot.utils.validators import validate_street_api
from src.app.database.models import Product
from src.app.database.sqlite_db import AsyncSQLiteDatabase

order_router = Router()


@order_router.callback_query(MenuNavigationCallback.filter(F.action == "orders"))
async def orders(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    user_id = callback.from_user.id
    orders = await db.get_orders_by_user(user_id)
    await callback.message.edit_text(
        "СПИСОК ЗАКАЗОВ:" if orders else "Список заказов пуст.",
        reply_markup=await ord_kb.orders(orders),
    )


@order_router.callback_query(OrderCallback.filter(F.action == "order_details"))
async def order_details(
    callback: CallbackQuery, callback_data: OrderCallback, db: AsyncSQLiteDatabase
):
    order_id = callback_data.order_id
    order = await db.get_order_by_id(order_id)
    order_items = await db.get_order_items(order.id)
    order_items_text = []
    for order_item in order_items:
        product = await db.get_product_by_id(order_item.product_id)
        emoji = product.emoji
        name = product.name
        size = order_item.size
        size_text = product.get_size_text(size)
        quantity = order_item.quantity
        price = order_item.price
        order_items_text.append(
            f"{emoji[0]} {name} {size_text} - {quantity} шт. -- {(price * quantity):.2f} BYN\n"
        )
    order_items_normalized = "".join(order_items_text)
    mark = {
        "done": "✅ Оплачен",
        "pending": "⚠️ Ожидает оплаты",
        "cancelled": "❌ Отменён",
    }
    await callback.message.edit_text(
        f"{mark[order.status]}\nЗАКАЗ #{order.id} от {order.created_at_local}:\n\n{order_items_normalized}\nСТОИМОСТЬ: {order.amount:.2f} BYN\n\nИмя: {order.client_name}\nТелефон: +375{order.phone}\nАдрес: {order.address}\n"
        + ((f"Доп инфо: {order.additional_info}") if order.additional_info else ""),
        reply_markup=await ord_kb.order_info(order),
    )


class OrderStates(StatesGroup):
    client = State()
    phone = State()
    street = State()
    house = State()
    apartment = State()
    floor = State()
    enterance = State()
    additional_info = State()


@order_router.callback_query(CartCallback.filter(F.action == "make_order"))
async def order_start_creation(
    callback: CallbackQuery, callback_data: CartCallback, state: FSMContext
):
    await callback.message.edit_text(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите ваше имя:",
        reply_markup=await ord_kb.cancel_order(),
    )
    await state.set_state(OrderStates.client)


@order_router.message(OrderStates.client)
async def client(message: Message, state: FSMContext):
    pattern = r"^[а-яА-Яa-zA-ZёЁ\'\-\.\s]+$"
    client_name = " ".join(word.capitalize() for word in message.text.split())
    if not re.match(pattern, client_name):
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Допустимые символы для имени: буквы(Аа-Яя, Aa-Zz), апостраф('), точка(.), дефис(-) и пробел.\n\nВведите ваше имя:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return
    elif not 1 < len(client_name) < 50:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Имя должно быть длиной от 2 до 50 символов.\n\nВведите ваше имя:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return
    else:
        await state.update_data(client_name=client_name)

        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите ваш номер телефона\nПример: 29 1234567",
            reply_markup=await ord_kb.cancel_order(),
        )
        await state.set_state(OrderStates.phone)


@order_router.callback_query(OrderCallback.filter(F.action == "edit_street"))
async def edit_street(
    callback: CallbackQuery, callback_data: OrderCallback, state: FSMContext
):
    await state.set_state(OrderStates.street)
    await callback.message.edit_text(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите улицу:",
        reply_markup=await ord_kb.cancel_order(),
    )


@order_router.message(OrderStates.phone)
async def phone(
    message: Message,
    state: FSMContext,
):
    client_phone = message.text
    operators_codes = ("25", "29", "33", "44")
    operator_code_verified = client_phone.startswith(operators_codes)
    if len(client_phone) != 9 or not client_phone.isdecimal():
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер телефона должен быть в формате XX1234567, где XX ваш код оператора (для Беларуси {', '.join(operators_codes)}).\n✅ Пример: 291234567\n\nВведите ваш номер телефона:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return
    elif not operator_code_verified:
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Неверный код оператора.\nАктуальные коды: {', '.join(operators_codes)}\n✅ Пример: 291234567\n\nВведите ваш номер телефона:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return

    else:
        await state.update_data(phone=client_phone)

        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите улицу:",
            reply_markup=await ord_kb.cancel_order(),
        )
        await state.set_state(OrderStates.street)


@order_router.message(OrderStates.street)
async def street(message: Message, state: FSMContext):
    street = message.text
    if not 2 < len(street) < 50:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Название улицы должно быть от 3 до 50 символов.\n\nВведите улицу:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return

    elif street.isnumeric():
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Название улицы не должно содержать только цифры.\n\nВведите улицу:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return

    nums_count = sum(1 for с in street if с.isdigit())
    if nums_count > 2:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! В названии улицы может быть не больше 2х цифр.\n\nВведите улицу:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return

    street_validated, found = await validate_street_api(street)
    if not found:
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n⚠️ Улица не найдена в базе, для уточнения вам перезвонит оператор либо нажмите кнопку ниже для повторного ввода.\nВыбрано: {street_validated}.\n\nВведите номер дома:",
            reply_markup=await ord_kb.cancel_order("change_street"),
        )
    else:
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n✅ Улица найдена в базе.\nВыбрано: {street_validated}.\n\nВведите номер дома:",
            reply_markup=await ord_kb.cancel_order("change_street"),
        )
    await state.update_data(street=street_validated)

    await state.set_state(OrderStates.house)


@order_router.message(OrderStates.house)
async def house(message: Message, state: FSMContext):
    house = message.text
    if not house.isdecimal():
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер дома должен быть числовым значением.\nВведите номер дома:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return

    elif int(house) not in range(1, 300):
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер дома должен быть от 1 до 300.\nВведите номер дома:",
            reply_markup=await ord_kb.cancel_order(),
        )
        return
    else:
        await state.update_data(house=house)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер квартиры или /skip для пропуска:",
        reply_markup=await ord_kb.cancel_order(),
    )
    await state.set_state(OrderStates.apartment)


@order_router.message(OrderStates.apartment)
async def apartment(message: Message, state: FSMContext):
    apartment = message.text
    if apartment == "/skip":
        await state.update_data(apartment=None)
    else:
        if not apartment.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер квартиры должен быть от 1 до 1000.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return

        elif int(apartment) not in range(1, 1000):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер квартиры должен быть от 1 до 1000.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return
        else:
            await state.update_data(apartment=apartment)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите этаж или /skip для пропуска:",
        reply_markup=await ord_kb.cancel_order(),
    )
    await state.set_state(OrderStates.floor)


@order_router.message(OrderStates.floor)
async def floor(message: Message, state: FSMContext):
    floor = message.text
    if floor == "/skip":
        await state.update_data(floor=None)
    else:
        if not floor.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Этаж должен быть числовым значением.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return
        elif int(floor) not in range(1, 50):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Этаж должен быть от 1 до 50.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return
        else:
            await state.update_data(floor=floor)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер подъезда или /skip для пропуска",
        reply_markup=await ord_kb.cancel_order(),
    )
    await state.set_state(OrderStates.enterance)


@order_router.message(OrderStates.enterance)
async def enterance(message: Message, state: FSMContext):
    enterance = message.text
    if enterance == "/skip":
        await state.update_data(enterance=None)
    else:
        if not enterance.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер подъезда должен быть числовым значением.\nВведите номер подъезда или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return
        elif int(enterance) not in range(1, 30):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер подъезда должен быть от 1 до 30.\nВведите номер подъезда или /skip для пропуска:",
                reply_markup=await ord_kb.cancel_order(),
            )
            return

        await state.update_data(enterance=enterance)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите дополнительную информацию или /skip для пропуска",
        reply_markup=await ord_kb.cancel_order(),
    )
    await state.set_state(OrderStates.additional_info)


@order_router.message(OrderStates.additional_info)
async def additional_info(
    message: Message, state: FSMContext, redis: Redis, db: AsyncSQLiteDatabase
):
    await state.update_data(
        additional_info=message.text if message.text != "/skip" else None
    )
    data = await state.get_data()
    client_name = data["client_name"]
    phone = data["phone"]
    street = data["street"]
    house = data["house"]
    apartment = data["apartment"]
    floor = data["floor"]
    enterance = data["enterance"]
    additional_info = data["additional_info"]

    cart = Cart(message.from_user.id, redis, db)
    cart_items = await cart.get_cart_items()
    amount = await cart.get_current_price_amount()

    cart_text = []
    for item in cart_items:
        product, size, quantity = item
        product: Product
        price = product.get_size_price(size)
        cart_text.append(
            f"{product.emoji} {product.name} {product.get_size_text(size)} - {quantity} шт. -- {(price * quantity):.2f} BYN\n"
        )
        cart_text_normalized = "".join(cart_text)

    client_text = f"Имя: {client_name}, телефон: +375{phone}"
    address_parts = [
        f"{street}",
        f"дом {house}",
        f"квартира {apartment}" if apartment else None,
        f"этаж {floor}" if floor else None,
        f"подъезд {enterance}" if enterance else None,
    ]
    address_text = ", ".join(part for part in address_parts if part)
    order = await db.add_order(
        message.from_user.id,
        cart_items,
        client_name,
        phone,
        address_text,
        additional_info,
    )
    message_parts = [
        f"⚠️ Сформирован заказ #{order.id}. Проверьте перед оплатой!\n",
        cart_text_normalized,
        f"СТОИМОСТЬ {amount:.2f} BYN\n",
        client_text,
        f"Адрес: {address_text}",
        f"\nДоп инфо: {additional_info}" if additional_info else "",
    ]
    await message.answer(
        "\n".join(message_parts),
        reply_markup=await ord_kb.order_confirm(order.id),
    )
    await state.clear()
    await cart.clear()
