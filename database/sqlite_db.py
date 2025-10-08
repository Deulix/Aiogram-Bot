import os
from datetime import datetime

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
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )
    is_admin = Column(Boolean, default=False, server_default=text("0"), nullable=False)


class Product(Base):
    __tablename__ = "products"
    id: int = Column(Integer, primary_key=True, index=True)
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
        return self.get_size_text("small")

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

    def has_only_one_size(self):
        return self.price_large is None


class Order(Base):
    __tablename__ = "orders"
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_name: str = Column(String(50), nullable=False)
    address: str = Column(Text, nullable=False)
    amount: float = Column(Float, nullable=False)
    created_at: datetime = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="orders")
    order_items = relationship(
        "OrderItem", backref="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    id: int = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    size = Column(String(10), nullable=False)


class AsyncSQLiteDatabase:
    def __init__(self, db_path: str = "database/shop.db"):
        import os

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        self.AsyncSession = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(f"SQLITE CONNECTED")
        return self

    async def add_user(
        self, user_id: int, username: str, first_name: str, last_name: str | None
    ):
        async with self.AsyncSession() as session:
            try:
                new_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=(user_id == int(os.getenv("ADMIN_ID"))),
                )

                session.add(new_user)
                await session.commit()

            except Exception as e:
                await session.rollback()
                print(f"Error adding user: {e}")
        return new_user

    from aiogram.types import User as TgUser

    async def update_user(self, tg_user: TgUser):

        async with self.AsyncSession() as session:
            result = await session.execute(
                select(User).where(User.user_id == tg_user.id)
            )
            db_user = result.scalar_one_or_none()
            try:
                if (
                    db_user.username != tg_user.username
                    or db_user.first_name != tg_user.first_name
                    or db_user.last_name != tg_user.last_name
                ):

                    db_user.username = tg_user.username
                    db_user.first_name = tg_user.first_name
                    db_user.last_name = tg_user.last_name

                if tg_user.id == int(os.getenv("ADMIN_ID")):
                    db_user.is_admin = True

                session.add(db_user)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Error adding user: {e}")
            return db_user

    async def add_product(
        self,
        name: str,
        price_small: float,
        price_large: float,
        category: str,
        category_rus: str,
        description: str | None,
        ingredients: str | None,
        nutrition: str | None,
        emoji: str,
    ):
        async with self.AsyncSession() as session:
            try:
                product = Product(
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
                session.add(product)
                await session.commit()

            except Exception as e:
                await session.rollback()
                print(f"Error adding product: {e}")

    async def add_order(self, user_id, list_cart_items):
        async with self.AsyncSession() as session:
            order = Order(user_id=user_id, amount=0)
            total_amount = 0
            session.add(order)
            await session.flush()
            for item in list_cart_items:
                product, size, quantity = item
                product: Product
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.get_size_price(size) * quantity,
                    size=size,
                )
                total_amount += order_item.price
                session.add(order_item)
            order.amount = total_amount
            await session.commit()

    async def get_products(self):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product))
            category_order = ["pizza", "snack", "drink", "cake"]
            return sorted(
                result.scalars().all(), key=lambda x: category_order.index(x.category)
            )

    async def get_orders(self, user_id):
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(Order).where(Order.user_id == user_id)
            )
            return sorted(result.scalars().all(), key=lambda x: x.created_at)
        
    async def get_order_by_id(self, order_id):
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            return result.scalar_one_or_none()

    async def get_product_by_id(self, id):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product).where(Product.id == id))
            return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id):
        async with self.AsyncSession() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()

    async def get_products_by_category(self, category: str):
        async with self.AsyncSession() as session:
            stmt = select(Product).where(Product.category == category)
            if category == "snack":
                stmt = select(Product).where(Product.category.in_([category, "snack"]))
            result = await session.execute(stmt)
            return result.scalars().all()

    async def check_connection(self):
        try:
            async with self.AsyncSession() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    async def delete_product(self, id):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product).where(Product.id == id))
            product = result.scalar_one_or_none()
            await session.delete(product)
            await session.commit()


async def init_async_sqlite():
    return await AsyncSQLiteDatabase().init_db()
