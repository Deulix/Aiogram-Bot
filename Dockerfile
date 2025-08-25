FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python -m pip install -r requirements.txt && \
    python -m pip install --upgrade pip

WORKDIR /bot_app

COPY . .

CMD [ "python", "main.py" ]