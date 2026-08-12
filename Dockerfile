FROM python:3.11-slim

WORKDIR /app

# System deps (psycopg2/asyncpg sometimes need these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects $PORT at runtime — don't hardcode 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT