import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel
from redis.asyncio import Redis

# from transliterate import translit
import app.keyboards as kb
from database.sqlite_db import AsyncSQLiteDatabase, Product

handlers_router = Router()

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


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

    adm_txt = "/admin\n/start\n" if db_user.is_admin else ""

    await message.answer(
        f"{adm_txt}Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(),
    )


@handlers_router.callback_query(F.data == "main menu")
async def cmd_main_menu(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    await state.clear()
    tg_user = callback.from_user
    db_user = await db.update_user(tg_user)
    adm_txt = "/admin\n/start\n" if db_user.is_admin else ""
    await callback.message.edit_text(
        f"{adm_txt}Привет, {db_user.first_name}! Выбери пункт меню:",
        reply_markup=await kb.main_menu(),
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
    except:
        cart_amount = None
    if category == "snack":
        products.extend(await db.get_products_by_category("cake"))
    await callback.message.edit_text(
        (
            f"{"Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см\n\n" if category == "pizza" else ""}{f"Общая стоимость корзины: {cart_amount:.2f} BYN\n\n" if cart_amount else ""}Для продолжения заказа выбери пункт меню:"
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
) -> tuple[Product, str, Cart, str, int, float, list]:
    id = callback.data.split("_")[-2]
    product = await db.get_product_by_id(id)
    size = callback.data.split("_")[-1]
    cart_key = f"cart:{callback.from_user.id}"
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    full_callback = f"{id}_{size}"
    quantity = await redis.hget(cart_key, full_callback) or 0
    cart_amount = await cart.get_current_amount()
    list_cart_items = await get_cart_list(callback.from_user.id, redis, db)

    return (
        product,
        size,
        cart,
        full_callback,
        int(quantity),
        cart_amount,
        list_cart_items,
    )


@handlers_router.callback_query(F.data.startswith("add_"))
async def cmd_add_to_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity, *_) = await getall(
        callback=callback, redis=redis, db=db
    )

    await cart.increase_prod_count(full_callback)
    quantity += 1
    products: list[Product] = await db.get_products_by_category(product.category)
    if product.category == "snack":
        products.extend(await db.get_products_by_category("cake"))
    text = f"{product.category_rus.capitalize()} {product.name} {product.large_size_text if size == "large" else product.small_size_text} ({quantity} шт) добавлен(а) в корзину"

    # logger.info(
    #     f"***User {user_id} added {product.name} to cart with size {size} and quantity {quantity}***"
    # )
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    await callback.message.edit_text(
        f"{"Стандарт: ~ 650 грамм, 29 см\nБольшая: ~ 850 грамм, 36 см" if product.category == "pizza"else ""}\n\n{text}\n\nОбщая стоимость корзины: {cart_amount:.2f} BYN\n\nДля продолжения заказа выбери пункт меню:",
        reply_markup=await kb.init_category_menu(products),
    )


async def get_cart_list(user_id: int, redis: Redis, db: AsyncSQLiteDatabase) -> list:
    cart_key = f"cart:{user_id}"
    dict_cart_items = await redis.hgetall(cart_key)
    print(dict_cart_items)
    list_cart_items = []
    for item_key, quantity in dict_cart_items.items():
        id = item_key.split("_")[0]
        size = item_key.split("_")[-1]
        product = await db.get_product_by_id(id)
        list_cart_items.append([product, size, int(quantity)])
    print(list_cart_items)
    return list_cart_items


@handlers_router.callback_query(F.data == "cart")
async def cmd_cart_menu(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.clear()
    user_id = callback.from_user.id
    list_cart_items = await get_cart_list(user_id, redis, db)
    cart = Cart(user_id, redis)
    try:
        cart_amount = await cart.get_current_amount()
    except TypeError:
        cart_amount = None
    await callback.message.edit_text(
        (f"КОРЗИНА:" if list_cart_items else "В корзине нет товаров."),
        reply_markup=await kb.init_cart(list_cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("plus_"))
async def cmd_plus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, _, _, list_cart_items) = await getall(
        callback=callback, redis=redis, db=db
    )
    await cart.increase_prod_count(full_callback)
    await cart.add_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    await callback.message.edit_text(
        f"КОРЗИНА:",
        reply_markup=await kb.init_cart(list_cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("minus_"))
async def cmd_minus_quantity(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity, _, list_cart_items) = await getall(
        callback=callback, redis=redis, db=db
    )
    if int(quantity) > 1:
        await cart.decrease_prod_count(full_callback)
    else:
        await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size))
    cart_amount = await cart.get_current_amount()
    await callback.message.edit_text(
        f"КОРЗИНА:",
        reply_markup=await kb.init_cart(list_cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data.startswith("del_"))
async def cmd_delete_from_cart(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    (product, size, cart, full_callback, quantity, cart_amount, list_cart_items) = (
        await getall(callback=callback, redis=redis, db=db)
    )
    await cart.delete_product(full_callback)
    await cart.sub_amount(product.get_size_price(size) * quantity)
    await callback.message.edit_text(
        f"{callback.from_user.first_name}, вот твоя корзина:\n\nОбщая стоимость корзины: {await cart.get_current_amount()} BYN",
        reply_markup=await kb.init_cart(list_cart_items, cart_amount),
    )


@handlers_router.callback_query(F.data == "erase_cart")
async def cmd_erase_cart(callback: CallbackQuery, redis: Redis):
    cart = Cart(user_id=callback.from_user.id, redis=redis)
    await callback.message.edit_text(
        f"Корзина была очищена.",
        reply_markup=await kb.main_menu(),
    )
    await cart.clear()


@handlers_router.callback_query(F.data == "contacts")
async def menu_contacts(callback: CallbackQuery):
    await callback.answer("Контакты:\n+375291112233", show_alert=True)


#### АДМИНКА ####


@handlers_router.message(Command("admin"))
@handlers_router.callback_query(F.data == "admin")
async def cmd_handle_admin(
    event: Message | CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    user_id = event.from_user.id
    user = await db.get_user_by_id(user_id)
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


@handlers_router.message(Command("db"))
async def cmd_handle_redis(message: Message, redis: Redis, db: AsyncSQLiteDatabase):
    user_id = message.from_user.id
    user = await db.get_user_by_id(user_id)
    if user.is_admin:
        await redis.set("REDIS_STATUS", "OK")
        redis_result = await redis.get("REDIS_STATUS")
        sqlite_result = await db.check_connection()
        await message.answer(
            f"/admin\n/start\nREDIS_STATUS: {redis_result or "FAIL"}\nSQLITE_STATUS: {"OK" if sqlite_result else "FAIL"}"
        )
        await redis.delete("REDIS_STATUS")
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
        f"ДОБАВЛЕНИЕ ТОВАРА \nВыберите тип товара:",
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
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}) \nДобавьте название (обязательно):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_name)
async def state_product_create_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    # await state.update_data(
    #     callback_name=translit(
    #         message.text.replace(" ", ".").lower(), "ru", reversed=True
    #     )
    # )
    await state.set_state(AddProduct.add_price_small_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}, {await state.get_value("name")}) \nДобавьте цену для стандартного размера (обязательно):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_price_small_size)
