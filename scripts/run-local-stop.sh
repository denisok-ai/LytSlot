#!/usr/bin/env bash
# @file: run-local-stop.sh
# @description: Остановка API и Worker, запущенных через run-local.sh. Опционально — остановка контейнеров БД/Redis.
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "[run-local-stop] Остановка процессов, запущенных run-local.sh..."

if [ -f .run-local.api.pid ]; then
  PID=$(cat .run-local.api.pid)
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    echo "[run-local-stop] API (PID $PID) остановлен."
  fi
  rm -f .run-local.api.pid
fi

if [ -f .run-local.worker.pid ]; then
  PID=$(cat .run-local.worker.pid)
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    echo "[run-local-stop] Worker (PID $PID) остановлен."
  fi
  rm -f .run-local.worker.pid
fi

# Опционально: остановить контейнеры БД и Redis
if [ "${1:-}" = "--all" ]; then
  if command -v podman-compose &>/dev/null; then
    echo "[run-local-stop] Остановка контейнеров (podman-compose)..."
    podman-compose -f infra/docker-compose.yml stop db redis 2>/dev/null || true
  elif command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    echo "[run-local-stop] Остановка контейнеров (docker compose)..."
    docker compose -f infra/docker-compose.yml stop db redis 2>/dev/null || true
  fi
  echo "[run-local-stop] Контейнеры db и redis остановлены."
fi

echo "[run-local-stop] Готово. Web останавливается по Ctrl+C в терминале, где запущен run-local.sh."
