# Журнал изменений (Changelog)

Хронологический журнал всех значительных изменений в проекте LytSlot.

---

## Формат записей

Каждая запись оформляется по шаблону:

```markdown
## [YYYY-MM-DD] - Краткое описание изменений
### Добавлено
- Описание новых функций

### Изменено
- Описание модификаций

### Исправлено
- Описание исправлений
```

---

## [2025-02-20] - CI (GitHub Actions)

### Добавлено
- **.github/workflows/ci.yml** — workflow при push/PR в `main` и `develop`: job **backend-lint** (ruff, black), **backend-test** (PostgreSQL 16/TimescaleDB service, alembic upgrade head, pytest), **frontend-lint** (npm ci, npm run lint в services/web), **frontend-build** (npm run build). Переменные для тестов: DATABASE_URL_SYNC, JWT_SECRET, ENABLE_DEV_LOGIN, CELERY_BROKER_URL пустой.

### Изменено
- Tasktracker: задача «CI/CD (GitHub Actions)» переведена в статус «В процессе» (workflow добавлен, деплой по ветке/тегу — при необходимости).

---

## [2025-02-20] - Линтеры и pre-commit

### Добавлено
- **Backend:** в `pyproject.toml` добавлены dev-зависимости `black`, `pre-commit`; расширена конфигурация `ruff` (include/exclude, select); добавлена секция `[tool.black]` (line-length 100, исключение миграций и .venv).
- **Frontend:** в `services/web` добавлены `prettier` (devDependencies), скрипты `format` и `format:check`, конфиг `.prettierrc` и `.prettierignore`.
- **Корень:** `.pre-commit-config.yaml` — хуки: ruff (с --fix), black, frontend eslint (`npm run lint` в services/web), frontend prettier (форматирование изменённых файлов в services/web).

### Изменено
- Tasktracker: задача «Линтеры и pre-commit» переведена в статус «Завершена».

---

## [2025-02-19] - Инициализация документации проекта

### Добавлено
- Создана структура документации: `docs/changelog.md`, `docs/tasktracker.md`, `docs/project.md`
- Заданы форматы записей для журнала изменений и трекера задач
- Добавлено правило Cursor для процесса разработки и документирования

---

## [2025-02-19] - Архитектура LytSlot Pro (Multi-Channel Ad Platform)

### Добавлено
- **docs/Project.md** — описание проекта: цели, масштабы (1000+ каналов, 10k+ заказов/день), бизнес-модель (Freemium/Pro), функциональные требования (мульти-каналы, веб-кабинет, бот, админка, продвинутые фичи), технологический стек (FastAPI, Celery, aiogram 3, Next.js 14, PostgreSQL, Redis, Stripe/ЮKassa), архитектурная схема (Mermaid), мульти-тенантность, этапы MVP и масштабирования, стандарты и поддерживаемость
- **docs/Tasktracker.md** — трекер задач по разделам Project.md с приоритетами (Критический/Высокий/Средний/Низкий) и статусами; задачи по инфраструктуре, backend, очередям, боту, frontend, платежам, админке, продвинутым функциям, мониторингу и документации
- **docs/Diary.md** — дневник проекта с форматом записей: дата, Наблюдения, Решения, Проблемы; первая запись о инициализации архитектурной документации
- **docs/qa.md** — список вопросов по архитектуре (инфраструктура, мульти-тенантность, платежи и юр. требования, бот/Telegram, модерация, аналитика, безопасность, репозиторий и приоритеты)
- **.cursorrules** — правила проекта: перед каждой операцией обращаться к docs/Project.md, Tasktracker.md, Diary.md, qa.md и к процессу документирования

### Изменено
- Заготовка docs/project.md заменена полным документом docs/Project.md (LytSlot Pro)
- Трекер задач расширен до Tasktracker.md с приоритетами и разделами по архитектуре

---

## [2025-02-19] - Старт реализации LytSlot Pro (monorepo, шаги 1–7)

### Добавлено
- В **Project.md** — п. 6.4: структура монорепо (services/api, bot, worker, web; infra; db; shared; tests).
- В **Diary.md** — запись о решении монорепо и плане из 8 шагов реализации.
- Реализация по промпту: создание структуры каталогов, db/ (модели SQLAlchemy, Alembic, RLS, seed), shared/ (Pydantic), services/api (FastAPI), services/web (Next.js 14), services/bot (aiogram 3), services/worker (Celery), infra (docker-compose, k8s).
- **Код**: db/models (Tenant, Channel, Slot, Order, Payment, View), db/migrations/versions/001 (схема + RLS + hypertable), shared/schemas (BaseTenantModel, OrderCreate, SlotFilter), services/api (auth JWT + Telegram init_data, routers channels/orders/admin/webhooks, WebSocket /ws/dashboard), services/bot (start menu, api_client), services/worker (publish_order, process_webhook), services/web (App Router, dashboard с useQuery), infra/docker-compose.yml и Dockerfile'ы.

---

## [2025-02-20] - Auth: Telegram Login + JWT

### Добавлено
- **Верификация Telegram Login Widget**: проверка initData через HMAC-SHA256 с секретом из BOT_TOKEN (WebAppData), проверка auth_date (защита от повторного использования, 24 ч).
- **POST /api/auth/callback**: при успешной проверке — get_or_create Tenant по telegram_id, имя из first_name/username; выдача JWT с sub (telegram_id) и tenant_id; в ответе access_token, token_type, tenant_id.
- **Зависимости**: get_current_user_id, get_optional_tenant_id, get_current_tenant_id (403 при отсутствии tenant); get_db_with_tenant (опциональный tenant), get_db_with_required_tenant (обязательный tenant для RLS).
- **Конфиг**: telegram_bot_token (env BOT_TOKEN), auth_date_max_age_seconds (24 ч).

### Изменено
- Роутеры channels и orders переведены на get_db_with_required_tenant (обязательный tenant для списков и создания).

---

## [2025-02-20] - API: CRUD каналы, слоты, заказы

### Добавлено
- **Скрипт** `scripts/db-migrate.sh`: применение миграций и seed (один раз после поднятия БД).
- **Каналы**: GET /api/channels, GET /api/channels/{id}, POST /api/channels (ChannelCreate), PATCH /api/channels/{id} (ChannelUpdate). Схемы в shared/schemas/channel.py.
- **Слоты**: роутер `/api/slots` — GET list (query: channel_id, date_from, date_to), GET /{id}, POST create (SlotCreate: channel_id, datetime). Схема SlotCreate в shared/schemas/slot.py.
- **Заказы**: GET /api/orders/{id}, PATCH /api/orders/{id} (OrderUpdate: status). Схема OrderUpdate в shared/schemas/order.py.

### Изменено
- README: миграции и seed — вызов через `./scripts/db-migrate.sh`.
- Tasktracker: задача «API: каналы, слоты, заказы» отмечена как Завершена.
