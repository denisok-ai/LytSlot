#!/usr/bin/env bash
# @file: podman-up-db-redis.sh
# @description: Запуск только PostgreSQL и Redis через Podman (для локальной разработки: API/миграции на хосте).
# @dependencies: podman-compose
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
echo "=== Запуск db и redis (podman-compose) ==="
podman-compose -f infra/docker-compose.yml up -d db redis
echo "=== Готово. PostgreSQL: localhost:5432, Redis: localhost:6379 ==="
echo "Дальше: export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot && ./scripts/db-migrate.sh"
