import re

import aiohttp
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

# from pydantic import BaseModel
from redis.asyncio import Redis

from src.app.config.settings import settings
from src.app.database.models import Product
from src.app.database.sqlite_db import AsyncSQLiteDatabase

from . import keyboards as kb

handlers_router = Router()


@handlers_router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSQLiteDatabase, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    if not (db_user := await db.get_user_by_id(message.from_user.id)):
        db_user = await db.add_user(
            user_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
    else:
        db_user = await db.update_user(tg_user)

    await message.answer(
        f"Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(db_user),
    )


@handlers_router.callback_query(F.data == "main menu")
async def cmd_main_menu(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    await state.clear()
    tg_user = callback.from_user
    db_user = await db.update_user(tg_user)
    await callback.message.edit_text(
        f"Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(db_user),
    )


@handlers_router.callback_query(F.data.in_(["catalog", "pizza", "snack", "drink"]))
async def cmd_category_menu(
    callback: CallbackQuery, db: AsyncSQLiteDatabase, redis: Redis
):
    category = callback.data
    products: list[Product] = await db.get_products_by_category(category)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    try:
        cart_amount = await cart.get_current_amount()
    except:  # noqa: E722
        cart_amount = None
    await callback.message.edit_text(
        (
            f"{'Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см\n\n' if category == 'pizza' else ''}{f'Общая стоимость корзины: {cart_amount:.2f} BYN\n\n' if cart_amount else ''}Для продолжения заказа выбери пункт меню:"
        ),
        reply_markup=(
            await kb.catalog()
            if callback.data == "catalog"
            else await kb.init_category_menu(products)
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
        return float(current_amount) if current_amount else None

    async def add_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def sub_amount(self, price: float):
        await self.redis.incrbyfloat(self.amount_key, -price)
        await self.redis.expire(self.amount_key, 3600 * 12)
        await self.redis.expire(self.cart_key, 3600 * 12)

    async def clear(self):
        await self.redis.delete(self.cart_key)
        await self.redis.delete(self.amount_key)

    async def delete_product(self, full_callback: str):
        await self.redis.hdel(self.cart_key, full_callback)

    async def increase_prod_count(self, full_callback: str):
        await self.redis.hincrby(self.cart_key, full_callback, 1)

    async def decrease_prod_count(self, full_callback: str):
        await self.redis.hincrby(self.cart_key, full_callback, -1)


async def getall(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[Product, str, Cart, str, int, list]:
    id = callback.data.split("_")[-2]
    product = await db.get_product_by_id(id)
    size = callback.data.split("_")[-1]
    cart_key = f"cart:{callback.from_user.id}"
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    full_callback = f"{id}_{size}"
    quantity = await redis.hget(cart_key, full_callback) or 0

    return (
        product,
        size,
        cart,
        full_callback,
        int(quantity),
    )


@handlers_router.callback_query(F.data.startswith("add_"))
async def cmd_add_to_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )

    await cart.increase_prod_count(full_callback)
    quantity += 1
    products: list[Product] = await db.get_products_by_category(product.category)
    text = f"{product.category_rus.capitalize()} {product.name} {product.large_size_text if size == 'large' else product.small_size_text} ({quantity} шт) добавлен(а) в корзину"
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    await callback.message.edit_text(
        f"{'Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см' if product.category == 'pizza' else ''}\n\n{text}\n\nОбщая стоимость корзины: {cart_amount:.2f} BYN\n\nДля продолжения заказа выбери пункт меню:",
        reply_markup=await kb.init_category_menu(products),
    )


async def get_cart_items(
    user_id: int, redis: Redis, db: AsyncSQLiteDatabase
) -> tuple[tuple[Product, str, int]]:
    cart_key = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart_key)
    cart_items = []
    for item_key, quantity in dict_cart_items.items():
        id = item_key.split("_")[0]
        size = item_key.split("_")[-1]
        product = await db.get_product_by_id(id)
        cart_items.append((product, size, int(quantity)))
    category_order = ["pizza", "snack", "cake", "drink"]
    return tuple(
        sorted(
            cart_items,
            key=lambda x: (category_order.index(x[0].category), x[0].name.lower()),
        )
    )


@handlers_router.callback_query(F.data == "cart")
async def cmd_cart_menu(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.clear()
    user_id = callback.from_user.id
    cart_items = await get_cart_items(user_id, redis, db)
    cart = Cart(user_id, redis)
    try:
        cart_amount = await cart.get_current_amount()
    except TypeError:
        cart_amount = None
    await callback.message.edit_text(
        ("КОРЗИНА:" if cart_items else "В корзине нет товаров."),
        reply_markup=await kb.init_cart(cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("plus_"))
async def cmd_plus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, _) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.increase_prod_count(full_callback)
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await kb.init_cart(cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("minus_"))
async def cmd_minus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    if int(quantity) > 1:
        await cart.decrease_prod_count(full_callback)
    else:
        await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        "КОРЗИНА:",
        reply_markup=await kb.init_cart(cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("del_"))
async def cmd_delete_from_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size) * quantity)
    cart_amount = await cart.get_current_amount()
    cart_items = await get_cart_items(callback.from_user.id, redis, db)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data == "erase_cart")
async def cmd_erase_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    user_id = callback.from_user.id
    user = await db.get_user_by_id(user_id)
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        "Корзина была очищена.",
        reply_markup=await kb.main_menu(user),
    )
    await cart.clear()


