# 🤖 Aiogram Bot
Проект Telegram бота на Aiogram 3.x для пиццерии

## 🚀 Быстрый старт

### Через Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Deulix/Aiogram-Bot.git
cd Aiogram-Bot
```
2. **Настройте переменные окружения:**
```bash
cp .env.example .env
```

3. **Запустите через Docker Compose:**
```bash
docker-compose up -d
```
Aiogram-Bot/
├── app/
│   ├── handlers/          # 📋 Обработчики сообщений
│   ├── keyboards/         # ⌨️ Инлайн-клавиатуры   
│   └── __init__.py
├── docker-compose.yml    # 🐳 Docker конфигурация
├── Dockerfile           # 🐳 Образ Docker
├── requirements.txt     # 📦 Зависимости Python
└── .env.example        # 🔧 Пример переменных окружения

BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
DATABASE_URL=sqlite+aiosqlite:///shop.db
REDIS_URL=redis://redis:6379/0

🛠️ Технологии
Python 3.11+ - основной язык

Aiogram 3.x - современный фреймворк для Telegram ботов

SQLAlchemy 2.0 - работа с базой данных

Redis - кэширование и FSM

Docker - контейнеризация приложения

📈 Особенности
✅ Готовая структура для масштабирования

✅ Поддержка Docker из коробки

✅ Инлайн-клавиатуры и меню

✅ Кэширование через Redis

✅ Асинхронная архитектура

✅ Легкая кастомизация

🐛 Разработка
Для разработки без Docker:

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m app