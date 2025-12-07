from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        default=False, server_default=text("0"), nullable=False
    )

    @property
    def created_at_local(self):
        return self.created_at + timedelta(hours=3)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    ingredients: Mapped[str | None] = mapped_column(String(130), nullable=True)
    nutrition: Mapped[str | None] = mapped_column(String(40), nullable=True)
    price_small: Mapped[float] = mapped_column(nullable=False)
    price_large: Mapped[float] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    category_rus: Mapped[str] = mapped_column(String(50), nullable=True)
    emoji: Mapped[str] = mapped_column(String(5), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    order_items: Mapped[list["OrderItem"]] = relationship(backref="product")
    # соединяет в 2 стороны Product.order_items <-> OrderItems.product
    # вариант более явный это back_popultates, но там надо прописывать с обеих сторон
    # ПРИМЕР: в Product строчка order_items = relationship("OrderItem", back_popultates="product"),
    # а в OrderItem строчка product = relationship("Product", back_popultates="order_items")
    # тогда будет коннект, backref экономит несколько строк

    @staticmethod
    def get_size_text(category: str, size: str) -> str | None:
        sizes = {
            "pizza": {"small": "cтандарт", "large": "большая"},
            "snack": {"small": "cтандарт", "large": "большая"},
            "drink": {"small": "0.5 литра", "large": "1 литр"},
            "cake": {"small": "cтандарт", "large": "большой"},
        }
        return sizes[category][size]

    @property
    def small_size_text(self) -> str:
        if (
            self.price_large
        ):  # чтобы не показывало надпись "стандарт" у продуктов с одним размером
            return self.get_size_text(self.category, "small")
        else:
            return ""

    @property
    def large_size_text(self) -> str | None:
        return self.get_size_text(self.category, "large")

    def get_size_price(self, size) -> float | None:
        if size == "large":
            return self.price_large
        elif size == "small":
            return self.price_small
        else:
            return None

    @property
    def has_only_one_size(self):
        return self.price_large is None


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(9), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    additional_info: Mapped[str | None] = mapped_column(String(200), nullable=True)
    amount: Mapped[float] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    user: Mapped["User"] = relationship(backref="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        backref="order", cascade="all, delete-orphan"
    )

    @property
    def created_at_local(self):
        return self.created_at + timedelta(hours=3)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    size: Mapped[str] = mapped_column(String(10), nullable=False)