@handlers_router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)


#### АДМИНКА ####


@handlers_router.callback_query(F.data == "admin")
async def cmd_handle_admin(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    user_id = callback.from_user.id
    user = await db.get_user_by_id(user_id)
    if user.is_admin:
        await state.clear()
        await callback.message.edit_text(
            "АДМИНПАНЕЛЬ:\n",
            reply_markup=await kb.admin(),
        )

    else:
        await callback.message.edit_text(
            "Я умею отвечать только на меню. Выбери пункт ниже:",
            reply_markup=await kb.main_menu(user),
        )


@handlers_router.callback_query(F.data == "db_check")
async def cmd_handle_redis(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    redis_result = await redis.ping()
    logger.info("Соединение с Redis активно")

    sqlite_result = await db.check_connection()
    await callback.message.edit_text(
        f"REDIS_STATUS: {'OK' if redis_result else 'FAIL'}\nSQLITE_STATUS: {'OK' if sqlite_result else 'FAIL'}",
        reply_markup=await kb.admin(),
    )
    await redis.delete("REDIS_STATUS")


class AddProduct(StatesGroup):
    choose_type = State()
    add_name = State()
    add_price_small_size = State()
    add_price_large_size = State()
    add_description = State()
    add_ingredients = State()
    add_nutrition = State()


# class ProductData(BaseModel):
#     name: str
#     description: str = None
#     ingredients: str = None
#     nutrition: str = None
#     price_small: str
#     price_large: str = None
#     category: str
#     category_rus: str
#     emoji: str


@handlers_router.callback_query(F.data == "product_create")
async def cmd_product_create(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ДОБАВЛЕНИЕ ТОВАРА \nВыберите тип товара:",
        reply_markup=await kb.create_product(),
    )
    await state.set_state(AddProduct.choose_type)


@handlers_router.callback_query(
    AddProduct.choose_type, F.data.startswith("product_create_")
)
async def state_product_create_choose_type(callback: CallbackQuery, state: FSMContext):
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
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}) \nДобавьте название (обязательно):",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_name)
async def state_product_create_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    await state.set_state(AddProduct.add_price_small_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}) \nДобавьте цену для стандартного размера (обязательно):",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_price_small_size)
async def state_product_create_add_price_small(message: Message, state: FSMContext):
    await state.update_data(price_small=message.text.replace(",", "."))
    await state.set_state(AddProduct.add_price_large_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')} BYN) \nДобавьте цену для большого размера\n\n/skip для пропуска",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_price_large_size)
async def state_product_create_add_price_large(message: Message, state: FSMContext):
    await state.update_data(
        price_large=message.text.replace(",", ".") if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_description)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте описание\n\n/skip для пропуска",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_description)
async def state_product_create_add_description(message: Message, state: FSMContext):
    await state.update_data(
        description=message.text.capitalize() if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_ingredients)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')},"
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте состав\n\n/skip для пропуска",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_ingredients)
async def state_product_create_add_ingredients(message: Message, state: FSMContext):
    await state.update_data(
        ingredients=message.text.capitalize() if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_nutrition)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте КБЖУ\n\n/skip для пропуска",
        reply_markup=await kb.cancel_admin_action(),
    )


