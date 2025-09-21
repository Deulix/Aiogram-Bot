import logging
from typing import List

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from transliterate import translit

import app.keyboards as kb
from database.sqlite_db import AsyncSQLiteDatabase, Product

router = Router()

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSQLiteDatabase, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    await message.answer(
        f"Привет, {user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(),
    )


@router.callback_query(F.data == "main menu")
async def menu_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f"Привет, {callback.from_user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(),
    )


@router.message(F.photo)
async def handle_photo(message: Message):
    await message.reply(message.photo[-1].file_id)


@router.callback_query(F.data == "catalog")
async def menu_catalog(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Для продолжения заказа выбери пункт меню:",
        reply_markup=await kb.catalog(),
    )


@router.callback_query(F.data.in_(["pizzas", "snacks", "drinks"]))
async def category_menu(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    category = callback.data[:-1]
    products = await db.get_products_by_category(category)
    if category == "pizza":
        await callback.message.edit_text(
            f"Для продолжения заказа выбери пункт меню ниже.\n\nИнформация о размерах пицц:\nСтандартная: 500-600 грамм, 25 сантиметров\nБольшая: 800-900 грамм, 35 сантиметров",
            reply_markup=await kb.init_category_menu(products, category),
        )
    else:
        await callback.message.edit_text(
            f"Для продолжения заказа выбери пункт меню:",
            reply_markup=await kb.init_category_menu(products, category),
        )


class Cart:
    def __init__(self, user_id: int, redis: Redis):
        self.user_id = user_id
        self.redis = redis
        self.cart_key = f"cart:{user_id}"
        self.amount_key = f"cart_amount:{user_id}"

    async def get_current_amount(self):
        current_amount = await self.redis.get(self.amount_key)
        return current_amount

    async def add(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, price)
        await self.redis.expire(self.amount_key, 3600 * 12)

    async def sub(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, -price)
        await self.redis.expire(self.amount_key, 3600 * 12)

    async def delete(self, product: Product, size):
        amount = await self.redis.hget(
            self.cart_key, f"{product.category}_{product.callback_name}_{size}"
        )
        await self.redis.incrbyfloat(
            self.amount_key, -product.get_current_price(size) * int(amount)
        )
        await self.redis.expire(self.amount_key, 3600 * 12)

    async def clear(self):
        await self.redis.delete(self.cart_key)
        await self.redis.delete(self.amount_key)


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    _, category, callback_name, size = callback.data.split("_")

    user_id = callback.from_user.id
    cart_key = f"cart:{user_id}"
    product_redis_key = f"{category}_{callback_name}_{size}"

    await redis.hincrby(cart_key, product_redis_key, 1)
    await redis.expire(cart_key, 3600 * 12)
    quantity = await redis.hget(cart_key, product_redis_key)
    products = await db.get_products_by_category(category)
    product = await db.get_product_by_callback_name(callback_name)
    reply_markup = kb.init_category_menu(products, category)
    if category == "pizza":
        text = f"Пицца {product.name} {("большая 35 см" if size == "large" else "стандартная 25 см")} ({quantity} шт) добавлена в корзину\n\nИнформация о размерах пицц:\nСтандартная: 500-600 грамм, 25 сантиметров\nБольшая: 800-900 грамм, 35 сантиметров"
    elif category == "snack":
        text = f"Закуска {product.name} {product.get_current_size_text(size)} ({quantity} шт) добавлена в корзину"
    elif category == "drink":
        text = f"Напиток {product.name} {"1 литр" if size == "large" else "0,5 литра"} ({quantity} шт) добавлен в корзину"
    logger.info(
        f"***User {user_id} added {product.name} to cart with size {size} and quantity {quantity}***"
    )
    cart = Cart(user_id=user_id, redis=redis)
    await cart.add(product.get_current_price(size))
    cart_text = f"\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN"
    await callback.message.edit_text(text + cart_text, reply_markup=await reply_markup)


async def get_formatted_cart(
    user_id: int, redis: Redis, db: AsyncSQLiteDatabase
) -> List:
    cart_key = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart_key)
    list_cart_items = []
    for item_key, quantity in dict_cart_items.items():
        callback_name = item_key.split("_")[1]
        size = item_key.split("_")[-1]
        product = await db.get_product_by_callback_name(callback_name)
        list_cart_items.append([product, size, quantity])

    return list_cart_items


@router.callback_query(F.data == "cart")
async def menu_cart(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis, db)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, {f"вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN" if sorted_list_cart_items else "твоя корзина пуста"}",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


