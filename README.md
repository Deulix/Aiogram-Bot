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


## ⚙️ Конфигурация
Перед запуском заполните .env файл:
```python
BOT_TOKEN="your_bot_token_here" # ваш токен от @botfather в telegram
ADMIN_ID="your_telegram_id" # ваш id в telegram
REDIS_PORT=6379 # стандартный порт redis
REDIS_URL="redis://redis:6379/0" # URL вашего Redis
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

## 🛠️ Технологии
![](https://img.shields.io/badge/python_3.13.5-blue?logo=python&logoColor=yellow) - основной язык

![](https://img.shields.io/badge/aiogram_3.21.0-blue?logo=telegram&logoColor=white) - современный фреймворк для Telegram ботов

![](https://img.shields.io/badge/SQLAlchemy_2.0.43-orange) - работа с базой данных

![](https://img.shields.io/badge/Redis_7-red) - для хранения корзины клиента

![](https://img.shields.io/badge/Docker-blue) - контейнеризация приложения

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
- [ ] PostgreSQL
- [ ] Тесты
- [ ] Оплата (тестовая)
