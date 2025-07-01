FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update || true && \
    apt-get install -y --no-install-recommends gnupg && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0xA1BCEDF1FE77E8CA && \
    apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim as base

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/requirements.txt .

RUN apt-get update && apt-get install -y \
    libpq5 \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /app

COPY . .

FROM base AS admin_panel

WORKDIR /admin_panel

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

FROM base AS bot

WORKDIR /bot

RUN apt-get update && apt-get install -y wget gnupg && \
    apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxrandr2 libgbm1 libxdamage1 libxfixes3 \
        libxrender1 libxcursor1 libasound2 libpangocairo-1.0-0 libgtk-3-0 libx11-xcb1 libxcb1 libxext6 libxi6 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN playwright install --with-deps

CMD ["python", "-m", "main.py"]
