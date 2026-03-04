FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget curl gnupg && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./pyproject.toml
COPY agentos ./agentos

RUN pip install --no-cache-dir -e .
RUN playwright install chromium

CMD ["sh", "-c", "uvicorn agentos.backend.main:app --host 0.0.0.0 --port ${PORT}"]
