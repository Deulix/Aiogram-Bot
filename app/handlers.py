from typing import List

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

import app.keyboards as kb
from database.products import products

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, redis: Redis):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Выбери пункт меню:",
        reply_markup=kb.main,
    )


@router.callback_query(F.data == "main menu")
async def menu_main(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Привет, {callback.from_user.first_name}! Выбери пункт меню:",
        reply_markup=kb.main,
    )


@router.message(F.photo)
async def handle_photo(message: Message):
    await message.reply(message.photo[-1].file_id)


@router.message(F.text == "redis")
async def handle_redis(message: Message, redis: Redis):
    await redis.set("REDIS_STATUS", "OK")
    value = await redis.get("REDIS_STATUS")
    await message.reply(f"REDIS_STATUS: {value or "FAIL"}")


@router.message(F.text)
async def handle_answer(message: Message):
    await message.answer(
        f"Я пока умею только отвечать на меню. Выбери пункт ниже:",
        reply_markup=kb.main,
    )


@router.callback_query(F.data == "catalog")
async def menu_catalog(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Для продолжения заказа выбери пункт меню:",
        reply_markup=await kb.catalog(),
    )


@router.callback_query(F.data == "pizzas")
async def menu_pizzas(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Для продолжения заказа выбери пункт меню:",
        reply_markup=await kb.init_pizzas(products),
    )


@router.callback_query(F.data == "snacks")
async def menu_snacks(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Для продолжения заказа выбери пункт меню:",
        reply_markup=await kb.init_snacks(products),
    )


@router.callback_query(F.data == "drinks")
async def menu_drinks(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Для продолжения заказа выбери пункт меню:",
        reply_markup=await kb.init_drinks(products),
    )


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, redis: Redis):
    parts = callback.data.split("_")
    size = parts[-1]
    product = next(i for i in products if i.callback_name == parts[2])

    user_id = callback.from_user.id
    cart = f"cart:{user_id}"
    product_redis_key = f"{product.callback_name}_{size}"

    await redis.hincrby(cart, product_redis_key, 1)
    await redis.expire(cart, 3600 * 12)
    quantity = await redis.hget(cart, product_redis_key)

    if callback.data.startswith("add_pizza"):
        await callback.message.edit_text(
            f"Пицца {product.name} {('стандартная 25 см' if size == 'small' else 'большая 35 см')} ({quantity} шт) добавлена в корзину",
            reply_markup=await kb.init_pizzas(products),
        )
    elif callback.data.startswith("add_snack"):
        await callback.message.edit_text(
            f"Закуска {product.name} ({quantity} шт) добавлена в корзину",
            reply_markup=await kb.init_snacks(products),
        )
    else:
        await callback.message.edit_text(
            f"Напиток {product.name} {'1 литр' if size == '1' else '0,5 литра'} ({quantity} шт) добавлен в корзину",
            reply_markup=await kb.init_drinks(products),
        )


async def get_formatted_cart(user_id: int, redis: Redis) -> List:
    cart = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart)
    list_cart_items = []
    for item_key, quantity in dict_cart_items.items():
        callback_name = item_key.split("_")[0]
        size = item_key.split("_")[1]
        product = next(i for i in products if i.callback_name == callback_name)
        list_cart_items.append([product, size, quantity])

    return sorted(list_cart_items, key=lambda x: x[0].category)


@router.callback_query(F.data == "cart")
async def menu_cart(callback: CallbackQuery, redis: Redis):
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, {"вот твоя корзина:" if sorted_list_cart_items else "твоя корзина пуста"}",
        reply_markup=await kb.init_cart(
            sorted_list_cart_items,
        ),
    )


@router.callback_query(F.data.startswith("plus_"))
async def plus_quantity(callback: CallbackQuery, redis: Redis):
    cart = f"cart:{callback.from_user.id}"
    await redis.hincrby(cart, callback.data[5:], 1)
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("minus_"))
async def minus_quantity(callback: CallbackQuery, redis: Redis):
    cart = f"cart:{callback.from_user.id}"
    quantity = await redis.hget(cart, callback.data[6:])
    if int(quantity) > 1:
        await redis.hincrby(cart, callback.data[6:], -1)
    else:
        await redis.hdel(cart, callback.data[6:])

    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("del_"))
async def delete_from_cart(callback: CallbackQuery, redis: Redis):
    cart = f"cart:{callback.from_user.id}"
    await redis.hdel(cart, callback.data[4:])
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data == "erase_cart")
async def erase_cart(callback: CallbackQuery, redis: Redis):
    user_id = callback.from_user.id
    cart = f"cart:{user_id}"
    await redis.delete(cart)
    await callback.message.edit_text(
        f"Корзина была очищена.",
        reply_markup=kb.main,
    )


@router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)
