FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget curl gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY backend/ ./

# Copy required root modules
COPY governance ./governance
COPY core ./core

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
