#!/usr/bin/env bash
# =============================================================================
# LytSlot — развёртывание с нуля на чистом Ubuntu (запускать НА СЕРВЕРЕ под root).
# Устанавливает: пакеты, Docker, клонирует репо, создаёт .env, затем вызывает
# единый скрипт scripts/deploy-update.sh (сборка, up, миграции).
# Для приватного репо при git clone запросят логин и токен GitHub.
# =============================================================================
set -e
export DEBIAN_FRONTEND=noninteractive

INSTALL_DIR="${INSTALL_DIR:-/opt/lytslot}"
REPO_URL="${REPO_URL:-https://github.com/denisok-ai/LytSlot.git}"
BRANCH="${BRANCH:-main}"

echo "=== LytSlot: развёртывание с нуля ==="
echo "Каталог: $INSTALL_DIR"
echo "Репозиторий: $REPO_URL (ветка: $BRANCH)"
echo ""

# 1. Системные пакеты
echo "=== Установка пакетов ==="
apt-get update -qq
apt-get install -y -qq git curl ca-certificates

# 2. Docker и Compose
if ! command -v docker &>/dev/null; then
  echo "=== Установка Docker ==="
  apt-get install -y -qq docker.io
  systemctl enable --now docker
fi
if ! docker compose version &>/dev/null 2>&1 && ! command -v docker-compose &>/dev/null; then
  echo "=== Установка Docker Compose ==="
  apt-get install -y -qq docker-compose-plugin 2>/dev/null || apt-get install -y -qq docker-compose
fi

# 3. Репозиторий
mkdir -p "$(dirname "$INSTALL_DIR")"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "=== Обновление репозитория ==="
  cd "$INSTALL_DIR"
  git fetch origin
  git checkout -q "$BRANCH" 2>/dev/null || true
  git pull -q origin "$BRANCH" || true
else
  echo "=== Клонирование репозитория ==="
  echo "При приватном репозитории введите логин GitHub и пароль (или Personal Access Token)."
  GIT_TERMINAL_PROMPT=1 git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# 4. .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env из .env.example. Для продакшена: nano $INSTALL_DIR/.env (JWT_SECRET, BOT_TOKEN)."
else
  echo ".env уже существует."
fi

# 5. Сборка, запуск и миграции
echo ""
COMPOSE_FILE="infra/docker-compose.yml"
if [ -f scripts/deploy-update.sh ]; then
  echo "=== Запуск единого скрипта обновления (сборка, up, миграции) ==="
  bash scripts/deploy-update.sh --no-cache
else
  echo "=== Сборка образов (скрипт deploy-update.sh не найден — выполняем шаги вручную) ==="
  if docker compose version &>/dev/null 2>&1; then
    COMPOSE="docker compose"
  elif command -v docker-compose &>/dev/null; then
    COMPOSE="docker-compose"
  else
    echo "Ошибка: нужен docker compose или docker-compose."
    exit 1
  fi
  export CACHEBUST="${CACHEBUST:-$(date +%s)}"
  $COMPOSE -f "$COMPOSE_FILE" build --no-cache web
  $COMPOSE -f "$COMPOSE_FILE" build
  echo "=== Запуск контейнеров ==="
  $COMPOSE -f "$COMPOSE_FILE" --profile full up -d
  echo "Ожидание готовности API (до 90 с)..."
  for i in $(seq 1 45); do
    if curl -sf http://localhost:8000/ready &>/dev/null; then echo "API готов."; break; fi
    [ "$i" -eq 45 ] && echo "Предупреждение: API не ответил за 90 с." && break
    sleep 2
  done
  echo "=== Миграции и seed ==="
  $COMPOSE -f "$COMPOSE_FILE" --profile full exec -T api python -m alembic upgrade head
  $COMPOSE -f "$COMPOSE_FILE" --profile full exec -T api python -m db.seed
fi

# 6. Порты (опционально)
if command -v ufw &>/dev/null && [ "$(ufw status 2>/dev/null | head -1)" = "Status: active" ]; then
  for p in 22 80 443 3000 8000; do ufw allow "$p" 2>/dev/null || true; done
  echo "Порты 22,80,443,3000,8000 разрешены в ufw."
fi

echo ""
echo "=== Готово ==="
echo "API:    http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "Web:    http://$(hostname -I | awk '{print $1}'):3000"
echo "Health: http://$(hostname -I | awk '{print $1}'):8000/ready"
echo ""
echo "Дальнейшие обновления: cd $INSTALL_DIR && bash scripts/deploy-update.sh --pull --no-cache"
echo "(если скрипта нет — см. docs/Deploy-Update.md, раздел «Если скрипта нет на сервере»)"
