# Development Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (OCR + utils)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./src ./src
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

EXPOSE 8080

# Development: hot-reload enabled
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
