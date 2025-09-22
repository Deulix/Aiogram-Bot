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


@router.callback_query(F.data.in_(["catalog", "pizza", "snack", "drink"]))
async def category_menu(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    category = callback.data

    products:List[Product] = await db.get_products_by_category(category)
    if category == "snack":
        products.extend(await db.get_products_by_category("cake"))
    await callback.message.edit_text(
        (
            (
                "Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см"
                if category == "pizza"
                else ""
            )
            + "\nДля продолжения заказа выбери пункт меню:"
        ),
        reply_markup=(
            await kb.catalog()
            if callback.data == "catalog"
            else await kb.init_category_menu(products, category)
        ),
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
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def sub(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, -price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def clear(self):
        await self.redis.delete(self.cart_key)
        await self.redis.delete(self.amount_key)

    async def delete_product(self, full_callback_name: str):
        await self.redis.hdel(self.cart_key, full_callback_name)

    async def increase(self, full_callback_name: str):
        await self.redis.hincrby(self.cart_key, full_callback_name, 1)

    async def decrease(self, full_callback_name: str):
        await self.redis.hincrby(self.cart_key, full_callback_name, -1)


async def getall(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[Product, str, Cart, str, int]:
    callback_name = callback.data.split("_")[-2]
    product = await db.get_product_by_callback_name(callback_name)
    size = callback.data.split("_")[-1]
    cart_key = f"cart:{callback.from_user.id}"
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    full_callback_name = f"{product.category}_{callback_name}_{size}"
    quantity = await redis.hget(cart_key, full_callback_name) or 0

    return (product, size, cart, full_callback_name, int(quantity))


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    (product, size, cart, full_callback_name, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )

    await cart.increase(full_callback_name)
    quantity += 1
    products = await db.get_products_by_category(product.category)
    text = f"{product.category_rus.capitalize()} {product.name} {product.large_size_text if size == "large" else product.small_size_text} ({quantity} шт) добавлен(а) в корзину"
    
    # logger.info(
    #     f"***User {user_id} added {product.name} to cart with size {size} and quantity {quantity}***"
    # )
    await cart.add(product.get_current_price(size))
    await callback.message.edit_text(
        f"{text} \n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_category_menu(products, product.category),
    )


async def get_cart(user_id: int, redis: Redis, db: AsyncSQLiteDatabase) -> List:
    cart_key = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart_key)
    print(dict_cart_items)
    list_cart_items = []
    for item_key, quantity in dict_cart_items.items():
        callback_name = item_key.split("_")[1]
        size = item_key.split("_")[-1]
        product = await db.get_product_by_callback_name(callback_name)
        list_cart_items.append([product, size, quantity])

    return list_cart_items


@router.callback_query(F.data == "cart")
async def menu_cart(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    sorted_list_cart_items = await get_cart(callback.from_user.id, redis, db)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        (
            f"Общая стоимость корзины: {await cart.get_current_amount()} BYN"
            if sorted_list_cart_items
            else "Корзина пуста"
        ),
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("plus_"))
async def plus_quantity(callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase):
    (product, size, cart, full_callback_name, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.increase(full_callback_name)
    await cart.add(product.get_current_price(size))
    sorted_list_cart_items = await get_cart(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("minus_"))
async def minus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback_name, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    if int(quantity) > 1:
        await cart.decrease(full_callback_name)
    else:
        await cart.delete_product(full_callback_name)
    await cart.sub(product.get_current_price(size))
    sorted_list_cart_items = await get_cart(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data.startswith("del_"))
async def delete_from_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback_name, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.delete_product(full_callback_name)
    sorted_list_cart_items = await get_cart(callback.from_user.id, redis, db)
    await cart.sub(product.get_current_price(size) * quantity)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(sorted_list_cart_items),
    )


@router.callback_query(F.data == "erase_cart")
async def erase_cart(callback: CallbackQuery, redis: Redis):
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        f"Корзина была очищена.",
        reply_markup=await kb.main_menu(),
    )
    await cart.clear()


@router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)


#### Админка ####


@router.message(Command("admin"))
@router.callback_query(F.data == "admin")
async def handle_admin(
    event: Message | CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    user = await db.get_user_by_id(event.from_user.id)
    if user.is_admin:
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
    user = await db.get_user_by_id(message.from_user.id)
    if user.is_admin:
        await redis.set("REDIS_STATUS", "OK")
        redis_result = await redis.get("REDIS_STATUS")
        sqlite_result = await db.check_connection()
        await message.answer(
            f"REDIS_STATUS: {redis_result or "FAIL"}\nSQLITE_STATUS: {"OK" if sqlite_result else "FAIL"}"
        )
        redis.delete("REDIS_STATUS")
    else:
        await message.answer(
            f"Я умею отвечать только на меню. Выбери пункт ниже:",
            reply_markup=await kb.main_menu(),
        )


class AddProduct(StatesGroup):
    choose_type = State()
    add_name = State()
    add_price_small_size = State()
    add_price_large_size = State()
    add_description = State()
    add_ingredients = State()
    add_nutrition = State()


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
async def product_create_add_price_small(message: Message, state: FSMContext):
    await state.update_data(price_small=message.text.replace(",", "."))
    await state.set_state(AddProduct.add_price_large_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")} BYN). Добавьте цену для большого размера (0 если такого размера не будет):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_price_large_size)
async def product_create_add_price_large(message: Message, state: FSMContext):
    await state.update_data(
        price_large=message.text.replace(",", ".") if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_description)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")}/{await state.get_value("price_large")} BYN). Добавьте описание (0 если без описания):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_description)
async def product_create_add_description(message: Message, state: FSMContext):
    await state.update_data(
        description=message.text.capitalize() if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_ingredients)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")}/{await state.get_value("price_large")} BYN). Добавьте состав (0 если без состава):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_ingredients)
async def product_create_add_ingredients(message: Message, state: FSMContext):
    await state.update_data(
        ingredients=message.text.capitalize() if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_nutrition)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА ({await state.get_value("category_rus")}, {await state.get_value("name")}, {await state.get_value("price_small")}/{await state.get_value("price_large")} BYN). Добавьте КБЖУ (0 если без КБЖУ):",
        reply_markup=await kb.cancel_creation(),
    )


@router.message(AddProduct.add_nutrition)
async def product_create_add_nutrition(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.update_data(nutrition=message.text if message.text != "0" else None)
    data = await state.get_data()
    category = data["category"]
    category_rus = data["category_rus"]
    name = data["name"]
    callback_name = data["callback_name"]
    price_small = data["price_small"]
    price_large = data["price_large"]
    description = data["description"]
    ingredients = data["ingredients"]
    nutrition = data["nutrition"]
    emoji = data["emoji"]
    await state.clear()
    await db.add_product(
        name=name,
        callback_name=callback_name,
        price_small=price_small,
        price_large=price_large,
        category=category,
        category_rus=category_rus,
        description=description,
        ingredients=ingredients,
        nutrition=nutrition,
        emoji=emoji,
    )

    await message.answer(
        f"СОЗДАН ТОВАР\nКатегория: {category_rus}\nEmoji: {emoji}\nНазвание: {name}\nCallback: {callback_name}\nКатегория в DB: {category}\nЦена: {price_small}{f" / {price_large} BYN" if price_large else " BYN (один размер)"}\nОписание: {f"\n{description}"  if description else "---"}\nСостав:{f"\n{ingredients}"  if ingredients else "---"}\nКБЖУ: {f"\n{nutrition}" if nutrition else "---"}",
        reply_markup=await kb.admin(),
    )


@router.callback_query(F.data == "product_delete")
async def product_delete(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА. Выберите товар из списка для удаления:",
        reply_markup=await kb.delete_product(products),
    )


@router.callback_query(F.startswith("product_delete_"))
async def product_delete_specified(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    product = await db.get_product_by_callback_name(callback.data.split("_")[-1])
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА. Вы уверены, что хотите удалить {product.name}:",
        reply_markup=await kb.delete_product(products),
    )


#### Остальное ####


@router.message(F.text)
async def handle_answer(message: Message):
    await message.answer(
        f"Я умею отвечать только на меню. Выбери пункт ниже:",
        reply_markup=await kb.main_menu(),
    )


@router.callback_query(F.data.startswith("info_"))
async def product_info(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    callback_name = callback.data.split("_")[2]
    product = await db.get_product_by_callback_name(callback_name)
    await callback.answer(
        f"{product.category_rus.capitalize()} {product.name}\n{f"\n{product.description}\n" if product.description else ""}{f"\nСостав: \n{product.ingredients}\n" if product.ingredients else ""}{f"\n{product.nutrition}" if product.nutrition else ""}",
        show_alert=True,
    )
