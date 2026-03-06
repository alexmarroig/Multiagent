FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget curl gnupg \
&& rm -rf /var/lib/apt/lists/*

# Copy the entire monorepo to /app
COPY . /app

# resolve dependency file safely
RUN set -eux; \
    if [ -f /app/backend/requirements.txt ]; then \
        cp /app/backend/requirements.txt /tmp/requirements.txt; \
    else \
        cp /app/requirements.txt /tmp/requirements.txt; \
    fi; \
    pip install --no-cache-dir -r /tmp/requirements.txt

RUN playwright install chromium

# Set PYTHONPATH to include both the root and backend for monorepo support
ENV PYTHONPATH=/app:/app/backend

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
