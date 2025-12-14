from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from src.app.bot.core.callbacks import AdminCallback
from src.app.bot.keyboards import adm_kb, nav_kb, tst_kb
from src.app.config.logger import logger
from src.app.config.settings import settings
from src.app.database.sqlite_db import AsyncSQLiteDatabase

admin_router = Router()


@admin_router.callback_query(AdminCallback.filter(action="admin"))
async def cmd_handle_admin(
    callback: CallbackQuery, state: FSMContext, db: AsyncSQLiteDatabase
):
    user_id = callback.from_user.id
    user = await db.get_user_by_id(user_id)
    if user.is_admin:
        await state.clear()
        await callback.message.edit_text(
            "АДМИНПАНЕЛЬ:\n",
            reply_markup=await adm_kb.admin(),
        )

    else:
        await callback.message.edit_text(
            "Я умею отвечать только на меню. Выбери пункт ниже:",
            reply_markup=await nav_kb.main_menu(user),
        )


@admin_router.callback_query(AdminCallback.filter(action="check_db"))
async def cmd_handle_redis(
    callback: CallbackQuery, redis: Redis, db: AsyncSQLiteDatabase
):
    redis_result = await redis.ping()
    logger.info("Соединение с Redis активно")

    sqlite_result = await db.check_connection()
    await callback.message.edit_text(
        f"REDIS_STATUS: {'OK' if redis_result else 'FAIL'}\nSQLITE_STATUS: {'OK' if sqlite_result else 'FAIL'}",
        reply_markup=await adm_kb.admin(),
    )
    await redis.delete("REDIS_STATUS")


class AddProduct(StatesGroup):
    choose_category = State()
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


@admin_router.callback_query(
    AdminCallback.filter(action="add_product", product_category=None)
)
async def cmd_product_create(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ДОБАВЛЕНИЕ ТОВАРА \nВыберите категорию товара:",
        reply_markup=await adm_kb.create_product(),
    )
    await state.set_state(AddProduct.choose_category)


@admin_router.callback_query(
    AddProduct.choose_category,
    AdminCallback.filter(action="add_product", product_category=F.is_not(None)),
)
async def state_product_create_choose_category(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
):
    category = callback_data.product_category
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
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_name)
async def state_product_create_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    await state.set_state(AddProduct.add_price_small_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}) \nДобавьте цену для стандартного размера (обязательно):",
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_price_small_size)
async def state_product_create_add_price_small(message: Message, state: FSMContext):
    await state.update_data(price_small=message.text.replace(",", "."))
    await state.set_state(AddProduct.add_price_large_size)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')} BYN) \nДобавьте цену для большого размера\n\n/skip для пропуска",
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_price_large_size)
async def state_product_create_add_price_large(message: Message, state: FSMContext):
    await state.update_data(
        price_large=message.text.replace(",", ".") if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_description)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте описание\n\n/skip для пропуска",
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_description)
async def state_product_create_add_description(message: Message, state: FSMContext):
    await state.update_data(
        description=message.text.capitalize() if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_ingredients)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')},"
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте состав\n\n/skip для пропуска",
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_ingredients)
async def state_product_create_add_ingredients(message: Message, state: FSMContext):
    await state.update_data(
        ingredients=message.text.capitalize() if message.text != "/skip" else None
    )
    await state.set_state(AddProduct.add_nutrition)
    await message.answer(
        f"ДОБАВЛЕНИЕ ТОВАРА \n({await state.get_value('category_rus')}, {await state.get_value('name')}, "
        f"{await state.get_value('price_small')}/{await state.get_value('price_large')} BYN) \nДобавьте КБЖУ\n\n/skip для пропуска",
        reply_markup=await adm_kb.cancel_admin_action(),
    )


@admin_router.message(AddProduct.add_nutrition)
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
        reply_markup=await adm_kb.admin(),
    )