async def state_product_create_add_price_small(message: Message, state: FSMContext):
    await state.update_data(price_small=message.text.replace(",", "."))
    await state.set_state(AddProduct.add_price_large_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}, {await state.get_value("name")}, "
        f"{await state.get_value("price_small")} BYN) \nДобавьте цену для большого размера (0 если такого размера не будет):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_price_large_size)
async def state_product_create_add_price_large(message: Message, state: FSMContext):
    await state.update_data(
        price_large=message.text.replace(",", ".") if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_description)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}, {await state.get_value("name")}, "
        f"{await state.get_value("price_small")}/{await state.get_value("price_large")} BYN) \nДобавьте описание (0 если без описания):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_description)
async def state_product_create_add_description(message: Message, state: FSMContext):
    await state.update_data(
        description=message.text.capitalize() if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_ingredients)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}, {await state.get_value("name")},"
        f"{await state.get_value("price_small")}/{await state.get_value("price_large")} BYN) \nДобавьте состав (0 если без состава):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_ingredients)
async def state_product_create_add_ingredients(message: Message, state: FSMContext):
    await state.update_data(
        ingredients=message.text.capitalize() if message.text != "0" else None
    )
    await state.set_state(AddProduct.add_nutrition)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value("category_rus")}, {await state.get_value("name")}, "
        f"{await state.get_value("price_small")}/{await state.get_value("price_large")} BYN) \nДобавьте КБЖУ (0 если без КБЖУ):",
        reply_markup=await kb.cancel_creation(),
    )


@handlers_router.message(AddProduct.add_nutrition)
async def state_product_create_add_nutrition(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    await state.update_data(nutrition=message.text if message.text != "0" else None)
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
    await db.add_product(
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
        f"""СОЗДАН ТОВАР\nКатегория: {category_rus}\nEmoji: {emoji}
        \nНазвание: {name}\n
        Категория в DB: {category}\n
        Цена: {price_small}{f" / {price_large} BYN" if price_large else " BYN (один размер)"}\n
        Описание: {f"\n{description}"  if description else "---"}\n
        Состав:{f"\n{ingredients}"  if ingredients else "---"}\n
        КБЖУ: {f"\n{nutrition}" if nutrition else "---"}""",
        reply_markup=await kb.admin(),
    )


@handlers_router.callback_query(F.data == "product_delete")
async def cmd_product_delete(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА \nВыберите товар из списка для удаления:",
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
        f"РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите товар из списка для изменения:",
        reply_markup=await kb.product_edit(products),
    )


@handlers_router.callback_query(F.data.startswith("product_edit_"))
async def cmd_product_edit_choose(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.message.edit_text(
        f"РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите значение из списка для изменения",
        reply_markup=await kb.product_edit_choose(product),
    )


#### ОФОРМЛЕНИЕ ЗАКАЗА ####


class OrderStates(StatesGroup):
    client = State()
    street = State()
    house = State()
    apartment = State()
    floor = State()
    additional_info = State()


@handlers_router.callback_query(F.data == "make_order")
async def start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите имя клиента:",
        reply_markup=await kb.cancel_payment(),
    )
    await state.set_state(OrderStates.client)


@handlers_router.message(OrderStates.client)
async def client(message: Message, state: FSMContext):
    await state.update_data(client=message.text)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите улицу:", reply_markup=await kb.cancel_payment()
    )
    await state.set_state(OrderStates.street)


