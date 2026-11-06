#!/bin/sh
set -e

# Worker do Celery em segundo plano
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1 &

# API em primeiro plano (é o processo principal do container)
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"