async def getall(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[Product, str, str, float, str, Cart, float]:
    callback_name = callback.data.split("_")[-2]
    product = await db.get_product_by_callback_name(callback_name)
    size = callback.data.split("_")[-1]
    current_price = product.get_current_price(size)
    cart_key = f"cart:{callback.from_user.id}"
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    
    return (
        product,
        callback_name,
        size,
        current_price,
        cart_key,
        cart,
    )


@router.callback_query(F.data.startswith("plus_"))
async def plus_quantity(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    (
        product,
        callback_name,
        size,
        current_price,
        cart_key,
        cart,
    ) = await getall(callback=callback, redis=redis, db=db)
    await redis.hincrby(cart_key, callback.data[5:], 1)
    await cart.add(product.get_current_price(size))
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("minus_"))
async def minus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (
        product,
        callback_name,
        size,
        current_price,
        cart_key,
        cart,
    ) = await getall(callback=callback, redis=redis, db=db)
    quantity = await redis.hget(cart_key, callback.data[6:])
    if int(quantity) > 1:
        await redis.hincrby(cart_key, callback.data[6:], -1)
    else:
        await redis.hdel(cart_key, callback.data[6:])
        await cart.delete(product, size)
    await cart.sub(product.get_current_price(size))
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("del_"))
async def delete_from_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (
        product,
        callback_name,
        size,
        current_price,
        cart_key,
        cart,
    ) = await getall(callback=callback, redis=redis, db=db)
    await redis.hdel(cart_key, callback.data[4:])
    sorted_list_cart_items = await get_formatted_cart(callback.from_user.id, redis, db)
    await cart.delete()
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data == "erase_cart")
async def erase_cart(callback: CallbackQuery, redis: Redis):
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await cart.clear()
    await callback.message.edit_text(
        f"Корзина была очищена.",
        reply_markup=await kb.main_menu(),
    )


@router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)


#### Админка ####


@router.message(Command("admin"))
@router.callback_query(F.data == "admin")
async def handle_admin(event: Message | CallbackQuery, state: FSMContext):
    if event.from_user.id == 490573254:
        await state.clear()
        try:
            if isinstance(event, Message):
                await event.answer(
                    f"АДМИНПАНЕЛЬ:\n",
                    reply_markup=await kb.admin(),
                )
            else:
                await event.message.edit_text(
                    f"АДМИНПАНЕЛЬ:\n",
                    reply_markup=await kb.admin(),
                )
        except Exception as e:
            print(e)
    else:
        await event.answer(
            f"Я умею отвечать только на меню. Выбери пункт ниже:",
            reply_markup=await kb.main_menu(),
        )


@router.message(Command("db"))
async def handle_redis(message: Message, redis: Redis, db: AsyncSQLiteDatabase):
    await redis.set("REDIS_STATUS", "OK")
    redis_result = await redis.get("REDIS_STATUS")
    sqlite_result = await db.check_connection()
    await message.answer(
        f"REDIS_STATUS: {redis_result or "FAIL"}\nSQLITE_STATUS: {"OK" if sqlite_result else "FAIL"}"
    )
    redis.delete("REDIS_STATUS")


class AddProduct(StatesGroup):
    choose_type = State()
    add_name = State()
    add_price_small_size = State()
    add_price_big_size = State()
    add_description = State()


@router.callback_query(F.data == "product_create")
async def product_create(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"ДОБАВЛЕНИЕ ТОВАРА. Выберите тип товара:",
        reply_markup=await kb.create_product(),
    )
    await state.set_state(AddProduct.choose_type)


@router.callback_query(AddProduct.choose_type, F.data.startswith("product_create_"))
async def product_create_choose_type(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[-1]
    await state.update_data(category=category)
    categories = {
        "pizza": ("пицца", "🍕"),
        "snack": ("закуска", "🍟"),
        "drink": ("напиток", "🥤"),
        "cake": ("тортик", "🍰"),
    }
    await state.update_data(category_rus=categories[category][0])
    await state.update_data(emoji=categories[category][1])
    await state.set_state(AddProduct.add_name)
    await callback.message.edit_text(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}). Добавьте название (обязательно):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_name)
async def product_create_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    await state.update_data(
        callback_name=translit(
            message.text.replace(" ", ".").lower(), "ru", reversed=True
        )
    )
    await state.set_state(AddProduct.add_price_small_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}). Добавьте цену для стандартного размера (обязательно):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_price_small_size)
async def product_create_add_price(message: Message, state: FSMContext):
    await state.update_data(price_small=message.text.replace(",", "."))
    await state.set_state(AddProduct.add_price_big_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")} BYN). Добавьте цену для большого размера (0 если такого размера не будет):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_price_big_size)
async def product_create_add_price(message: Message, state: FSMContext):
    await state.update_data(
        price_large=message.text.replace(",", ".") if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_description)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")}/{await state.get_value("price_large")} BYN). Добавьте описание (0 если без описания):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_description)
async def product_create_add_description(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.update_data(description=message.text if message.text != "0" else None)
    data = await state.get_data()
    category = data["category"]
    category_rus = data["category_rus"]
    name = data["name"]
    callback_name = data["callback_name"]
    price_small = data["price_small"]
    price_large = data["price_large"]
    description = data["description"]
    emoji = data["emoji"]
    await state.clear()
    await db.add_product(
        name=name,
        callback_name=callback_name,
        price_small=price_small,
        price_large=price_large,
        category=category,
        description=description,
        emoji=emoji,
    )

    await message.answer(
        f"СОЗДАН ТОВАР:\nКатегория: {category_rus}\nEmoji: {emoji}\nНазвание: {name}\nCallback: {callback_name}\nКатегория в DB: {category}\nЦена: {price_small}{f" / {price_large} BYN" if price_large else " BYN (один размер)"}\nОписание: {description or "---"}",
        reply_markup=await kb.admin(),
    )


@router.callback_query(F.data == "product_delete")
async def product_delete(callback: CallbackQuery):
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА. Выберите товар из списка для удаления:",
        reply_markup=await kb.delete_product(),
    )


#### Остальное ####


@router.message(F.text)
async def handle_answer(message: Message):
    await message.answer(
        f"Я умею отвечать только на меню. Выбери пункт ниже:",
        reply_markup=await kb.main_menu(),
    )
