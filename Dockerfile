FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM base as admin_panel

WORKDIR /admin_panel

COPY admin_panel/ /admin_panel/

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

FROM base as bot

WORKDIR /bot

COPY bot/ /bot/

CMD ["python", "main.py"]