# 🤖 Aiogram Bot
Проект Telegram бота на Aiogram 3.21.0 клиентов и администраторов пиццерий

## 🚀 Быстрый старт

### Через Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Deulix/Aiogram-Bot.git
```

2. **Перейдите в папку проекта:**
```bash
cd '.\Aiogram Bot\'
```

3. **Настройте переменные окружения:**
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
BOT_TOKEN=your_bot_token # Токен бота, полученный у BotFather
ADMIN_ID=your_id # Ваш Telegram ID (нельзя лишить администрирования)
REDIS_PORT=6379 # Стандартный порт redis
REDIS_HOST="redis" # Стандартный хост redis
DATABASE_URL="sqlite+aiosqlite:///your_db_path/your_db_name.db" # Путь к вашей async sqlite БД
TEST_PAYMENT_KEY=your_test_payment_key # Тестовый ключ оплаты, полученный у BotFather
MAPS_API_KEY=your_yandex_geocoder_api_key # API ключ для поиска улиц, полученный у Yandex
```
## 📁 Структура проекта
```bash
Aiogram-Bot/
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── src/
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── README
│   │   └── script.py.mako
│   ├── app/
│   │   ├── bot/
│   │   │   ├── handlers.py
│   │   │   ├── keyboards.py
│   │   │   └── payments.py
│   │   ├── database/
│   │   │   ├── models.py
│   │   │   ├── redis_db.py
│   │   │   ├── shop.db
│   │   │   └── sqlite_db.py
│   │   └── main.py
│   └── tests/
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
├── README.md
└── requirements.txt
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

## 🐛 Разработка
Для разработки без Docker:
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r requirements.txt
python -m app
```

## TODO
- [x] CRUD для заказов, продуктов
- [x] Корзина Redis
- [ ] Тесты
- [ ] Оплата (тестовая)
- [ ] PostgreSQL
