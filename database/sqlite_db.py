from datetime import datetime
import os
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
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
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    callback_name: str = Column(String(255), nullable=False)
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

    def __get_size_text(self):
        match self.category:
            case "pizza":
                size_text = {"small": "cтандарт", "large": "большая"}
            case "snack":
                size_text = {"small": "cтандарт", "large": "большая"}
            case "drink":
                size_text = {"small": "0.5 литра", "large": "1 литр"}
            case "cake":
                size_text = {"small": "cтандарт", "large": "большой"}
        return size_text

    @property
    def small_size_text(self):
        if self.price_large:
            return self.__get_size_text()["small"]
        else:
            return ""

    @property
    def large_size_text(self):
        return self.__get_size_text()["large"]

    def get_current_size_text(self, size):
        if self.price_large:
            return self.__get_size_text()[size]
        else:
            return ""

    def get_current_price(self, size):
        if size == "large":
            return self.price_large
        elif size == "small":
            return self.price_small
        else:
            return 0

    def has_only_one_size(self):
        return self.price_large is None


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
                script = select(User).where(User.user_id == user_id)
                result = await session.execute(script)
                existing_user = result.scalar_one_or_none()
                if existing_user:
                    if (
                        existing_user.username != username
                        or existing_user.first_name != first_name
                        or existing_user.last_name != last_name
                    ):

                        existing_user.username = username
                        existing_user.first_name = first_name
                        existing_user.last_name = last_name

                    if user_id == os.getenv("ADMIN_ID"):
                        existing_user.is_admin = True
                else:
                    new_user = User(
                        user_id=user_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        is_admin=(user_id == os.getenv("ADMIN_ID")),
                    )
                    session.add(new_user)

                await session.commit()

            except Exception as e:
                await session.rollback()
                print(f"Error adding user: {e}")

    async def add_product(
        self,
        name: str,
        callback_name: str,
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
                    callback_name=callback_name,
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

    async def get_products(self):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product))
            category_order = ["pizza", "snack", "drink", "cake"]
            return sorted(
                result.scalars().all(), key=lambda x: category_order.index(x.category)
            )

    async def get_product_by_callback_name(self, callback_name):
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(Product).where(Product.callback_name == callback_name)
            )
            return result.scalar()

    async def get_user_by_id(self, user_id):
        async with self.AsyncSession() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar()

    async def get_products_by_category(self, category: int):
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(Product).where(Product.category == category)
            )
            return result.scalars().all()

    async def check_connection(self):
        try:
            async with self.AsyncSession() as session:
                result = await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False


async def init_async_sqlite():
    return await AsyncSQLiteDatabase().init_db()
