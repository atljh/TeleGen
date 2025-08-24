FROM python:3.11-slim-bookworm as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --user --no-cache-dir .[prod,scraping]

FROM python:3.11-slim-bookworm as base

RUN groupadd -r app && useradd -r -g app app

COPY --from=builder /root/.local /home/app/.local
COPY --from=builder /app/pyproject.toml .

RUN apt-get update && apt-get install -y \
    libpq5 \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY --chown=app:app . .

FROM base AS admin_panel

USER app
WORKDIR /app/admin_panel

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync"]

FROM base AS bot

# RUN apt-get update && apt-get install -y \
#     chromium \
#     chromium-driver \
#     wget \
#     libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxrandr2 libgbm1 \
#     libxdamage1 libxfixes3 libxrender1 libxcursor1 libasound2 libpangocairo-1.0-0 \
#     libgtk-3-0 libx11-xcb1 libxcb1 libxext6 libxi6 libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --headless"

USER app
WORKDIR /app/bot

CMD ["python", "-m", "main"]

FROM base AS celery_beat

USER app
WORKDIR /app

CMD ["celery", "-A", "core", "beat", "--loglevel=info"]

FROM base AS celery_worker

USER app
WORKDIR /app

CMD ["celery", "-A", "core", "worker", "--loglevel=info"]