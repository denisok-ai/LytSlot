#!/usr/bin/env bash
# @file: docker-up-full.sh
# @description: Автономный запуск стека на сервере (Docker или Podman). Сборка, up -d, ожидание API, миграции.
#   По умолчанию — полный стек (api, web, db, redis, bot, worker). Флаг --minimal — только api, web, db, redis.
# @dependencies: docker compose или podman-compose
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
COMPOSE_FILE="infra/docker-compose.yml"
PROFILE_ARG="--profile full"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --minimal) PROFILE_ARG="" ; shift ;;
    --full)    PROFILE_ARG="--profile full" ; shift ;;
    *)         echo "Использование: $0 [--minimal|--full]. По умолчанию: полный стек."; exit 1 ;;
  esac
done

# Автономность: если .env нет — создаём из .env.example (для быстрого старта; в продакшене задайте JWT_SECRET и BOT_TOKEN)
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env из .env.example. Для продакшена отредактируйте .env (JWT_SECRET, BOT_TOKEN) и при необходимости перезапустите."
fi

# Определяем команду: docker compose или podman-compose
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v podman-compose &>/dev/null; then
  COMPOSE="podman-compose"
else
  echo "Ошибка: нужен Docker (docker compose) или Podman (podman-compose)."
  exit 1
fi

echo "=== LytSlot: запуск стека ($COMPOSE) ==="
$COMPOSE -f "$COMPOSE_FILE" build
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG up -d

echo "Ожидание готовности API (до 60 с)..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/ready &>/dev/null; then
    echo "API готов."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Предупреждение: API не ответил /ready за 60 с. Проверьте логи: $COMPOSE -f $COMPOSE_FILE logs api"
    exit 1
  fi
  sleep 2
done

# Миграции в контейнере API (-T — без TTY для неинтерактивного запуска)
echo "=== Применение миграций и seed в контейнере API ==="
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG exec -T api python -m alembic upgrade head
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG exec -T api python -m db.seed
echo "=== Готово ==="

echo ""
echo "Стек запущен. Контейнеры перезапускаются автоматически (restart: unless-stopped)."
echo "  API:    http://localhost:8000/docs"
echo "  Web:    http://localhost:3000"
echo "  Health: http://localhost:8000/ready"
