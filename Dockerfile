FROM python:3.11-slim as builder

WORKDIR /app

# Установка зависимостей только для сборки
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements.txt сначала
COPY requirements.txt .

# Устанавливаем зависимости в отдельную папку
RUN pip install --user --no-cache-dir -r requirements.txt

# Основной этап
FROM python:3.11-slim as base

# Копируем только установленные зависимости
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/requirements.txt .

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y \
    libpq5 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Добавляем pip-пакеты в PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /app

# Копируем остальные файлы проекта
COPY . .

FROM base AS admin_panel

WORKDIR /admin_panel

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

FROM base AS bot

WORKDIR /bot

CMD ["python", "-m", "main.py"]