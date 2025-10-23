import os

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from .models import User, Product, Order, OrderItem

Base = declarative_base()


class AsyncSQLiteDatabase:
    def __init__(self, db_path: str = os.getenv("DATABASE_URL")):
        self.engine = create_async_engine(db_path)
        self.AsyncSession = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.create_all) # нужно при отсутствии alembic
            await self.check_connection()
        print(f"SQLITE CONNECTED")
        return self

    async def add_user(
        self, user_id: int, username: str, first_name: str, last_name: str | None
    ):
        async with self.AsyncSession() as session:
            try:
                new_user = User(
                    id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=(id == int(os.getenv("ADMIN_ID"))),
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
            stmt = select(User).where(User.id == tg_user.id)
            result = await session.execute(stmt)
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

    async def add_order(
        self,
        user_id,
        list_cart_items,
        client_name,
        phone,
        address_text,
        additional_info,
    ):
        async with self.AsyncSession() as session:
            order = Order(
                user_id=user_id,
                client_name=client_name,
                phone=phone,
                address=address_text,
                additional_info=additional_info,
            )
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
                    price=product.get_size_price(size),
                    size=size,
                )
                total_amount += order_item.price * order_item.quantity
                session.add(order_item)
            order.amount = total_amount
            await session.commit()
            return order

    async def toggle_admin(self, user_id):
        async with self.AsyncSession() as session:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            value = not user.is_admin
            user.is_admin = value
            await session.commit()
            return value

    async def get_admins(self):
        async with self.AsyncSession() as session:
            stmt = select(User).where(User.is_admin == True)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_products(self):
        async with self.AsyncSession() as session:
            result = await session.execute(select(Product))
            category_order = ["pizza", "snack", "cake", "drink"]
            return sorted(
                result.scalars().all(),
                key=lambda x: (category_order.index(x.category), x.name.lower()),
            )

    async def get_orders(self, user_id):
        async with self.AsyncSession() as session:
            stmt = select(Order).where(Order.user_id == user_id)
            result = await session.execute(stmt)
            return sorted(result.scalars().all(), key=lambda x: x.created_at)

    async def get_order_items(self, order_id):
        async with self.AsyncSession() as session:
            stmt = select(OrderItem).where(OrderItem.order_id == order_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_order_by_id(self, order_id):
        async with self.AsyncSession() as session:
            result = await session.get(Order, order_id)
            return result

    async def get_product_by_id(self, product_id):
        async with self.AsyncSession() as session:
            result = await session.get(Product, product_id)
            return result

    async def get_user_by_id(self, user_id):
        async with self.AsyncSession() as session:
            result = await session.get(User, user_id)
            return result

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

    async def delete_product(self, product_id):
        async with self.AsyncSession() as session:
            product = await self.get_product_by_id(product_id)
            await session.delete(product)
            await session.commit()


async def init_async_sqlite():
    return await AsyncSQLiteDatabase().init_db()
