FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps


COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

FROM base AS admin_panel

WORKDIR /admin_panel

COPY admin_panel/ /admin_panel/

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

FROM base AS bot

WORKDIR /bot

COPY bot/ /bot/

CMD ["python", "-m", "main.py"]