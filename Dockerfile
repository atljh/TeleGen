FROM python:3.11-slim-bookworm as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm as base

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

FROM base AS bot

WORKDIR /bot

RUN apt-get update && apt-get install -y \
    wget \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxrandr2 libgbm1 \
    libxdamage1 libxfixes3 libxrender1 libxcursor1 libasound2 libpangocairo-1.0-0 \
    libgtk-3-0 libx11-xcb1 libxcb1 libxext6 libxi6 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN playwright install --with-deps

CMD ["python", "-m", "main"]