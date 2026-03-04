FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget curl gnupg \
&& rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r backend/requirements.txt

RUN playwright install chromium

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
