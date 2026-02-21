#!/usr/bin/env bash
# @file: run-local.sh
# @description: Один скрипт — автономный локальный запуск: БД, Redis, миграции, API (в фоне), при необходимости Worker, Web (в текущем терминале). Без зависимости от удалённого сервера.
# @dependencies: Podman или Docker, venv с pip install -e ., Node.js для frontend
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
export DATABASE_URL_SYNC="${DATABASE_URL_SYNC:-postgresql://lytslot:lytslot@localhost:5432/lytslot}"

# ---------- 1. CRLF и .env ----------
for sh in scripts/local-preflight.sh scripts/db-migrate.sh scripts/seed-db.sh scripts/run-api.sh scripts/run-worker.sh scripts/podman-up-db-redis.sh; do
  [ -f "$sh" ] && grep -q $'\r' "$sh" 2>/dev/null && sed -i 's/\r$//' "$sh"
done
[ ! -f .env ] && cp .env.example .env && echo "[run-local] Создан .env из .env.example"

# ---------- 2. venv ----------
if [ ! -x .venv/bin/python3 ]; then
  echo "[run-local] Ошибка: нужен venv. Выполните: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  exit 1
fi
.venv/bin/python3 -c "import fastapi, alembic" 2>/dev/null || {
  echo "[run-local] Ошибка: установите зависимости: source .venv/bin/activate && pip install -e ."
  exit 1
}

# ---------- 3. Compose: Podman или Docker ----------
COMPOSE_CMD=""
if command -v podman-compose &>/dev/null; then
  COMPOSE_CMD="podman-compose -f infra/docker-compose.yml"
elif command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
  COMPOSE_CMD="docker compose -f infra/docker-compose.yml"
else
  echo "[run-local] Ошибка: нужен podman-compose или docker compose"
  exit 1
fi

# ---------- 4. Запуск БД и Redis ----------
echo "[run-local] Запуск PostgreSQL и Redis..."
$COMPOSE_CMD up -d db redis 2>/dev/null || true

# ---------- 5. Ожидание PostgreSQL (до 60 с) ----------
echo "[run-local] Ожидание готовности PostgreSQL..."
for i in $(seq 1 30); do
  if .venv/bin/python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
  s.connect(('127.0.0.1', 5432))
  s.close()
  exit(0)
except Exception:
  exit(1)
" 2>/dev/null; then
    echo "[run-local] PostgreSQL доступен."
    break
  fi
  [ "$i" -eq 30 ] && { echo "[run-local] PostgreSQL не ответил за 60 с. Проверьте: \$COMPOSE_CMD ps"; exit 1; }
  sleep 2
done

# ---------- 6. Миграции и seed ----------
echo "[run-local] Миграции и тестовые данные..."
./scripts/db-migrate.sh

# ---------- 7. API в фоне ----------
API_PID_FILE="$ROOT/.run-local.api.pid"
if [ -f "$API_PID_FILE" ]; then
  OLD_PID=$(cat "$API_PID_FILE")
  kill -0 "$OLD_PID" 2>/dev/null && { echo "[run-local] API уже запущен (PID $OLD_PID). Остановите: kill $OLD_PID"; } || rm -f "$API_PID_FILE"
fi
if [ ! -f "$API_PID_FILE" ] || ! kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
  echo "[run-local] Запуск API в фоне..."
  cd "$ROOT"
  nohup .venv/bin/uvicorn services.api.main:app --host 0.0.0.0 --port 8000 >> .run-local.api.log 2>&1 &
  echo $! > "$API_PID_FILE"
  cd - >/dev/null
fi

# ---------- 8. Ожидание /health (до 30 с) ----------
echo "[run-local] Ожидание API..."
for i in $(seq 1 15); do
  if .venv/bin/python3 -c "
import urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; then
    echo "[run-local] API отвечает на /health"
    break
  fi
  [ "$i" -eq 15 ] && { echo "[run-local] API не ответил. Проверьте логи."; exit 1; }
  sleep 2
done

# ---------- 9. Worker в фоне (если задан CELERY_BROKER_URL или REDIS_URL) ----------
WORKER_PID_FILE="$ROOT/.run-local.worker.pid"
[ -f "$ROOT/.env" ] && set -a && source "$ROOT/.env" 2>/dev/null && set +a || true
if [ -n "${CELERY_BROKER_URL:-}" ] || [ -n "${REDIS_URL:-}" ]; then
  if [ -f "$WORKER_PID_FILE" ]; then
    OLD_PID=$(cat "$WORKER_PID_FILE")
    kill -0 "$OLD_PID" 2>/dev/null && true || rm -f "$WORKER_PID_FILE"
  fi
  if [ ! -f "$WORKER_PID_FILE" ] || ! kill -0 "$(cat "$WORKER_PID_FILE")" 2>/dev/null; then
    echo "[run-local] Запуск Worker в фоне..."
    cd "$ROOT"
    export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
    nohup .venv/bin/celery -A services.worker.celery_app worker -l info -Q default,publish,notifications,analytics >> .run-local.worker.log 2>&1 &
    echo $! > "$WORKER_PID_FILE"
    cd - >/dev/null
  fi
fi

# ---------- 10. Frontend: npm install при необходимости ----------
if [ ! -d services/web/node_modules ]; then
  echo "[run-local] Установка npm-зависимостей (один раз)..."
  ( cd services/web && npm install )
fi

# ---------- 11. Web в текущем терминале (логи здесь; Ctrl+C остановит только Web) ----------
echo ""
echo "[run-local] Запуск веб-кабинета (логи ниже). Остановка: Ctrl+C (API и контейнеры продолжат работать)."
echo "[run-local] Кабинет: http://localhost:3000  |  Вход (dev): telegram_id 123456789  |  API: http://localhost:8000/docs"
echo ""
( cd "$ROOT/services/web" && npm run dev )
