# Развёртывание на чистой ОС (Ubuntu 24.04 / 22.04)

Команды для клонирования репозитория и запуска LytSlot Pro с нуля. Путь к проекту замените на свой (например `/opt/lytslot` или `~/projects/LytSlot`).

---

## Автономный запуск на внешнем сервере (Docker/Podman)

Если на сервере установлены Docker (или Podman), весь стек можно поднять одной командой. Файл `.env` при отсутствии создаётся из `.env.example` (для продакшена потом отредактируйте в нём JWT_SECRET и BOT_TOKEN):

```bash
cd /path/to/LytSlot
chmod +x scripts/docker-up-full.sh
./scripts/docker-up-full.sh
```

Опционально: `./scripts/docker-up-full.sh --minimal` — поднимает только API, Web, БД и Redis (без бота и воркера; удобно для первого запуска или демо без Telegram-бота).

Скрипт:
- при отсутствии `.env` копирует его из `.env.example`;
- определяет доступную команду (`docker compose` или `podman-compose`);
- собирает образы и запускает сервисы (по умолчанию полный стек: db, redis, api, bot, worker, web);
- ждёт готовности API (эндпоинт `/ready`);
- выполняет миграции и seed внутри контейнера API.

В `infra/docker-compose.yml` для всех сервисов задано `restart: unless-stopped` и healthchecks для `db`, `redis`, `api` — после перезагрузки сервера контейнеры поднимутся самостоятельно. **Обновление после изменений в коде** — удобнее всего скрипт (он сам выберет docker/podman, соберёт образы, перезапустит контейнеры и применит миграции):

```bash
./scripts/deploy-update.sh --pull
```

Вручную: `docker compose -f infra/docker-compose.yml build && docker compose -f infra/docker-compose.yml up -d`, затем миграции в контейнере API (см. README). Подробный список команд: [Deploy-Update.md](Deploy-Update.md).

---

## 1. Установка зависимостей (один раз)

```bash
# Обновление и базовые пакеты
sudo apt update && sudo apt install -y git curl

# Python 3.11+ и venv
sudo apt install -y python3 python3-pip python3.12-venv

# Node.js 18+ (для фронта)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Контейнеры: либо Docker, либо Podman
# Вариант A — Docker
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Выйти из сессии и зайти снова, чтобы группа применилась

# Вариант B — Podman (rootless)
sudo apt install -y podman podman-compose
```

---

## 2. Клонирование и переход в проект

```bash
git clone https://github.com/denisok-ai/LytSlot.git
cd LytSlot
```

Путь к проекту дальше считаем текущим каталогом (`$(pwd)` = корень репозитория).

---

## 3. Конфиг окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`: задайте минимум `JWT_SECRET` и `BOT_TOKEN` (бот можно не трогать, если только API + web).

```bash
# Для локального входа без Telegram (режим разработки)
# Раскомментируйте в .env:
# ENABLE_DEV_LOGIN=true
nano .env
```

Для фронта (опционально, если будете открывать web):

```bash
cp services/web/.env.local.example services/web/.env.local
# При необходимости отредактируйте NEXT_PUBLIC_APP_URL (например http://ВАШ_IP:3000)
```

---

## 4. База данных и Redis

**С Docker:**

```bash
docker compose -f infra/docker-compose.yml up -d db redis
```

**С Podman:**

```bash
chmod +x scripts/podman-up-db-redis.sh
./scripts/podman-up-db-redis.sh
```

Подождите 5–10 секунд, пока PostgreSQL поднимется. Проверка:

```bash
# Docker
docker compose -f infra/docker-compose.yml ps

# Podman
podman ps
```

---

## 5. Python-окружение, миграции и тестовые данные

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot

# Исправить CRLF в скриптах, если ошибка 'bash\r'
sed -i 's/\r$//' scripts/db-migrate.sh scripts/seed-db.sh scripts/run-api.sh 2>/dev/null || true

chmod +x scripts/db-migrate.sh scripts/seed-db.sh scripts/run-api.sh
./scripts/db-migrate.sh
```

Сид создаёт тестового tenant с `telegram_id=123456789`. Для входа в кабинет в режиме разработки используйте этот ID на странице /login.

---

## 6. Запуск API

В том же терминале (с активированным venv):

```bash
./scripts/run-api.sh
```

Или вручную:

```bash
source .venv/bin/activate
uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```

Проверка: в другом терминале `curl -s http://localhost:8000/health` → `{"status":"ok"}`. Документация API: http://localhost:8000/docs.

---

## 7. Запуск веб-кабинета (Next.js)

Новый терминал:

```bash
cd LytSlot
cd services/web
npm install
npm run dev
```

Откройте http://localhost:3000. Вход: /login → «Режим разработки» → введите **123456789** → «Войти для разработки».

---

## 8. Опционально: Worker (Celery) и бот

**Worker** (нужен запущенный Redis):

```bash
cd LytSlot
source .venv/bin/activate
./scripts/run-worker.sh
```

**Бот** (нужен запущенный API и BOT_TOKEN в .env):

```bash
cd LytSlot
source .venv/bin/activate
python -m services.bot.main
```

---

## Краткая шпаргалка (всё уже установлено)

```bash
cd /path/to/LytSlot
source .venv/bin/activate
export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot

# Терминал 1: БД + Redis (если ещё не запущены)
./scripts/podman-up-db-redis.sh   # или docker compose -f infra/docker-compose.yml up -d db redis

# Терминал 2: API
./scripts/run-api.sh

# Терминал 3: Web
cd services/web && npm run dev
```

---

## Порты

| Сервис   | Порт |
|----------|------|
| API      | 8000 |
| Web      | 3000 |
| PostgreSQL | 5432 |
| Redis    | 6379 |

На сервере откройте в файрволе при необходимости: `sudo ufw allow 8000` и `sudo ufw allow 3000`.
