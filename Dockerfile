FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update &&\
    apt-get install --no-install-recommends sqlite3 -y &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /pzz_app

COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install --system -r pyproject.toml

COPY . .

CMD [ "echo", "all commands in docker-compose"]