# LytSlot Pro — Multi-Channel Ad Platform

Масштабируемая SaaS-платформа для продажи рекламы в Telegram-каналах (1000+ клиентов, 10k orders/day).

## Структура (monorepo)

- `services/api` — FastAPI (auth, channels, orders, admin, webhooks, WebSocket)
- `services/bot` — aiogram 3.x (FSM: каналы → слот → заказ)
- `services/worker` — Celery (publish, webhooks)
- `services/web` — Next.js 14 (dashboard, календарь, аналитика)
- `db` — SQLAlchemy модели, Alembic, TimescaleDB (views), RLS
- `shared` — Pydantic-схемы
- `infra` — docker-compose, Dockerfile'ы

## Локальный запуск

1. Скопировать `.env.example` в `.env`, задать `BOT_TOKEN`, `JWT_SECRET`.
2. БД и Redis.  
   **Если у вас Docker:**  
   ```bash
   docker compose -f infra/docker-compose.yml up -d db redis
   ```  
   **Если при этой команде ошибка про сокет** (`FileNotFoundError`, `No such file or directory`, `Connection aborted`) — у вас **Podman**. Тогда используйте команды из раздела [Запуск с Podman](#запуск-с-podman-ubuntu-с-podman-вместо-docker) ниже (например `./scripts/podman-up-db-redis.sh`).
3. Миграции и seed (один раз после поднятия БД).

   **Вариант А — через venv (хост).** В Ubuntu 24.04 обязателен venv. Если при `python3 -m venv .venv` пишет «ensurepip is not available» — сначала установите пакет и **дождитесь окончания установки** (на «Do you want to continue? [Y/n]» введите `Y` и Enter):
   ```bash
   sudo apt install python3.12-venv
   ```
   Затем (если venv создавался с ошибкой — удалите битую папку):
   ```bash
   cd /home/denisok/projects/LytSlot
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot
   ./scripts/db-migrate.sh
   ```

   **Вариант Б — миграции в контейнере** (venv на хосте не нужен). После того как стек поднят (`./scripts/podman-up.sh`):
   ```bash
   ./scripts/db-migrate-in-container.sh
   ```
   Скрипт выполнит `alembic upgrade head` и `db.seed` внутри контейнера API.

   Если ошибка `'bash\r'` — выполните `sed -i 's/\r$//' scripts/db-migrate.sh`.
4. API (обязательно с активированным venv, иначе будет `ModuleNotFoundError: No module named 'fastapi'`):
   ```bash
   source .venv/bin/activate
   uvicorn services.api.main:app --reload
   ```
   Или скрипт (сам подхватит .venv): `./scripts/run-api.sh`  
   Если ошибка `'bash\r'`: выполните `sed -i 's/\r$//' scripts/run-api.sh` или запустите `bash scripts/run-api.sh`.

   **Документация API:** после запуска API доступны Swagger UI — `http://localhost:8000/docs`, ReDoc — `http://localhost:8000/redoc`. Экспорт схемы в файл: `python scripts/export-openapi.py` (создаёт `docs/openapi.json`).
5. Бот: `python -m services.bot.main`  
   Для авторизации пользователей бот вызывает API (dev-login по telegram_id): API должен быть запущен, в корневом `.env` задать `ENABLE_DEV_LOGIN=true` и `API_BASE_URL` в `services/bot` (или по умолчанию `http://localhost:8000`).
6. Worker (опционально): если в `.env` задан `CELERY_BROKER_URL` (например `redis://localhost:6379/0`), API ставит задачи в очередь. Если не задан — API работает без фоновых задач (удобно для dev без Redis). Запуск воркера: `./scripts/run-worker.sh`. Переменные: `REDIS_URL`, `BOT_TOKEN`.
7. Web: `cd services/web && npm install && npm run dev`

**Тестовые данные:** после миграций `db-migrate.sh` автоматически запускает сид (tenant с telegram_id=123456789, 2 канала, слоты, заказы, просмотры, API-ключ). Чтобы войти под этим пользователем: на странице /login включите «Режим разработки» и введите **123456789** → «Войти для разработки». Тогда в кабинете появятся каналы, заказы, данные в аналитике и один тестовый API-ключ в Настройках. Повторно заполнить данными: `./scripts/seed-db.sh` (если tenant уже есть — подсказка; добавить слоты/просмотры: `./scripts/seed-db.sh extra`).

### Запуск с Podman (Ubuntu с podman вместо Docker)

Если при `docker compose` появляется ошибка про сокет (`FileNotFoundError`, `No such file or directory`) — у вас **Podman**. Используйте **podman-compose**.

**Шаг 0 — один раз:** установить podman-compose и (по желанию) настроить registries:
   ```bash
   sudo apt install podman-compose
   mkdir -p ~/.config/containers
   cp /home/denisok/projects/LytSlot/infra/registries.conf ~/.config/containers/registries.conf
   ```

**Только БД и Redis** (API/миграции запускаете на хосте в venv):
   ```bash
   cd /home/denisok/projects/LytSlot
   chmod +x scripts/podman-up-db-redis.sh
   ./scripts/podman-up-db-redis.sh
   export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot
   ./scripts/db-migrate.sh
   ```

**Весь стек** (api, bot, worker, web в контейнерах):
   ```bash
   cd /home/denisok/projects/LytSlot
   chmod +x scripts/podman-up.sh
   ./scripts/podman-up.sh
   ```
   Или вручную:
   ```bash
   cd /home/denisok/projects/LytSlot
   podman-compose -f infra/docker-compose.yml down --remove-orphans
   podman-compose -f infra/docker-compose.yml build
   podman-compose -f infra/docker-compose.yml up -d
   ```
*«"/" is not a shared mount»* при rootless Podman можно игнорировать.

**Вариант B — сокет Podman + docker-compose**  
Чтобы старый `docker-compose` подключался к Podman:
```bash
systemctl --user start podman.socket
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
docker compose -f infra/docker-compose.yml up -d
```
(В одном терминале держите `podman system service --time=0`, если сокет не поднимается через systemd.)

После запуска: API — http://localhost:8000/docs, health — http://localhost:8000/health.

### Не удаётся открыть сайт (localhost:8000 или :3000)

1. **Проверка из WSL** — в терминале Ubuntu выполните:
   ```bash
   curl -s http://localhost:8000/health
   ```
   Ожидается: `{"status":"ok"}`. Если ответ пришёл — API работает, проблема в доступе с Windows к WSL.

2. **Браузер на Windows**: WSL2 пробрасывает порты на localhost. Попробуйте:
   - http://127.0.0.1:8000/docs
   - Если не открывается — узнайте IP WSL: в WSL выполните `hostname -I | awk '{print $1}'` и откройте в браузере `http://<этот-IP>:8000/docs`.

3. **Если `curl` из WSL не отвечает** — посмотрите логи API:
   ```bash
   podman logs infra_api_1
   ```
   Если после правки кода API контейнер всё ещё падает с той же ошибкой — образ не обновился (контейнер перезапущен, но не пересоздан). Тогда удалите контейнер, пересоберите образ и поднимите заново:
   ```bash
   podman rm -f infra_api_1
   podman-compose -f infra/docker-compose.yml build api
   podman-compose -f infra/docker-compose.yml up -d api
   ```
   Если есть ошибки подключения к БД — один раз выполните миграции. Либо в контейнере: `./scripts/db-migrate-in-container.sh`. Либо на хосте (в активированном venv): `export DATABASE_URL_SYNC=postgresql://lytslot:lytslot@localhost:5432/lytslot` и `./scripts/db-migrate.sh`.

## Развёртывание на чистой ОС

Пошаговые команды (клонирование, зависимости, БД, миграции, запуск API и web): **[docs/Deploy-Clean-OS.md](docs/Deploy-Clean-OS.md)**.

## Линтеры и pre-commit

- **Backend:** `ruff` (линтер) и `black` (форматирование). Установка dev-зависимостей: `pip install -e ".[dev]"`. Запуск: `ruff check db shared services tests`, `black db shared services tests`.
- **Frontend:** `eslint` (уже в Next.js) и `prettier`. В `services/web`: `npm run lint`, `npm run format`, `npm run format:check`.
- **Pre-commit:** нужен инициализированный Git-репозиторий (`git init`, если ещё не сделано). Затем в корне: `pip install pre-commit && pre-commit install`. Перед каждым коммитом будут запускаться ruff, black, frontend lint и prettier. Ручной прогон: `pre-commit run --all-files`. Без Git можно обходиться только ручным запуском ruff/black и `npm run lint`/`npm run format`.

## Документация

- [docs/Project.md](docs/Project.md) — цели, архитектура, этапы
- [docs/Tasktracker.md](docs/Tasktracker.md) — задачи и приоритеты
- [docs/Diary.md](docs/Diary.md) — решения и проблемы
