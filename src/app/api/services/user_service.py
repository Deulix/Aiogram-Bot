from src.app.database.models import User
from src.app.database.sqlite_db import AsyncSQLiteDatabase


async def get_users(db: AsyncSQLiteDatabase) -> list[User]:
    users = await db.get_users()
    if not users:
        return []
    return users


async def get_user_by_id(db: AsyncSQLiteDatabase, user_id: int) -> User | None:
    return await db.get_user_by_id(user_id)
