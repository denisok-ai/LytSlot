#!/usr/bin/env bash
# =============================================================================
# LytSlot — единый скрипт обновления (локально и на внешнем сервере)
# =============================================================================
# Используется для:
#   - обновления на внешнем сервере (Docker): git pull, сборка, up, миграции;
#   - локального запуска (Podman): сборка и подъём минимального стека;
#   - первичного развёртывания (вызов из server-bootstrap.sh).
#
# Определяет команду: podman-compose | docker compose | docker-compose.
# На сервере с Docker поддерживается --profile full (api, web, db, redis, bot, worker).
# Локально с Podman профиль не передаётся (podman-compose 1.x не поддерживает --profile).
#
# Использование:
#   bash scripts/deploy-update.sh                  # сборка + up + миграции (без pull)
#   bash scripts/deploy-update.sh --pull           # git pull, затем то же
#   bash scripts/deploy-update.sh --pull --no-cache   # рекомендуемый вариант на внешнем сервере
#   bash scripts/deploy-update.sh --minimal        # только api, web, db, redis
#   bash scripts/deploy-update.sh --full          # + bot, worker (по умолчанию при Docker)
#   bash scripts/deploy-update.sh --skip-verify    # не проверять фикс календаря
#
# На внешнем сервере (после SSH):
#   cd /opt/lytslot && bash scripts/deploy-update.sh --pull --no-cache
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
PROFILE_ARG="--profile full"
DO_PULL=""
NO_CACHE_WEB=""
SKIP_VERIFY=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --pull)        DO_PULL=1 ; shift ;;
    --minimal)     PROFILE_ARG="" ; shift ;;
    --full)        PROFILE_ARG="--profile full" ; shift ;;
    --no-cache)    NO_CACHE_WEB=1 ; shift ;;
    --skip-verify) SKIP_VERIFY=1 ; shift ;;
    -h|--help)
      echo "Использование: $0 [--pull] [--no-cache] [--minimal|--full] [--skip-verify]"
      echo "  --pull        перед обновлением выполнить git pull"
      echo "  --no-cache    пересобрать образ web без кэша (рекомендуется на сервере после pull)"
      echo "  --minimal     только api, web, db, redis"
      echo "  --full        api, web, db, redis, bot, worker (по умолчанию при Docker)"
      echo "  --skip-verify не проверять фикс календаря (eventClick as any)"
      echo ""
      echo "На внешнем сервере: cd /opt/lytslot && bash scripts/deploy-update.sh --pull --no-cache"
      exit 0
      ;;
    *) echo "Неизвестный аргумент: $1. Используйте --help." ; exit 1 ;;
  esac
done

# ---- Определение команды Compose ----
# Сначала Podman: иначе «docker compose» может вызвать системный docker-compose (Python) и падать по сокету.
detect_compose() {
  if command -v podman &>/dev/null && command -v podman-compose &>/dev/null; then
    echo "podman-compose"
    return
  fi
  if command -v docker &>/dev/null; then
    if docker compose version &>/dev/null 2>&1; then
      echo "docker compose"
      return
    fi
    if command -v docker-compose &>/dev/null && docker-compose version &>/dev/null 2>&1; then
      echo "docker-compose"
      return
    fi
  fi
  echo ""
}

COMPOSE="$(detect_compose)"
if [ -z "$COMPOSE" ]; then
  echo "Ошибка: не найдена рабочая команда. Установите:"
  echo "  Podman: sudo apt install podman podman-compose"
  echo "  Docker: sudo apt install docker.io docker-compose-plugin  (или docker-compose)"
  exit 1
fi

# podman-compose 1.x не поддерживает --profile (invalid choice: 'full')
if [ "$COMPOSE" = "podman-compose" ] && [ -n "$PROFILE_ARG" ]; then
  PROFILE_ARG=""
  echo "Примечание: podman-compose не поддерживает --profile, поднимается минимальный стек (api, web, db, redis)."
fi

echo "=== LytSlot: обновление ==="
echo "Каталог: $REPO_ROOT"
echo "Compose: $COMPOSE -f $COMPOSE_FILE"
[ -n "$PROFILE_ARG" ] && echo "Профиль: full (api, web, db, redis, bot, worker)"
echo ""

# ---- git pull ----
if [ -n "$DO_PULL" ]; then
  echo "=== git pull ==="
  git pull
  echo ""
fi

# ---- Проверка фикса календаря (сборка web падает без eventClick as any) ----
if [ -z "$SKIP_VERIFY" ] && [ -f "$SCRIPT_DIR/verify-web-calendar-fix.sh" ]; then
  if ! bash "$SCRIPT_DIR/verify-web-calendar-fix.sh"; then
    echo "Сборка web упадёт. Сделайте git pull или добавьте в SlotsCalendar.tsx: eventClick={handleEventClick as any}"
    echo "Или запустите с --skip-verify."
    exit 1
  fi
  echo ""
fi

# ---- Сборка ----
echo "=== Сборка образов ==="
export CACHEBUST="${CACHEBUST:-$(date +%s)}"

if [ -n "$NO_CACHE_WEB" ]; then
  $COMPOSE -f "$COMPOSE_FILE" build --no-cache web
  $COMPOSE -f "$COMPOSE_FILE" build
else
  $COMPOSE -f "$COMPOSE_FILE" build
fi

echo ""
echo "=== Перезапуск контейнеров ==="
# Пустой PROFILE_ARG при podman-compose — ок (один пробел в команде)
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG up -d

echo ""
echo "Ожидание готовности API (до 60 с)..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/ready &>/dev/null; then
    echo "API готов."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Предупреждение: API не ответил /ready за 60 с. Логи: $COMPOSE -f $COMPOSE_FILE $PROFILE_ARG logs api"
    exit 1
  fi
  sleep 2
done

echo "=== Миграции и seed ==="
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG exec -T api python -m alembic upgrade head
$COMPOSE -f "$COMPOSE_FILE" $PROFILE_ARG exec -T api python -m db.seed

echo ""
echo "Обновление завершено. API: http://localhost:8000/docs  Web: http://localhost:3000"
