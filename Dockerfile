FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install uv &&\
    apt-get update &&\
    apt-get install --no-install-recommends sqlite3 -y &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /bot_app

COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install . --system

COPY . .

CMD [ "python", "-m", "src.app.main" ]