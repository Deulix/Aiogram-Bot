from typing import Literal

from aiogram.filters.callback_data import CallbackData

from src.app.config.settings import CATEGORIES_AVAILABLE, SIZES_AVAILABLE

MENU_COMMANDS = Literal["cart", "main_menu", "catalog", "contacts", "orders", "admin"]
ORDER_COMMANDS = Literal["order_details", "cancel", "confirm", "edit_street"]
CATEGORY_COMMANDS = Literal["pizza", "snack", "drink"]
CART_COMMANDS = Literal["increase", "decrease", "erase_all", "delete", "make_order"]
PRODUCT_COMMANDS = Literal["add_to_cart", "view_product_details"]
ADMIN_COMMANDS = Literal[
    "add_product",
    "edit_product",
    "delete_product",
    "confirm_deleting_product",
    "admin_list",
    "test_functions",
    "test_payment",
    "check_db",
    "get_admin_info",
    "create_admin",
    "dismiss_admin",
]
# PAYMENT_COMMANDS = Literal["start_payment", "confirm_payment", "cancel_payment"]


class MenuNavigationCallback(CallbackData, prefix="menu"):
    action: MENU_COMMANDS

    @classmethod
    def CART(cls):
        return cls(action="cart").pack()

    @classmethod
    def MAIN_MENU(cls):
        return cls(action="main_menu").pack()

    @classmethod
    def CATALOG(cls):
        return cls(action="catalog").pack()

    @classmethod
    def CONTACTS(cls):
        return cls(action="contacts").pack()

    @classmethod
    def ORDERS(cls):
        return cls(action="orders").pack()

    @classmethod
    def ADMIN(cls):
        return cls(action="admin").pack()


class OrderCallback(CallbackData, prefix="order"):
    action: ORDER_COMMANDS
    order_id: int | None = None

    @classmethod
    def get_order_details(cls, order_id):
        return cls(action="order_details", order_id=order_id).pack()

    @classmethod
    def cancel_order(cls, order_id):
        return cls(action="cancel", order_id=order_id).pack()

    @classmethod
    def confirm_order(cls, order_id):
        return cls(action="confirm", order_id=order_id).pack()

    @classmethod
    def edit_street(cls):
        return cls(action="edit_street").pack()


class CategoryNavigationCallback(CallbackData, prefix="category"):
    action: CATEGORY_COMMANDS

    @classmethod
    def PIZZAS(cls):
        return cls(action="pizza").pack()

    @classmethod
    def SNACKS(cls):
        return cls(action="snack").pack()

    @classmethod
    def DRINKS(cls):
        return cls(action="drink").pack()


class CartCallback(CallbackData, prefix="cart"):
    action: CART_COMMANDS
    product_id: int | None = None
    size: SIZES_AVAILABLE | None = None

    @classmethod
    def increase(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="increase", product_id=product_id, size=size).pack()

    @classmethod
    def decrease(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="decrease", product_id=product_id, size=size).pack()

    @classmethod
    def delete(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="delete", product_id=product_id, size=size).pack()

    @classmethod
    def ERASE_ALL(cls):
        return cls(action="erase_all").pack()

    @classmethod
    def MAKE_ORDER(cls):
        return cls(action="make_order").pack()


class ProductCallback(CallbackData, prefix="product"):
    action: PRODUCT_COMMANDS
    product_id: int
    size: SIZES_AVAILABLE | None = None

    @classmethod
    def view_product_details(cls, product_id: int):
        return cls(action="view_product_details", product_id=product_id).pack()

    @classmethod
    def add_small_size(cls, product_id: int):
        return cls(action="add_to_cart", product_id=product_id, size="small").pack()

    @classmethod
    def add_large_size(cls, product_id: int):
        return cls(action="add_to_cart", product_id=product_id, size="large").pack()


class AdminCallback(CallbackData, prefix="admin"):
    action: ADMIN_COMMANDS
    product_category: CATEGORIES_AVAILABLE | None = None
    editing_field: Literal[
        "name",
        "description",
        "price_small",
        "price_large",
        "ingredients",
        "nutrition",
        "category",
        None,
    ] = None
    product_id: int | None = None
    user_id: int | None = None

    @classmethod
    def ADD_PRODUCT(cls):
        return cls(action="add_product").pack()

    @classmethod
    def add_product(cls, product_category: CATEGORIES_AVAILABLE):
        return cls(action="add_product", product_category=product_category).pack()

    @classmethod
    def EDIT_PRODUCT(cls):
        return cls(action="edit_product").pack()

    @classmethod
    def edit_product(cls, product_id: int):
        return cls(action="edit_product", product_id=product_id).pack()

    @classmethod
    def edit_field(
        cls,
        product_id: int,
        field: Literal[
            "name",
            "description",
            "price_small",
            "price_large",
            "ingredients",
            "nutrition",
            "category",
        ],
    ):
        return cls(
            action="edit_product", product_id=product_id, editing_field=field
        ).pack()

    @classmethod
    def DELETE_PRODUCT(cls):
        return cls(action="delete_product", product_id=None).pack()

    @classmethod
    def delete_product(cls, product_id: int):
        return cls(action="delete_product", product_id=product_id).pack()

    @classmethod
    def confirm_deleting_product(cls, product_id: int):
        return cls(action="confirm_deleting_product", product_id=product_id).pack()

    @classmethod
    def ADMIN_LIST(cls):
        return cls(action="admin_list").pack()

    @classmethod
    def CREATE_ADMIN(cls):
        return cls(action="create_admin").pack()

    @classmethod
    def create_admin(cls, user_id: int):
        return cls(action="create_admin", user_id=user_id).pack()

    @classmethod
    def dismiss_admin(cls, user_id: int):
        return cls(action="dismiss_admin", user_id=user_id).pack()

    @classmethod
    def TEST_FUNCTIONS(cls):
        return cls(action="test_functions").pack()

    @classmethod
    def TEST_PAYMENT(cls):
        return cls(action="test_payment").pack()

    @classmethod
    def CHECK_DB(cls):
        return cls(action="check_db").pack()


# class PaymentCallback(CallbackData, prefix="payment"):
#     action: PAYMENT_COMMANDS

#     @classmethod
#     def START_PAYMENT(cls):
#         return cls(action="start_payment").pack()

#     @classmethod
#     def CONFIRM_PAYMENT(cls):
#         return cls(action="confirm_payment").pack()

#     @classmethod
#     def CANCEL_PAYMENT(cls):
#         return cls(action="cancel_payment").pack()