@admin_router.callback_query(
    AdminCallback.filter(action="delete_product", product_id=None)
)
async def cmd_product_delete(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        "УДАЛЕНИЕ ТОВАРА \nВыберите товар из списка для удаления:",
        reply_markup=await adm_kb.product_delete(products),
    )


@admin_router.callback_query(
    AdminCallback.filter(action="delete_product", product_id=F.is_not(None))
)
async def cmd_product_confirm_delete(
    callback: CallbackQuery, callback_data: AdminCallback, db: AsyncSQLiteDatabase
):
    product_id = callback_data.product_id
    product = await db.get_product_by_id(product_id)
    await callback.message.edit_text(
        f"УДАЛЕНИЕ ТОВАРА \nВы уверены, что хотите удалить {product.emoji} {product.name}?",
        reply_markup=await adm_kb.confirm_deleting_product(product.id),
    )


@admin_router.callback_query(
    AdminCallback.filter(action="confirm_deleting_product", product_id=F.is_not(None))
)
async def cmd_product_confirmed_delete(
    callback: CallbackQuery, callback_data: AdminCallback, db: AsyncSQLiteDatabase
):
    product_id = callback_data.product_id
    product = await db.get_product_by_id(product_id)
    await db.delete_product(product.id)
    await callback.message.edit_text(
        f"Товар {product.emoji} {product.name} успешно удалён\nАДМИНПАНЕЛЬ:",
        reply_markup=await adm_kb.admin(),
    )


class EditProduct(StatesGroup):
    edit = State()


@admin_router.callback_query(AdminCallback.filter(action="edit_product"))
async def cmd_product_edit(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    products = await db.get_products()
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите товар из списка для изменения:",
        reply_markup=await adm_kb.product_edit(products),
    )


@admin_router.callback_query(AdminCallback.filter(action="edit_product"))
async def cmd_product_edit_choose(
    callback: CallbackQuery, callback_data: AdminCallback, db: AsyncSQLiteDatabase
):
    product_id = callback_data.product_id
    product = await db.get_product_by_id(product_id)
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВыберите значение из списка для изменения",
        reply_markup=await adm_kb.product_edit_choose(product),
    )


@admin_router.callback_query(
    AdminCallback.filter(action="edit_field", editing_field=F.is_not(None))
)
async def cmd_product_edit_choose(  # noqa: F811
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
):
    product_id = callback_data.product_id
    editing_field = callback_data.editing_field
    await state.update_data(product_id=product_id, editing_field=editing_field)
    await callback.message.edit_text(
        "РЕДАКТИРОВАНИЕ ТОВАРА \nВведите новое значение:",
        reply_markup=await adm_kb.cancel_admin_action("edit"),
    )
    await state.set_state(EditProduct.edit)


@admin_router.message(EditProduct.edit)
async def product_edit_set_new(
    message: Message, db: AsyncSQLiteDatabase, state: FSMContext
):
    data = await state.get_data()
    product_id = data["product_id"]
    product = await db.get_product_by_id(product_id)
    editing_field = data["editing_field"]
    field_dict = {
        "name": "НАЗВАНИЕ",
        "price_small": "ЦЕНА ЗА СТАНДАРТ",
        "price_large": "ЦЕНА ЗА БОЛЬШОЙ(УЮ)",
        "category": "КАТЕГОРИЯ",
        "description": "ОПИСАНИЕ",
        "ingredients": "ИНГРЕДИЕНТЫ",
        "nutrition": "КБЖУ",
    }
    field_name = field_dict[editing_field]
    new_field_value = message.text
    await db.edit_product(product_id, editing_field, new_field_value)
    await message.answer(
        f"РЕДАКТИРОВАНИЕ ТОВАРА \nВыбрано новое значение:\nНовое значение {field_name}: {new_field_value}",
        reply_markup=await adm_kb.product_edit_choose(product),
    )
    await state.set_state(EditProduct.edit)