@handlers_router.message(OrderStates.street)
async def street(message: Message, state: FSMContext):
    await state.update_data(street=message.text)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер дома:",
        reply_markup=await kb.cancel_payment(),
    )
    await state.set_state(OrderStates.house)


@handlers_router.message(OrderStates.house)
async def house(message: Message, state: FSMContext):
    await state.update_data(house=message.text)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите номер квартиры:",
        reply_markup=await kb.cancel_payment(),
    )
    await state.set_state(OrderStates.apartment)


@handlers_router.message(OrderStates.apartment)
async def apartment(message: Message, state: FSMContext):
    await state.update_data(apartment=message.text)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите этаж:", reply_markup=await kb.cancel_payment()
    )
    await state.set_state(OrderStates.floor)


@handlers_router.message(OrderStates.floor)
async def floor(message: Message, state: FSMContext):
    await state.update_data(floor=message.text)

    await message.answer(
        "ОФОРМЛЕНИЕ ЗАКАЗА\n\nВведите дополнительную информацию:",
        reply_markup=await kb.cancel_payment(),
    )
    await state.set_state(OrderStates.additional_info)


@handlers_router.message(OrderStates.additional_info)
async def additional_info(
    message: Message, state: FSMContext, redis: Redis, db: AsyncSQLiteDatabase
):
    await state.update_data(additional_info=message.text)
    data = await state.get_data()
    client = data["client"]
    street = data["street"]
    house = data["house"]
    apartment = data["apartment"]
    floor = data["floor"]
    additional_info = message.text

    list_cart_items = await get_cart_list(message.from_user.id, redis, db)
    cart = Cart(user_id=message.from_user.id, redis=redis)
    amount = await cart.get_current_amount()

    cart_text = []
    for item in list_cart_items:
        product, size, quantity = item
        product: Product
        price = product.get_size_price(size)
        cart_text.append(
            f"{product.category_rus.capitalize()} {product.name} {product.get_size_text(size)} - {quantity} шт. -- {(price * quantity):.2f} BYN\n"
        )
        cart_text_normalized = "".join(cart_text)

    address_text = f"Имя: {client}, Адрес: ул. {street} {house}, кв {apartment or "не указан"}, этаж: {floor or "не указан"}\nДоп инфо: {additional_info or "не указано"}"
    await message.answer(
        f'Спасибо, заказ оформлен!\n\n{cart_text_normalized}\n\n{address_text}\n\nСТОИМОСТЬ {amount:.2f} BYN\n\nПосмотреть статус заказа можно в меню "Мои заказы"',
        reply_markup=await kb.pay_to_main(),
    )
    await db.add_order(message.from_user.id, list_cart_items)
    await state.clear()
    await cart.clear()


#### ЗАКАЗЫ ####


@handlers_router.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    user_id = callback.from_user.id
    orders = await db.get_orders(user_id)
    await callback.message.edit_text(
        "Список заказов:", reply_markup=await kb.orders(orders)
    )


@handlers_router.callback_query(F.data.startswith("order_"))
async def orders(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    order_id = callback.data.split("_")[-1]
    order = await db.get_order_by_id(order_id)
    await callback.message.edit_text(
        "Список заказов:", reply_markup=await kb.order_info(order)
    )


#### ОСТАЛЬНОЕ ####


@handlers_router.message(Command("deleteme"))
async def handle_answer(message: Message):
    await message.delete()
    await message.answer(
        "Я удалил твоё сообщение, и что ты мне сделаешь?")


@handlers_router.message(F.text)
async def handle_answer(message: Message):
    await message.answer(
        f"Я умею отвечать только на меню. Выбери пункт ниже:",
        reply_markup=await kb.main_menu(),
    )


@handlers_router.callback_query(F.data.startswith("info_"))
async def product_info(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    product_id = callback.data.split("_")[-1]
    product = await db.get_product_by_id(product_id)
    await callback.answer(
        f"{product.category_rus.capitalize()} {product.name}\n{f"\n{product.description}\n" if product.description else ""}\
        {f"\nСостав: \n{product.ingredients}\n" if product.ingredients else ""}{f"\n{product.nutrition}" if product.nutrition else ""}",
        show_alert=True,
    )


@handlers_router.message(F.photo)
async def cmd_handle_photo(message: Message):
    await message.reply(message.photo[-1].file_id)
