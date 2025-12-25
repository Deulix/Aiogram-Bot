from enum import Enum


class SizesAvailable(str, Enum):
    SMALL = "small"
    LARGE = "large"


class CategoriesAvailable(str, Enum):
    PIZZA = "pizza"
    SNACK = "snack"
    DRINK = "drink"
    CAKE = "cake"


class MenuCommands(str, Enum):
    MAIN_MENU = "main_menu"
    CATALOG = "catalog"
    CONTACTS = "contacts"


class OrderCommands(str, Enum):
    ORDERS = "orders"
    ORDER_DETAILS = "order_details"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    EDIT_STREET = "edit_street"


class CategoryCommands(str, Enum):
    PIZZA = "pizza"
    SNACK = "snack"
    DRINK = "drink"


class CartCommands(str, Enum):
    CART = "cart"
    INCREASE = "increase"
    DECREASE = "decrease"
    ERASE_ALL = "erase_all"
    DELETE = "delete"
    MAKE_ORDER = "make_order"
    ADD_TO_CART = "add_to_cart"


class ProductCommands(str, Enum):
    VIEW_PRODUCT_DETAILS = "view_product_details"


class AdminCommands(str, Enum):
    ADMIN = "admin"
    ADD_PRODUCT = "add_product"
    EDIT_PRODUCTS_LIST = "edit_products_list"
    EDIT_PRODUCT = "edit_product"
    EDIT_FIELD = "edit_field"
    DELETE_PRODUCT = "delete_product"
    CONFIRM_DELETING_PRODUCT = "confirm_deleting_product"
    ADMIN_LIST = "admin_list"
    TEST_FUNCTIONS = "test_functions"
    TEST_PAYMENT = "test_payment"
    CHECK_DB = "check_db"
    GET_ADMIN_INFO = "get_admin_info"
    CREATE_ADMIN = "create_admin"
    DISMISS_ADMIN = "dismiss_admin"


class EditingField(str, Enum):
    NAME = "name"
    DESCRIPTION = "description"
    PRICE_SMALL = "price_small"
    PRICE_LARGE = "price_large"
    INGREDIENTS = "ingredients"
    NUTRITION = "nutrition"
    CATEGORY = "category"
