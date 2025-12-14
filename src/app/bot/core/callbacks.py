from typing import Literal

from aiogram.filters.callback_data import CallbackData

from src.app.bot.core import CATEGORIES_AVAILABLE, SIZES_AVAILABLE


class MenuNavigationCallback(CallbackData, prefix="menu"):
    action: Literal["cart", "main_menu", "catalog", "contacts", "orders", "admin"]

    @property
    def CART(self):
        return MenuNavigationCallback(action="cart").pack()

    @property
    def MAIN_MENU(self):
        return MenuNavigationCallback(action="main_menu").pack()

    @property
    def CATALOG(self):
        return MenuNavigationCallback(action="catalog").pack()

    @property
    def CONTACTS(self):
        return MenuNavigationCallback(action="contacts").pack()

    @property
    def ORDERS(self):
        return MenuNavigationCallback(action="orders").pack()

    @property
    def ADMIN(self):
        return MenuNavigationCallback(action="admin").pack()


class OrderCallback(CallbackData, prefix="order"):
    action: Literal["order_details", "cancel", "confirm"]
    order_id: int

    @property
    def ORDER_DETAILS(self):
        return OrderCallback(action="order_details", order_id=self.order_id).pack()

    @property
    def CANCEL(self):
        return OrderCallback(action="cancel", order_id=self.order_id).pack()

    @property
    def CONFIRM(self):
        return OrderCallback(action="confirm", order_id=self.order_id).pack()


class CategoryNavigationCallback(CallbackData, prefix="category"):
    action: Literal["list"]
    category: Literal["pizza", "snack", "drink"]

    @property
    def PIZZAS(self):
        return CategoryNavigationCallback(category="pizza", action="list").pack()

    @property
    def SNACKS(self):
        return CategoryNavigationCallback(category="snack", action="list").pack()

    @property
    def DRINKS(self):
        return CategoryNavigationCallback(category="drink", action="list").pack()


class CartCallback(CallbackData, prefix="cart"):
    action: Literal["increase", "decrease", "erase_all", "delete", "make_order"]
    product_id: int | None = None
    size: Literal["small", "large", None] = None

    @classmethod
    def increase(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="increase", product_id=product_id, size=size).pack()

    @classmethod
    def decrease(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="decrease", product_id=product_id, size=size).pack()

    @classmethod
    def delete(cls, product_id: int, size: SIZES_AVAILABLE):
        return cls(action="delete", product_id=product_id, size=size).pack()

    @property
    def ERASE_ALL(self):
        return CartCallback(action="erase_all").pack()

    @property
    def MAKE_ORDER(self):
        return CartCallback(action="make_order").pack()


class ProductCallback(CallbackData, prefix="product"):
    action: Literal["add_to_cart", "view_product_details"]
    product_id: int
    size: Literal["small", "large", None] = None

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
    action: Literal[
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
    product_category: Literal["pizza", "snack", "drink", "cake", None] = None
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

    @property
    def ADD_PRODUCT(self):
        return AdminCallback(action="add_product").pack()

    @classmethod
    def add_product(cls, product_category: CATEGORIES_AVAILABLE):
        return cls(action="add_product", product_category=product_category).pack()

    @property
    def EDIT_PRODUCT(self):
        return AdminCallback(action="edit_product").pack()

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

    @property
    def DELETE_PRODUCT(self):
        return AdminCallback(action="delete_product").pack()

    @classmethod
    def delete_product(cls, product_id: int):
        return cls(action="delete_product", product_id=product_id).pack()

    @classmethod
    def confirm_deleting_product(cls, product_id: int):
        return cls(action="delete_product", product_id=product_id).pack()

    @property
    def ADMIN_LIST(self):
        return AdminCallback(action="admin_list").pack()

    @property
    def CREATE_ADMIN(self):
        return AdminCallback(action="create_admin").pack()

    @classmethod
    def create_admin(cls, user_id: int):
        return cls(action="create_admin", user_id=user_id).pack()

    @classmethod
    def dismiss_admin(cls, user_id: int):
        return cls(action="dismiss_admin", user_id=user_id).pack()

    @property
    def TEST_FUNCTIONS(self):
        return AdminCallback(action="test_functions").pack()

    @property
    def TEST_PAYMENT(self):
        return AdminCallback(action="test_payment").pack()

    @property
    def CHECK_DB(self):
        return AdminCallback(action="check_db").pack()
