from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    select,
    text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
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


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    size = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=func.now(),
        nullable=False,
    )


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
        print(f"Была создана AsyncSQLite база данных: database/shop.db")
        return self

    async def add_user(
        self, user_id: int, username: str, first_name: str, last_name: str | None
    ):
        async with self.AsyncSession() as session:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()

    async def get_products(self):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product))
            return result.scalars().all()

    async def get_product(self, product_id: int):
        async with self.AsyncSession() as session:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            return result.scalar()

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