@handlers_router.message(AddProduct.add_nutrition)
async def state_product_create_add_nutrition(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.update_data(nutrition=message.text if message.text != "/skip" else None)
    data = await state.get_data()
    category = data["category"]
    category_rus = data["category_rus"]
    name = data["name"]
    price_small = data["price_small"]
    price_large = data["price_large"]
    description = data["description"]
    ingredients = data["ingredients"]
    nutrition = data["nutrition"]
    emoji = data["emoji"]
    await state.clear()
    product = await db.add_product(
        name=name,
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
        f"СОЗДАН ТОВАР\nКатегория: {product.category_rus}\nEmoji: {product.emoji}"
        f"\nНазвание: {product.name}\n"
        f"Категория в DB: {product.category}\n"
        f"Цена: {product.price_small}{f' / {product.price_large} BYN' if product.price_large else ' BYN (один размер)'}\n"
        f"Описание: {f'\n{product.description}' if product.description else '---'}\n"
        f"Состав:{f'\n{product.ingredients}' if product.ingredients else '---'}\n"
        f"КБЖУ: {f'\n{product.nutrition}' if product.nutrition else '---'}",
        reply_markup=await kb.admin(),
    )


@handlers_router.callback_query(F.data == "product_delete")
async def cmd_product_delete(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        "УДАЛЕНИЕ ТОВАРА \nВыберите товар из списка для удаления:",
        reply_markup=await kb.product_delete(products),
    )


@handlers_router.callback_query(F.data.startswith("product_delete_"))
async def cmd_product_confirm_delete(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА \nВы уверены, что хотите удалить {product.emoji} {product.name}?",
        reply_markup=await kb.product_confirmed_delete(product.id),
    )


@handlers_router.callback_query(F.data.startswith("product_confirmed_delete_"))
async def cmd_product_confirmed_delete(
    callback: CallbackQuery, db: AsyncSQLiteDatabase
):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await db.delete_product(product.id)
    await callback.message.edit_text(
        f"Товар {product.emoji} {product.name} успешно удалён\nАДМИНПАНЕЛЬ:",
        reply_markup=await kb.admin(),
    )


class EditProduct(StatesGroup):
    edit = State()


@handlers_router.callback_query(F.data == "product_edit")
async def cmd_product_edit(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите товар из списка для изменения:",
        reply_markup=await kb.product_edit(products),
    )


@handlers_router.callback_query(F.data.startswith("product_edit_"))
async def cmd_product_edit_choose(
    callback: CallbackQuery, db: AsyncSQLiteDatabase, state: FSMContext
):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите значение из списка для изменения",
        reply_markup=await kb.product_edit_choose(product),
    )


@handlers_router.callback_query(F.data.startswith("product_parameter_edit_"))
async def cmd_product_edit_choose(callback: CallbackQuery, state: FSMContext):  # noqa: F811
    parts = callback.data.split("_")
    product_id = parts[-1]
    product_parameter = parts[-2].replace("-", "_")
    await state.update_data(product_id=product_id, product_parameter=product_parameter)
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВведите новое значение:",
        reply_markup=await kb.cancel_admin_action("edit"),
    )
    await state.set_state(EditProduct.edit)