@admin_router.callback_query(AdminCallback.filter(action="get_admin_info"))
async def get_admin_info(
    callback: CallbackQuery, callback_data: AdminCallback, db: AsyncSQLiteDatabase
):
    can_dismiss = False
    admin_id = callback_data.user_id
    admin = await db.get_user_by_id(admin_id)
    if (
        callback.from_user.id
        in [
            settings.ADMIN_ID,
            admin.id,
        ]
    ):  # Даём право снимать админку, если метод вызывает суперадминистратор (но его самого нельзя снять) или админ снимает себя
        can_dismiss = True
    await callback.message.edit_text(
        f"ИНФОРМАЦИЯ ОБ АДМИНИСТРАТОРЕ\n\nID: {admin.id}\nUsername: @{admin.username}\nИмя: {admin.first_name}\n{f'Фамилия: {admin.last_name}\n' if admin.last_name else ''}",
        reply_markup=await adm_kb.back_to_admin_list(can_dismiss, admin_id),
    )


class AdminCreation(StatesGroup):
    create = State()


@admin_router.callback_query(AdminCallback.filter(action="admin_list"))
async def admin_list(callback: CallbackQuery, db: AsyncSQLiteDatabase):
    admins = await db.get_admins()
    callback_user = callback.from_user
    await callback.message.edit_text(
        "АДМИНИСТРАТОРЫ\n\nВыберите пункт из списка:",
        reply_markup=await adm_kb.admin_list(admins, callback_user),
    )


@admin_router.callback_query(AdminCallback.filter(action="create_admin"))
async def input_admin_id(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\nВведите ID нового администратора:",
        reply_markup=await adm_kb.cancel_admin_action(),
    )
    await state.set_state(AdminCreation.create)


@admin_router.message(AdminCreation.create)
async def make_admin(message: Message, state: FSMContext, db: AsyncSQLiteDatabase):
    admin_id = message.text
    admin = await db.get_user_by_id(admin_id)
    if not admin:
        await message.answer(
            f'ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Пользователь с ID "{admin_id}" не найден. Введите корректный ID:',
            reply_markup=await adm_kb.cancel_admin_action(),
        )
    elif admin.is_admin:
        await message.answer(
            f'ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Пользователь с ID "{admin_id}" уже является администратором. Введите корректный ID:',
            reply_markup=await adm_kb.cancel_admin_action(),
        )
    else:
        await db.make_admin(admin_id)
        await message.answer(
            f"ДОБАВЛЕНИЕ АДМИНИСТРАТОРА\n\n✅ Новый администратор (ID {admin_id}, {admin.first_name}) успешно добавлен.",
            reply_markup=await adm_kb.admin(),
        )
        await state.clear()


@admin_router.callback_query(
    AdminCallback.filter(action="dismiss_admin", user_id=F.is_not(None))
)
async def dismiss_admin(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
    db: AsyncSQLiteDatabase,
):
    admin_id = callback_data.user_id
    if int(admin_id) == settings.ADMIN_ID:
        await callback.message.edit_text(
            "УДАЛЕНИЕ АДМИНИСТРАТОРА\n\n❌ ОШИБКА! Суперадминистратор не может быть снят.",
            reply_markup=await adm_kb.admin(),
        )
        return
    else:
        admin = await db.get_user_by_id(admin_id)
        await db.dismiss_admin(admin.id)
        await callback.message.edit_text(
            f"УДАЛЕНИЕ АДМИНИСТРАТОРА\n\n✅ Администратор (ID {admin.id}, {admin.first_name}) успешно снят.",
            reply_markup=await adm_kb.admin(),
        )
        await state.clear()


@admin_router.callback_query(AdminCallback.filter(action="test_functions"))
async def tests(callback: CallbackQuery):
    await callback.message.edit_text(
        "ТЕСТЫ\n\nВведите тест из списка:",
        reply_markup=await tst_kb.tests(),
    )
