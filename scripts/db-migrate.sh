#!/usr/bin/env bash
# @file: db-migrate.sh
# @description: Применить миграции и seed (один раз после поднятия БД). Использует .venv если есть.
# @dependencies: venv с pip install -e .
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
[ -n "$DATABASE_URL_SYNC" ] || export DATABASE_URL_SYNC="postgresql://lytslot:lytslot@localhost:5432/lytslot"
if [ -x ".venv/bin/python3" ]; then
  PYTHON=".venv/bin/python3"
else
  PYTHON="python3"
fi
if ! "$PYTHON" -c "import alembic" 2>/dev/null; then
  echo "Ошибка: alembic не установлен."
  echo "  Вариант 1 — venv: sudo apt install python3.12-venv; rm -rf .venv; python3 -m venv .venv; source .venv/bin/activate; pip install -e ."
  echo "  Вариант 2 — миграции в контейнере (если API уже запущен): ./scripts/db-migrate-in-container.sh"
  exit 1
fi
echo "=== Миграции (DATABASE_URL_SYNC=$DATABASE_URL_SYNC) ==="
"$PYTHON" -m alembic upgrade head
echo "=== Seed ==="
"$PYTHON" -m db.seed
echo "=== Готово ==="