@handlers_router.message(EditProduct.edit)
async def cmd_product_edit_enter_new(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    data = await state.get_data()
    product_id = data["product_id"]
    product = await db.get_product_by_id(product_id)
    product_parameter = data["product_parameter"]
    parameter_dict = {
        "name": "НАЗВАНИЕ",
        "price_small": "ЦЕНА ЗА СТАНДАРТ",
        "price_large": "ЦЕНА ЗА БОЛЬШОЙ(УЮ)",
        "category": "КАТЕГОРИЯ",
        "description": "ОПИСАНИЕ",
        "ingredients": "ИНГРЕДИЕНТЫ",
        "nutrition": "КБЖУ",
    }
    parameter_name = parameter_dict[product_parameter]
    new_parameter_value = message.text
    await db.edit_product(product_id, product_parameter, new_parameter_value)
    await message.answer(
        f"РЕДАКТИРОВАНИЕ ТОВАРА \nВыбрано новое значение:\nНовое значение {parameter_name}: {new_parameter_value}",
        reply_markup=await kb.product_edit_choose(product),
    )
    await state.set_state(EditProduct.edit)


@handlers_router.callback_query(F.data.startswith("admin_id_"))
async def get_admin_info(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    can_dismiss = False
    admin_id = callback.data.split("_")[-1]
    admin = await db.get_user_by_id(admin_id)
    if (
        callback.from_user.id
        in [
            settings.ADMIN_ID,
            admin.id,
        ]
    ):  # Даём право снимать админку, если метод вызывает суперадминистратор или админ снимает себя
        can_dismiss = True
    await callback.message.edit_text(
        f"ИНФОРМАЦИЯ ОБ АДМИНИСТРАТОРЕ\n\nID: {admin.id}\nUsername: @{admin.username}\nИмя: {admin.first_name}\n{f'Фамилия: {admin.last_name}\n' if admin.last_name else ''}",
        reply_markup=await kb.back_to_admin_list(can_dismiss, admin_id),
    )


class AdminCreation(StatesGroup):
    create = State()


@handlers_router.callback_query(F.data == "admin_list")
async def admin_list(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    admins = await db.get_admins()
    callback_user = callback.from_user
    await callback.message.edit_text(
        "АДМИНИСТРАТОРЫ\n\nВыберите пункт из списка:",
        reply_markup=await kb.admin_list(admins, callback_user),
    )


@handlers_router.callback_query(F.data == "admin_create")
async def input_admin_id(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\nВведите ID нового администратора:",
        reply_markup=await kb.cancel_admin_action(),
    )
    await state.set_state(AdminCreation.create)


@handlers_router.message(AdminCreation.create)
async def make_admin(message: Message, state: FSMContext, db: AsyncSQLiteDatabase):
    admin_id = message.text
    admin = await db.get_user_by_id(admin_id)
    if not admin:
        await message.answer(
            f'ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Пользователь с ID "{admin_id}" не найден. Введите корректный ID:',
            reply_markup=await kb.cancel_admin_action(),
        )
    elif admin.is_admin:
        await message.answer(
            f'ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Пользователь с ID "{admin_id}" уже является администратором. Введите корректный ID:',
            reply_markup=await kb.cancel_admin_action(),
        )
    else:
        await db.make_admin(admin_id)
        await message.answer(
            f"ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n✅ Новый администратор (ID {admin_id}, {admin.first_name}) успешно добавлен.",
            reply_markup=await kb.admin(),
        )
        await state.clear()


@handlers_router.callback_query(F.data.startswith("dismiss_admin_"))
async def dismiss_admin(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    admin_id = callback.data.split("_")[-1]
    if int(admin_id) == settings.ADMIN_ID:
        await callback.message.edit_text(
            "УДАЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Суперадминистратор не может быть снят.",
            reply_markup=await kb.admin(),
        )
        return
    else:
        admin = await db.get_user_by_id(admin_id)
        await db.dismiss_admin(admin.id)
        await callback.message.edit_text(
            f"УДАЛЕНИЕ АДМИНИСТРАТОРА\n\n✅ Администратор (ID {admin.id}, {admin.first_name}) успешно снят.",
            reply_markup=await kb.admin(),
        )
        await state.clear()


@handlers_router.callback_query(F.data == "tests")
async def tests(callback: CallbackQuery):
    await callback.message.edit_text(
        "ТЕСТЫ\n\nВведите тест из списка:",
        reply_markup=await kb.tests(),
    )


#### ОФОРМЛЕНИЕ ЗАКАЗА ####


class OrderStates(StatesGroup):
    client = State()
    phone = State()
    street = State()
    house = State()
    apartment = State()
    floor = State()
    entrance = State()
    additional_info = State()


@handlers_router.callback_query(F.data == "make_order")
async def order_start_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите ваше имя:",
        reply_markup=await kb.cancel_order(),
    )
    await state.set_state(OrderStates.client)


@handlers_router.message(OrderStates.client)
async def client(message: Message, state: FSMContext):
    pattern = r"^[а-яА-Яa-zA-ZёЁ\'\-\.\s]+$"
    client_name = " ".join(word.capitalize() for word in message.text.split())
    if not re.match(pattern, client_name):
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Допустимые символы для имени: буквы(Аа-Яя, Aa-Zz), апостраф('), точка(.), дефис(-) и пробел.\n\nВведите ваше имя:",
            reply_markup=await kb.cancel_order(),
        )
        return
    elif not 1 < len(client_name) < 50:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Имя должно быть длиной от 2 до 50 символов.\n\nВведите ваше имя:",
            reply_markup=await kb.cancel_order(),
        )
        return
    else:
        await state.update_data(client_name=client_name)

        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите ваш номер телефона\nПример: 29 1234567",
            reply_markup=await kb.cancel_order(),
        )
        await state.set_state(OrderStates.phone)


@handlers_router.callback_query(F.data == "change_street")
@handlers_router.message(OrderStates.phone)
async def phone(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, Message):
        client_phone = event.text
        operators_codes = ("25", "29", "33", "44")
        operator_code_verified = client_phone.startswith(operators_codes)
        if len(client_phone) != 9 or not client_phone.isdecimal():
            await event.answer(
                f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер телефона должен быть в формате XX1234567, где XX ваш код оператора (для Беларуси {', '.join(operators_codes)}).\n✅ Пример: 291234567\n\nВведите ваш номер телефона:",
                reply_markup=await kb.cancel_order(),
            )
            return
        elif not operator_code_verified:
            await event.answer(
                f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Неверный код оператора.\nАктуальные коды: {', '.join(operators_codes)}\n✅ Пример: 291234567\n\nВведите ваш номер телефона:",
                reply_markup=await kb.cancel_order(),
            )
            return

        else:
            await state.update_data(phone=client_phone)

            await event.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите улицу:",
                reply_markup=await kb.cancel_order(),
            )
            await state.set_state(OrderStates.street)
    else:
        await state.set_state(OrderStates.street)
        await event.message.edit_text(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите улицу:",
            reply_markup=await kb.cancel_order(),
        )


