#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations..."
  MAX_RETRIES=10
  RETRY=0
  until alembic upgrade head; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
      echo "ERROR: Alembic failed after $MAX_RETRIES attempts. Exiting."
      exit 1
    fi
    echo "Migration failed (attempt $RETRY/$MAX_RETRIES). Retrying in 3s..."
    sleep 3
  done
else
  echo "WARNING: DATABASE_URL not set, skipping migrations."
fi

echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8080
