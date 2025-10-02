FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    rm -rf /root/.cache/pip/ &&\
    python -m pip install -r requirements.txt && \
    apt-get update &&\
    apt-get install sqlite3 -y

WORKDIR /bot_app

COPY . .

CMD [ "python", "main.py" ]