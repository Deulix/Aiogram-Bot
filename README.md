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
cd Aiogram-Bot
```

3. **Настройте переменные окружения:**
```bash
cp .env.example .env
```

4. **Запустите через Docker Compose:**
```bash
docker-compose up -d
```

## 📁 Структура проекта
```bash
Aiogram-Bot/
├── app/
│   ├── handlers/          # Обработчики сообщений
│   ├── keyboards/         # Инлайн-клавиатуры   
│   └── __init__.py
├── database/
│   ├── redis_db.py        # Redis DB
│   ├── shop.db            # Volume базы данных sqlite  
│   └── sqlite_db.py       # Async SQLite DB
├── docker-compose.yml     # Docker конфигурация
├── Dockerfile             # Образ Docker
├── requirements.txt       # Зависимости Python
└── .env.example           # Пример переменных окружения
```

## ⚙️ Конфигурация
Перед запуском заполните .env файл:
```
BOT_TOKEN=your_bot_token_here # ваш токен от @botfather в telegram
ADMIN_ID=your_telegram_id # ваш id в telegram
REDIS_PORT=6379 # стандартный порт redis
REDIS_URL=redis://redis:6379/0 # URL вашего Redis
```

## 🛠️ Технологии
![Python 3.13](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
Python 3.13.5 - основной язык

Aiogram 3.21.0 - современный фреймворк для Telegram ботов

SQLAlchemy 2.0.43 - работа с базой данных

Redis - для хранения корзины клиента

Docker - контейнеризация приложения

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
- [ ] Задача выполнена
- [ ] Оплата
