from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    is_admin = Column(Boolean, default=False, server_default=text("0"), nullable=False)

    @property
    def created_at_local(self):
        return self.created_at + timedelta(hours=3)


class Product(Base):
    __tablename__ = "products"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    description: str | None = Column(Text, nullable=True)
    ingredients: str | None = Column(Text, nullable=True)
    nutrition: str | None = Column(String(100), nullable=True)
    price_small: float = Column(Float, nullable=False)
    price_large: float = Column(Float, nullable=True)
    category: str = Column(String(50), nullable=True)
    category_rus: str = Column(String(50), nullable=True)
    emoji: str = Column(String(5), nullable=True)
    created_at: datetime = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    order_items = relationship(
        "OrderItem", backref="product"
    )  # соединяет в 2 стороны Product.order_items <-> OrderItems.product
    # вариант более явный это back_popultates, но там надо прописывать с обеих сторон
    # ПРИМЕР: в Product строчка order_items = relationship("OrderItem", back_popultates="product"),
    # а в OrderItem строчка product = relationship("Product", back_popultates="order_items")
    # тогда будет коннект, backref экономит несколько строк

    def get_size_text(self, size):
        sizes = {
            "pizza": {"small": "cтандарт", "large": "большая"},
            "snack": {"small": "cтандарт", "large": "большая"},
            "drink": {"small": "0.5 литра", "large": "1 литр"},
            "cake": {"small": "cтандарт", "large": "большой"},
        }
        return sizes[self.category][size]

    @property
    def small_size_text(self):
        if (
            self.price_large
        ):  # чтобы не показывало надпись "стандарт" у продуктов с одним размером
            return self.get_size_text("small")
        else:
            return ""

    @property
    def large_size_text(self):
        return self.get_size_text("large")

    def get_size_price(self, size):
        if size == "large":
            return self.price_large
        elif size == "small":
            return self.price_small
        else:
            return 0

    @property
    def has_only_one_size(self):
        return self.price_large is None


class Order(Base):
    __tablename__ = "orders"
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_name: str = Column(String(50), nullable=False)
    phone: str = Column(String(9), nullable=False)
    address: str = Column(Text, nullable=False)
    additional_info: str = Column(String(200), nullable=True)
    amount: float = Column(Float, nullable=False, default=0)
    created_at: datetime = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    status: str = Column(String(20), nullable=False, default="pending")
    user = relationship("User", backref="orders")
    order_items = relationship(
        "OrderItem", backref="order", cascade="all, delete-orphan"
    )


    @property
    def created_at_local(self):
        return self.created_at + timedelta(hours=3)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: int = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    size = Column(String(10), nullable=False)
