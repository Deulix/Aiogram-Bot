## Project Overview
- **Purpose**: Telegram pizza ordering bot (Aiogram) with a lightweight FastAPI admin panel, SQLite/Redis backends.
- **Main subsystems**: Bot (`src/app/bot`), API (`src/app/api`), Database (`src/app/database`), Config & Logging (`src/app/config`).

## Architecture & Data Flow
- **Bot**: `src/app/bot/main.py` initializes `Bot`, `Dispatcher`, Redis and AsyncSQLiteDatabase, registers `routers`, and starts polling.
- **API**: `src/app/api/main.py` runs FastAPI; templates are under `src/app/api/templates`.
- **Database**: `src/app/database/sqlite_db.py` wraps async SQLAlchemy; use `AsyncSQLiteDatabase` for DB operations.
- **Redis**: `src/app/database/redis_db.py` exposes `init_redis()` used for cart state and short-lived keys.
- **DI**: Handlers accept `db: AsyncSQLiteDatabase` or `redis: Redis` to use pre-registered objects from `Dispatcher`.

## Conventions & Patterns
- **Routers**: Define a `Router()` instance (e.g., `navigation_router`) in `src/app/bot/handlers/*` and include it in `src/app/bot/main.py` routers list.
- **Callback_data**: Use underscore-separated strings (`add_{id}_small`); parse with `callback.data.split("_")`.
- **Keyboards**: Use `InlineKeyboardBuilder()` and return its markup with `.as_markup()`.
- **Cart keys**: Redis keys `cart:{user_id}` (hash) and `cart_amount:{user_id}` (string amount). Expiry set to 12 hours.
- **Admins**: `settings.ADMIN_ID` and `User.is_admin` determine access to admin actions.

## Developer Workflows
- **Docker**: `docker-compose up -d` starts Redis, Aiobot, FastAPI.
- **Local**: Fill `.env` and run `python -m src.app.bot.main` (bot) and `uvicorn src.app.api.main:app` (API).
- **Migrations**: `alembic revision --autogenerate -m "message"` then `alembic upgrade head`.

## Testing — How to write tests (practical guidance)
- **Test location & naming**: tests in `src/tests/`, files named `test_*.py`.
- **Minimal test runner**: Use `pytest` from project root: `pytest -q`.
- **Async tests**:
  - Two options:
    - Use `asyncio.run` inside a sync test (no extra deps) — see example in `src/tests/test_cart_service.py`.
    - Add `pytest-asyncio` (dev dep) and write `async def` tests with `@pytest.mark.asyncio`.
- **Mocking and fakes**:
  - Avoid hitting real Redis/DB in unit tests. Use small in-test fakes or `unittest.mock.AsyncMock`.
  - For DB integration tests, use a temporary SQLite DB or a test-specific environment.
- **Testing DI and handlers**:
  - Test handlers as functions by passing in fake `db`, `redis`, and `FSMContext` objects or by validating individual service units instead of full polling loop.
- **CI**: Add GitHub Actions to run `pytest` if you want automated runs on PRs.

## Example Tests
- Synchronous, model-only test (no DB): `src/tests/test_product_model.py` — instantiates `Product` and checks `get_size_price`, `has_only_small_size`, and size text.
- Async-style test for `Cart` using a `FakeRedis`: `src/tests/test_cart_service.py` uses `asyncio.run` to test `add_amount`, `sub_amount`, `increase_prod_count`, `delete_product`, and `clear` methods.

## Quick Examples (snippets)
- Run all tests:
```
pytest -q
```
- Add `pytest-asyncio` as dev dependency (recommended for async tests):
```
pip install pytest-asyncio
```
- Example of writing an async test with pytest-asyncio:
```python
import pytest

@pytest.mark.asyncio
async def test_async_cart():
    redis = FakeRedis()
    cart = Cart(user_id=1, redis=redis)
    await cart.add_amount(1.23)
    assert float(await cart.get_current_amount()) == 1.23
```

## Best Practices & Patterns
- Prefer unit tests that are independent of infrastructure by using fakes/mocks.
- For integration tests, run the stack in Docker Compose and keep tests idempotent (clean up DB/Redis state after run).
- Use `asyncio.run` if you prefer to not add `pytest-asyncio` to dev deps.

If you'd like, I can:
- Add `pytest-asyncio` to `pyproject.toml` dev deps and add a CI workflow to run tests.
- Add fixtures for a temporary SQLite DB or a `FakeRedis` fixture.
- Add a few more example tests covering DB functions and APIs.
