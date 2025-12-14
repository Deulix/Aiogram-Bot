from typing import Literal

from .callbacks import (
    AdminCallback,
    CartCallback,
    CategoryNavigationCallback,
    MenuNavigationCallback,
    ProductCallback,
)

__all__ = [
    "AdminCallback",
    "CartCallback",
    "CategoryNavigationCallback",
    "MenuNavigationCallback",
    "ProductCallback",
]

SIZES_AVAILABLE = Literal["small", "large"]

CATEGORIES_AVAILABLE = Literal["pizza", "snack", "drink", "cake"]
