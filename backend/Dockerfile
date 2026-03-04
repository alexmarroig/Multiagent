FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget curl gnupg \
&& rm -rf /var/lib/apt/lists/*

# copy repository first so we can support both monorepo and single-service layouts
COPY . /app

# resolve dependency file safely (backend/requirements.txt preferred, root fallback)
RUN set -eux; \
    if [ -f /app/backend/requirements.txt ]; then \
        cp /app/backend/requirements.txt /tmp/requirements.txt; \
    elif [ -f /app/requirements.txt ]; then \
        cp /app/requirements.txt /tmp/requirements.txt; \
    else \
        echo "No requirements.txt found at /app/backend/requirements.txt or /app/requirements.txt"; \
        exit 1; \
    fi; \
    pip install --no-cache-dir -r /tmp/requirements.txt

RUN playwright install chromium

ENV PYTHONPATH=/app/backend:/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
