#!/usr/bin/env bash
# @file: local-preflight.sh
# @description: Проверки перед локальным запуском: .env, venv, БД, скрипты (CRLF).
# @dependencies: bash
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
ERRORS=0

echo "=== Проверка перед локальным запуском ==="

# 1. .env
if [ ! -f .env ]; then
  echo "[!] Файл .env не найден. Копирую из .env.example..."
  cp .env.example .env
  echo "    Отредактируйте .env: JWT_SECRET, BOT_TOKEN (для dev можно оставить как есть)."
fi
echo "[OK] .env есть"

# 2. CRLF в скриптах (на WSL вызывает «bash: ...\r: command not found»)
for sh in scripts/local-preflight.sh scripts/db-migrate.sh scripts/seed-db.sh scripts/run-api.sh scripts/run-worker.sh scripts/podman-up-db-redis.sh; do
  if [ -f "$sh" ] && grep -q $'\r' "$sh" 2>/dev/null; then
    echo "[!] В $sh обнаружены символы CRLF. Исправляю..."
    sed -i 's/\r$//' "$sh"
  fi
done
echo "[OK] Скрипты без CRLF"

# 3. venv и зависимости
if [ ! -x .venv/bin/python3 ]; then
  echo "[!] Виртуальное окружение не найдено. Создайте:"
  echo "    python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  ERRORS=$((ERRORS + 1))
else
  if ! .venv/bin/python3 -c "import fastapi, alembic" 2>/dev/null; then
    echo "[!] В venv не установлены зависимости. Выполните:"
    echo "    source .venv/bin/activate && pip install -e ."
    ERRORS=$((ERRORS + 1))
  else
    echo "[OK] venv и зависимости Python"
  fi
fi

# 4. PostgreSQL доступен (порт 5432)
if ! command -v nc &>/dev/null; then
  echo "[~] netcat не найден, проверку порта 5432 пропускаю"
elif ! nc -z localhost 5432 2>/dev/null; then
  echo "[!] PostgreSQL на localhost:5432 недоступен. Запустите БД и Redis:"
  echo "    При Podman (Emulate Docker CLI using podman):"
  echo "      ./scripts/podman-up-db-redis.sh"
  echo "    или: podman-compose -f infra/docker-compose.yml up -d db redis"
  echo "    При Docker: docker compose -f infra/docker-compose.yml up -d db redis"
  echo "    Подождите 5–10 секунд после запуска контейнеров."
  ERRORS=$((ERRORS + 1))
else
  echo "[OK] PostgreSQL на :5432 доступен"
fi

# 5. Frontend: node_modules
if [ ! -d services/web/node_modules ]; then
  echo "[~] В services/web не установлены npm-зависимости. Перед запуском web выполните:"
  echo "    cd services/web && npm install"
fi

# 6. services/web/.env.local (опционально для Telegram Login)
if [ ! -f services/web/.env.local ]; then
  echo "[~] services/web/.env.local отсутствует (нужен для Telegram Login Widget). Для dev-входа не обязателен."
  echo "    Создать: cp services/web/.env.local.example services/web/.env.local"
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "=== Обнаружено проблем: $ERRORS. Устраните их и запустите скрипт снова. ==="
  exit 1
fi
echo "=== Предпроверка пройдена. Можно запускать сервисы. ==="
