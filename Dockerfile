FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright and psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browser
RUN playwright install --with-deps chromium

COPY . .

ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/pulse_ia

EXPOSE 8000