async def validate_street_api(street: str) -> tuple[str, bool]:
    country = "Belarus"
    city = "Minsk"
    street_noralized = "улица " + " ".join(word.capitalize() for word in street.split())
    try:
        url = "https://geocode-maps.yandex.ru/v1"
        params = {
            "apikey": settings.MAPS_API_KEY,
            "geocode": f"{country}, {city}, {street}",
            "lang": "ru_RU",
            "results": 1,
            "format": "json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    geo_object = data["response"]["GeoObjectCollection"][
                        "featureMember"
                    ]
                    if geo_object:
                        geocoder_metadata = geo_object[0]["GeoObject"][
                            "metaDataProperty"
                        ]["GeocoderMetaData"]
                        precision = geocoder_metadata["precision"]
                        kind = geocoder_metadata["kind"]
                        if precision == kind == "street":
                            yandex_street_name = geo_object[0]["GeoObject"]["name"]
                            return yandex_street_name, True
                    return street_noralized, False
    except Exception as e:
        print(e)
        return street_noralized, False


@handlers_router.message(OrderStates.street)
async def street(message: Message, state: FSMContext):
    street = message.text
    if not 2 < len(street) < 50:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Название улицы должно быть от 3 до 50 символов.\n\nВведите улицу:",
            reply_markup=await kb.cancel_order(),
        )
        return

    elif street.isnumeric():
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Название улицы не должно содержать только цифры.\n\nВведите улицу:",
            reply_markup=await kb.cancel_order(),
        )
        return

    nums_count = sum(1 for с in street if с.isdigit())
    if nums_count > 2:
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! В названии улицы может быть не больше 2х цифр.\n\nВведите улицу:",
            reply_markup=await kb.cancel_order(),
        )
        return

    street_validated, found = await validate_street_api(street)
    if not found:
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n⚠️ Улица не найдена в базе, для уточнения вам перезвонит оператор либо нажмите кнопку ниже для повторного ввода.\nВыбрано: {street_validated}.\n\nВведите номер дома:",
            reply_markup=await kb.cancel_order("change_street"),
        )
    else:
        await message.answer(
            f"ОФОРМЛЕНИЕ ЗАКАЗА\n\n✅ Улица найдена в базе.\nВыбрано: {street_validated}.\n\nВведите номер дома:",
            reply_markup=await kb.cancel_order("change_street"),
        )
    await state.update_data(street=street_validated)

    await state.set_state(OrderStates.house)


