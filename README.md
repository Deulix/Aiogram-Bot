# 🤖 Aiogram Bot
Проект Telegram бота на Aiogram 3.21.0 клиентов и администраторов пиццерий

## 🚀 Быстрый старт

### Через Docker

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Deulix/Aiogram-Bot.git
```

2. **Перейдите в папку проекта:**
```bash
cd '.\Aiogram Bot\'
```

3. **Переименуйте env файл и настройте его (смотрите ниже):**
```bash
cp .env.example .env
```

4. **Запустите через Docker Compose:**
```bash
docker-compose up -d
```


## ⚙️ Конфигурация
Перед запуском заполните .env файл:
```python
BOT_TOKEN=your_bot_token # ваш токен от @botfather в telegram
ADMIN_ID=your_telegram_id # ваш id в telegram
REDIS_PORT=your_redis_port # стандартный порт redis (по умолчанию 6379)
REDIS_HOST=your_redis_host # стандартный хост redis (по умолчанию "redis")
DATABASE_URL="sqlite+aiosqlite:///src/app/database/shop.db" # ваш путь к базе данных, указан по умолчанию
TEST_PAYMENT_KEY=your_redis_port # ваш токен (ключ) для оплаты 
MAPS_API_KEY=your_redis_port # ваш токен (ключ) от Yandex JavaScript API и HTTP Геокодер
```
## 📁 Структура проекта
```bash
Aiogram-Bot/

├── alembic
│   ├── versions
│   │   └── ...
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── src
│   ├── app
│   │   ├── bot
│   │   │   ├── handlers.py
│   │   │   ├── keyboards.py
│   │   │   └── payments.py
│   │   ├── config
│   │   │   └── settings.py
│   │   ├── database
│   │   │   ├── models.py
│   │   │   ├── redis_db.py
│   │   │   ├── shop.db
│   │   │   ├── sqlite_db_dump.sql
│   │   │   └── sqlite_db.py
│   │   └── main.py
│   └── tests
│       └── ...
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── docker-compose.yml
├── Dockerfile.dev
├── Dockerfile.prod
├── pyproject.toml
├── pytest.ini
├── README.md
└── uv.lock
```

## 🛠️ Технологии
![](https://img.shields.io/badge/python_3.13.5-blue?logo=python&logoColor=yellow) - основной язык

![](https://img.shields.io/badge/aiogram_3.21.0-blue?logo=telegram&logoColor=white) - современный фреймворк для Telegram ботов

![](https://img.shields.io/badge/SQLAlchemy_2.x.x-orange?logo=sqlalchemy&logoColor=white) - работа с базой данных

![](https://img.shields.io/badge/Redis_7-red?logo=redis&logoColor=white) - для хранения корзины клиента

![](https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=white) - контейнеризация приложения

![](https://img.shields.io/badge/Alembic-blue) - миграции баз данных

## 📈 Особенности
- Готовая структура для масштабирования

- Поддержка Docker из коробки

- Инлайн-клавиатуры и меню

- Возможность в будущем кэшировать через Redis

- Асинхронная архитектура

- Легкая кастомизация

## TODO
- [x] CRUD для заказов, продуктов
- [x] Корзина Redis
- [x] Админка через Telegram
- [x] Оплата (тестовая)
- [ ] Тесты
- [ ] Админка через FastAPI
- [ ] PostgreSQL

