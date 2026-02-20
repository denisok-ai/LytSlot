#!/usr/bin/env bash
# @file: run-api.sh
# @description: Запуск FastAPI (uvicorn). Использует .venv, если есть.
# @dependencies: pip install -e . (в venv)
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
if [ -x ".venv/bin/python3" ]; then
  PYTHON=".venv/bin/python3"
  UVICORN=".venv/bin/uvicorn"
else
  PYTHON="python3"
  UVICORN="uvicorn"
fi
if ! "$PYTHON" -c "import fastapi" 2>/dev/null; then
  echo "Ошибка: fastapi не установлен. Активируйте venv и установите зависимости:"
  echo "  source .venv/bin/activate"
  echo "  pip install -e ."
  echo "Или создайте venv: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  exit 1
fi
exec "$UVICORN" services.api.main:app --reload --host 0.0.0.0 --port 8000
