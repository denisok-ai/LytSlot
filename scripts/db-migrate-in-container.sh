#!/usr/bin/env bash
# @file: db-migrate-in-container.sh
# @description: Применить миграции и seed внутри контейнера API (не нужен venv на хосте).
# @dependencies: podman, запущенный контейнер infra_api_1
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
CONTAINER="${1:-infra_api_1}"
if ! podman inspect "$CONTAINER" &>/dev/null; then
  echo "Контейнер $CONTAINER не найден. Сначала поднимите стек: ./scripts/podman-up.sh"
  exit 1
fi
echo "=== Миграции и seed в контейнере $CONTAINER ==="
podman exec "$CONTAINER" python -m alembic upgrade head
podman exec "$CONTAINER" python -m db.seed
echo "=== Готово ==="
