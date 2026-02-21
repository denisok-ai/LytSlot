#!/usr/bin/env bash
# @file: run-worker.sh
# @description: Запуск Celery worker (очереди default, publish, notifications, analytics).
# @dependencies: Redis, pip install -e . (в venv)
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
if [ -x ".venv/bin/celery" ]; then
  CELERY=".venv/bin/celery"
else
  CELERY="celery"
fi
if ! "$CELERY" --help &>/dev/null; then
  echo "Ошибка: celery не найден. Активируйте venv и установите зависимости:"
  echo "  source .venv/bin/activate"
  echo "  pip install -e ."
  exit 1
fi
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
exec "$CELERY" -A services.worker.celery_app worker -l info -Q default,publish,notifications,analytics