@handlers_router.message(OrderStates.house)
async def house(message: Message, state: FSMContext):
    house = message.text
    if not house.isdecimal():
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер дома должен быть числовым значением.\nВведите номер дома:",
            reply_markup=await kb.cancel_order(),
        )
        return

    elif int(house) not in range(1, 300):
        await message.answer(
            "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер дома должен быть от 1 до 300.\nВведите номер дома:",
            reply_markup=await kb.cancel_order(),
        )
        return
    else:
        await state.update_data(house=house)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер квартиры или /skip для пропуска:",
        reply_markup=await kb.cancel_order(),
    )
    await state.set_state(OrderStates.apartment)


@handlers_router.message(OrderStates.apartment)
async def apartment(message: Message, state: FSMContext):
    apartment = message.text
    if apartment == "/skip":
        await state.update_data(apartment=None)
    else:
        if not apartment.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер квартиры должен быть от 1 до 1000.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return

        elif int(apartment) not in range(1, 1000):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер квартиры должен быть от 1 до 1000.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return
        else:
            await state.update_data(apartment=apartment)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите этаж или /skip для пропуска:",
        reply_markup=await kb.cancel_order(),
    )
    await state.set_state(OrderStates.floor)


@handlers_router.message(OrderStates.floor)
async def floor(message: Message, state: FSMContext):
    floor = message.text
    if floor == "/skip":
        await state.update_data(floor=None)
    else:
        if not floor.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Этаж должен быть числовым значением.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return
        elif int(floor) not in range(1, 50):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Этаж должен быть от 1 до 50.\nВведите номер квартиры или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return
        else:
            await state.update_data(floor=floor)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер подъезда или /skip для пропуска",
        reply_markup=await kb.cancel_order(),
    )
    await state.set_state(OrderStates.entrance)


@handlers_router.message(OrderStates.entrance)
async def entrance(message: Message, state: FSMContext):
    entrance = message.text
    if entrance == "/skip":
        await state.update_data(entrance=None)
    else:
        if not entrance.isdecimal():
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер подъезда должен быть числовым значением.\nВведите номер подъезда или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return
        elif int(entrance) not in range(1, 30):
            await message.answer(
                "ОФОРМЛЕНИЕ ЗАКАЗА\n\n❌ ОШИБКА! Номер подъезда должен быть от 1 до 30.\nВведите номер подъезда или /skip для пропуска:",
                reply_markup=await kb.cancel_order(),
            )
            return

        await state.update_data(entrance=entrance)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите дополнительную информацию или /skip для пропуска",
        reply_markup=await kb.cancel_order(),
    )
    await state.set_state(OrderStates.additional_info)


@handlers_router.message(OrderStates.additional_info)
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
    entrance = data["entrance"]
    additional_info = data["additional_info"]

    cart_items = await get_cart_items(message.from_user.id, redis, db)
    cart = Cart(user_id=message.from_user.id, redis=redis)
    amount = await cart.get_current_amount()

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
        f"подъезд {entrance}" if entrance else None,
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
        reply_markup=await kb.order_confirm(order.id),
    )
    await state.clear()
    await cart.clear()


#### ЗАКАЗЫ ####


@handlers_router.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    user_id = callback.from_user.id
    orders = await db.get_orders_by_user(user_id)
    await callback.message.edit_text(
        "СПИСОК ЗАКАЗОВ:" if orders else "Список заказов пуст.",
        reply_markup=await kb.orders(orders),
    )


@handlers_router.callback_query(F.data.startswith("order_"))
async def order_by_id(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    order_id = callback.data.split("_")[-1]
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
        reply_markup=await kb.order_info(order),
    )


#### ОСТАЛЬНОЕ ####

# @handlers_router.message(F.text)
# async def handle_answer(message: Message):
#     await message.answer(
#         f"Я умею отвечать только на меню. Выбери пункт ниже:",
#         reply_markup=await kb.main_menu(),
#     )


@handlers_router.callback_query(F.data.startswith("info_"))
async def product_info(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.answer(
        f"{product.category_rus.capitalize()} {product.name}\n{f'\n{product.description}\n' if product.description else ''}\
        {f'\nСостав: \n{product.ingredients}\n' if product.ingredients else ''}{f'\n{product.nutrition}' if product.nutrition else ''}",
        show_alert=True,
    )


@handlers_router.message(F.photo)
async def cmd_handle_photo(message: Message):
    await message.reply(message.photo[-1].file_id)
