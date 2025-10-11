from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.sqlite_db import Product, Order, OrderItem, User


async def main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
        InlineKeyboardButton(text="👤 Мои заказы", callback_data="orders"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts"),
    )
    return keyboard.adjust(1, 1, 2).as_markup()


async def catalog():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пиццы", callback_data="pizza"),
        InlineKeyboardButton(text="🍟 Закуски", callback_data="snack"),
        InlineKeyboardButton(text="🥤 Напитки", callback_data="drink"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(1, 2, 1).as_markup()


async def init_category_menu(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        name_btn = InlineKeyboardButton(
            text=f"{product.emoji} {product.name}",
            callback_data=f"info_{product.id}",
        )
        small_size_btn = InlineKeyboardButton(
            text=f"{product.small_size_text} {product.price_small} BYN",
            callback_data=f"add_{product.id}_small",
        )
        large_size_btn = InlineKeyboardButton(
            text=f"{product.large_size_text} {product.price_large} BYN",
            callback_data=f"add_{product.id}_large",
        )

        if not product.has_only_one_size():
            keyboard.row(name_btn, small_size_btn, large_size_btn)
        else:
            keyboard.row(name_btn, small_size_btn)

    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.as_markup()


async def init_cart(list_cart_items: list, cart_amount: float):
    keyboard = InlineKeyboardBuilder()

    if list_cart_items and cart_amount:
        for product, size, quantity in list_cart_items:
            product: Product
            size: str
            quantity: str
            price_by_count = product.get_size_price(size) * int(quantity)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{product.emoji} {product.name} {product.get_size_text(size)} - {quantity} шт -- {price_by_count:.2f} BYN",
                    callback_data="1",
                )
            )
            keyboard.row(
                InlineKeyboardButton(
                    text=f"+1",
                    callback_data=f"plus_{product.id}_{size}",
                ),
                InlineKeyboardButton(
                    text=f"-1",
                    callback_data=(
                        f"minus_{product.id}_{size}"
                        if int(quantity) > 1 or len(list_cart_items) > 1
                        else "erase_cart"
                    ),
                ),
                InlineKeyboardButton(
                    text=f"❌",
                    callback_data=(
                        f"del_{product.id}_{size}"
                        if len(list_cart_items) > 1
                        else "erase_cart"
                    ),
                ),
            )
        keyboard.row(
            InlineKeyboardButton(
                text=f"✅ Оформить заказ ({float(cart_amount):.2f} BYN)",
                callback_data="make_order",
            )
        )
        keyboard.row(
            InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="erase_cart")
        )
        keyboard.row(
            InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
            InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
        )
    else:
        keyboard.add(
            InlineKeyboardButton(text="📋 Каталог", callback_data="catalog"),
            InlineKeyboardButton(text="⏪ Главное меню ", callback_data="main menu"),
        )
        keyboard.adjust(1)
    return keyboard.as_markup()


#### АДМИНКА ####


async def admin():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="✙ Добавить продукт", callback_data="product_create"),
        InlineKeyboardButton(text="🖍️ Изменить продукт", callback_data="product_edit"),
        InlineKeyboardButton(text="❌ Удалить продукт", callback_data="product_delete"),
        InlineKeyboardButton(
            text="🛑 Права суперпользователя 🛑", callback_data="admin_list"
        ),
        InlineKeyboardButton(text="👤 В меню пользователя", callback_data="main menu"),
    )
    return keyboard.adjust(1).as_markup()


async def create_product():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🍕 Пицца", callback_data="product_create_pizza"),
        InlineKeyboardButton(text="🍟 Закуска", callback_data="product_create_snack"),
        InlineKeyboardButton(text="🥤 Напиток", callback_data="product_create_drink"),
        InlineKeyboardButton(text="🍰 Тортик", callback_data="product_create_cake"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()


async def cancel_creation():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🛑 Отмена создания", callback_data="admin"),
    )
    return keyboard.adjust().as_markup()


async def admin_list(admins: list[User], callback_user: User):
    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        text = f'{admin.id} - {admin.username} - {admin.first_name}{" (Вы)" if admin.id == callback_user.id else ""}'
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"admin_id_{admin.id}"))
    keyboard.add(
        InlineKeyboardButton(
            text="Добавить нового администратора", callback_data="admin_create"
        ),
        InlineKeyboardButton(text="Назад", callback_data="admin"),
    )
    return keyboard.adjust(1).as_markup()


async def product_delete(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=f"product_delete_{product.id}",
            )
        )
    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"))
    return keyboard.as_markup()


async def product_confirmed_delete(id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="❌ УДАЛИТЬ ❌",
            callback_data=f"product_confirmed_delete_{id}",
        ),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="product_delete"),
    )

    return keyboard.as_markup()


async def product_edit(products: list[Product]):
    keyboard = InlineKeyboardBuilder()
    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product.emoji} {product.name}",
                callback_data=f"product_edit_{product.id}",
            )
        )
    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin"))
    return keyboard.as_markup()


async def product_edit_choose(product: Product):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=f"НАЗВАНИЕ ({product.name})",
            callback_data=f"product_value_edit_name_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА СТАНДАРТ ({product.price_small} BYN)",
            callback_data=f"product_value_edit_price_small_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ЦЕНА ЗА БОЛЬШОЙ(УЮ) ({f'{product.price_large} BYN' if product.price_large else "---"})",
            callback_data=f"product_value_edit_price_large_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"КАТЕГОРИЯ ({product.emoji} {product.category_rus})",
            callback_data=f"product_value_edit_category_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ОПИСАНИЕ ({product.description or "---"})",
            callback_data=f"product_value_edit_description_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"ИНГРЕДИЕНТЫ ({product.ingredients or "---"})",
            callback_data=f"product_value_edit_ingredients_{product.id}",
        ),
        InlineKeyboardButton(
            text=f"КБЖУ ({product.nutrition or "---"})",
            callback_data=f"product_value_edit_nutrition_{product.id}",
        ),
    )

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="product_edit"),
        InlineKeyboardButton(text="⏪ Админпанель", callback_data="admin"),
    )

    return keyboard.as_markup()


async def back_to_admin_list():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin_list"))
    return keyboard.adjust().as_markup()


#### ОПЛАТА ####


async def cancel_payment():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="🛑 Отмена", callback_data="cart"),
    )
    return keyboard.adjust().as_markup()


async def pay_to_main():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="Мои заказы", callback_data="orders"),
        InlineKeyboardButton(text="В главное меню", callback_data="main menu"),
    )
    return keyboard.adjust(1).as_markup()


#### ЗАКАЗЫ ####


async def orders(orders: list[Order]):
    keyboard = InlineKeyboardBuilder()
    for order in orders:
        keyboard.add(
            InlineKeyboardButton(
                text=f"Заказ #{order.id} от {order.created_at}",
                callback_data=f"order_{order.id}",
            )
        )
    keyboard.adjust(1)
    if not orders:
        keyboard.row(
            InlineKeyboardButton(text="Каталог", callback_data="catalog"),
        )
        keyboard.row(
            InlineKeyboardButton(text="Главное меню", callback_data="main menu"),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main menu"),
        )
    return keyboard.as_markup()


async def order_info():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="orders"),
    )
    keyboard.row(
        InlineKeyboardButton(text="⏪ Главное меню", callback_data="main menu"),
    )
    return keyboard.as_markup()
