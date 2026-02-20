#!/usr/bin/env bash
# @file: seed-db.sh
# @description: Наполнение БД тестовыми данными (tenant, каналы, слоты, заказы, просмотры, API-ключ).
# @dependencies: миграции применены, venv с pip install -e .
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
[ -n "$DATABASE_URL_SYNC" ] || export DATABASE_URL_SYNC="postgresql://lytslot:lytslot@localhost:5432/lytslot"
if [ -x ".venv/bin/python3" ]; then
  PYTHON=".venv/bin/python3"
else
  PYTHON="python3"
fi
if ! "$PYTHON" -c "import db.seed" 2>/dev/null; then
  echo "Ошибка: не найден модуль db. Запустите из корня проекта с venv: source .venv/bin/activate; pip install -e ."
  exit 1
fi
echo "=== Тестовые данные (demo tenant telegram_id=123456789) ==="
"$PYTHON" -m db.seed
if [ "$1" = "extra" ]; then
  echo "=== Дополнительные слоты и просмотры ==="
  "$PYTHON" -m db.seed extra
fi
echo "=== Готово. Войдите в кабинет с telegram_id=123456789 (Режим разработки на /login). ==="
