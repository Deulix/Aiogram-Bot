from aiogram.filters.callback_data import CallbackData

from src.app.config.constants import (
    AdminCommands,
    CartCommands,
    CategoriesAvailable,
    CategoryCommands,
    EditingField,
    MenuCommands,
    OrderCommands,
    ProductCommands,
    SizesAvailable,
)


class MenuNavigationCallback(CallbackData, prefix="menu"):
    action: MenuCommands

    @classmethod
    def CART(cls):
        return cls(action=CartCommands.CART)

    @classmethod
    def MAIN_MENU(cls):
        return cls(action=MenuCommands.MAIN_MENU)

    @classmethod
    def CATALOG(cls):
        return cls(action=MenuCommands.CATALOG)

    @classmethod
    def CONTACTS(cls):
        return cls(action=MenuCommands.CONTACTS)

    @classmethod
    def ORDERS(cls):
        return cls(action=OrderCommands.ORDERS)

    @classmethod
    def ADMIN(cls):
        return cls(action=AdminCommands.ADMIN)


class OrderCallback(CallbackData, prefix="order"):
    action: OrderCommands
    order_id: int

    @classmethod
    def get_order_details(cls, order_id):
        return cls(action=OrderCommands.ORDER_DETAILS, order_id=order_id)

    @classmethod
    def cancel_order(cls, order_id):
        return cls(action=OrderCommands.CANCEL, order_id=order_id)

    @classmethod
    def confirm_order(cls, order_id):
        return cls(action=OrderCommands.CONFIRM, order_id=order_id)

    @classmethod
    def edit_street(cls):
        return cls(action=OrderCommands.EDIT_STREET)


class CategoryNavigationCallback(CallbackData, prefix="category"):
    action: CategoryCommands

    @classmethod
    def PIZZAS(cls):
        return cls(action=CategoryCommands.PIZZA)

    @classmethod
    def SNACKS(cls):
        return cls(action=CategoryCommands.SNACK)

    @classmethod
    def DRINKS(cls):
        return cls(action=CategoryCommands.DRINK)


class CartCallback(CallbackData, prefix="cart"):
    action: CartCommands
    product_id: int | None = None
    size: SizesAvailable | None = None

    @classmethod
    def increase(cls, product_id: int, size: SizesAvailable):
        return cls(action=CartCommands.INCREASE, product_id=product_id, size=size)

    @classmethod
    def decrease(cls, product_id: int, size: SizesAvailable):
        return cls(action=CartCommands.DECREASE, product_id=product_id, size=size)

    @classmethod
    def delete(cls, product_id: int, size: SizesAvailable):
        return cls(action=CartCommands.DELETE, product_id=product_id, size=size)

    @classmethod
    def ERASE_ALL(cls):
        return cls(action=CartCommands.ERASE_ALL)

    @classmethod
    def MAKE_ORDER(cls):
        return cls(action=CartCommands.MAKE_ORDER)


class ProductCallback(CallbackData, prefix="product"):
    action: ProductCommands
    product_id: int
    size: SizesAvailable | None = None

    @classmethod
    def view_product_details(cls, product_id: int):
        return cls(action=ProductCommands.VIEW_PRODUCT_DETAILS, product_id=product_id)

    @classmethod
    def add_small_size(cls, product_id: int):
        return cls(
            action=CartCommands.ADD_TO_CART,
            product_id=product_id,
            size=SizesAvailable.SMALL,
        )

    @classmethod
    def add_large_size(cls, product_id: int):
        return cls(
            action=CartCommands.ADD_TO_CART,
            product_id=product_id,
            size=SizesAvailable.LARGE,
        )


class AdminCallback(CallbackData, prefix="admin"):
    action: AdminCommands
    product_category: CategoriesAvailable | None = None
    editing_field: EditingField | None = None
    product_id: int | None = None
    user_id: int | None = None

    @classmethod
    def ADD_PRODUCTS(cls):
        return cls(action=AdminCommands.ADD_PRODUCT)

    @classmethod
    def add_product(cls, product_category: CategoriesAvailable):
        return cls(action=AdminCommands.ADD_PRODUCT, product_category=product_category)

    @classmethod
    def EDIT_PRODUCTS(cls):
        return cls(action=AdminCommands.EDIT_PRODUCT, product_id=None)

    @classmethod
    def edit_product(cls, product_id: int):
        return cls(action=AdminCommands.EDIT_PRODUCT, product_id=product_id)

    @classmethod
    def edit_field(cls, product_id: int, field: EditingField):
        return cls(
            action=AdminCommands.EDIT_FIELD, product_id=product_id, editing_field=field
        )

    @classmethod
    def DELETE_PRODUCTS(cls):
        return cls(action=AdminCommands.DELETE_PRODUCT, product_id=None)

    @classmethod
    def delete_product(cls, product_id: int):
        return cls(action=AdminCommands.DELETE_PRODUCT, product_id=product_id)

    @classmethod
    def confirm_deleting_product(cls, product_id: int):
        return cls(action=AdminCommands.CONFIRM_DELETING_PRODUCT, product_id=product_id)

    @classmethod
    def ADMIN_LIST(cls):
        return cls(action=AdminCommands.ADMIN_LIST)

    @classmethod
    def get_admin_info(cls, user_id: int):
        return cls(action=AdminCommands.GET_ADMIN_INFO, user_id=user_id)

    @classmethod
    def CREATE_ADMIN(cls):
        return cls(action=AdminCommands.CREATE_ADMIN)

    @classmethod
    def create_admin(cls, user_id: int):
        return cls(action=AdminCommands.CREATE_ADMIN, user_id=user_id)

    @classmethod
    def dismiss_admin(cls, user_id: int):
        return cls(action=AdminCommands.DISMISS_ADMIN, user_id=user_id)

    @classmethod
    def TEST_FUNCTIONS(cls):
        return cls(action=AdminCommands.TEST_FUNCTIONS)

    @classmethod
    def TEST_PAYMENT(cls):
        return cls(action=AdminCommands.TEST_PAYMENT)

    @classmethod
    def CHECK_DB(cls):
        return cls(action=AdminCommands.CHECK_DB)
