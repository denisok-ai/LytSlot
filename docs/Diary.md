# Дневник проекта LytSlot Pro

Подробный дневник технических решений, наблюдений и проблем для бесшовной работы команды разработчиков.

---

## 2025-02-20 — CI (GitHub Actions)

### Наблюдения
- В Tasktracker задача «CI/CD (GitHub Actions)» — Высокий приоритет, не начата. Нужен базовый pipeline: линтеры и тесты без деплоя.

### Решения
- Добавлен **.github/workflows/ci.yml**: триггер на push/PR в main и develop. Jobs: (1) backend-lint — Python 3.12, pip install -e ".[dev]", ruff check и black --check; (2) backend-test — сервис postgres (timescale/timescaledb:latest-pg16), env DATABASE_URL_SYNC, JWT_SECRET, ENABLE_DEV_LOGIN=true, CELERY_BROKER_URL пустой, alembic upgrade head, pytest tests/; (3) frontend-lint — Node 20, npm ci в services/web, npm run lint; (4) frontend-build — npm run build. Деплой по ветке/тегу оставлен на потом (Render/AWS/DO при необходимости).

### Проблемы
- Нет.

---

## 2025-02-20 — Ruff B008 и «системные» ошибки линтера

### Наблюдения
- Pre-commit выдавал десятки ошибок Ruff: B008 (function call in default argument), E501 (line too long), B904, F841, SIM108. Большинство B008 относились к `Depends(...)` и `Query(...)` в роутерах FastAPI.

### Решения
- **Корневая причина B008:** Правило Ruff B008 запрещает вызов функций в значениях по умолчанию аргументов (чтобы избежать побочных эффектов при определении функции). В FastAPI паттерн `def route(db: Session = Depends(get_db))` — намеренный: FastAPI не вызывает `Depends()` при определении, а использует его для внедрения зависимостей при запросе. Это ложное срабатывание для нашего стека.
- **Действие:** В `pyproject.toml` в секции `[tool.ruff]` добавлено `ignore = ["B008"]` с комментарием. Остальные замечания исправлены в коде: B904 в orders.py (`raise ... from None`), F841 в webhooks (переменные переименованы в `_body` + TODO), SIM108 в analytics (тернарный оператор), E501 — укорочены длинные строки в admin, analytics, order_flow, tasks.

### Проблемы
- Нет.

---

## 2025-02-20 — Линтеры и pre-commit

### Наблюдения
- В Tasktracker задача «Линтеры и pre-commit (backend, frontend)» имела приоритет Высокий и статус «Не начата»; ESLint уже был во фронте (next lint), ruff — в dev backend.

### Решения
- **Backend:** В pyproject.toml добавлены black и pre-commit в [project.optional-dependencies].dev; настроены [tool.ruff] (exclude миграций и .venv, select E/F/I/W/UP/B/C4/SIM) и [tool.black] (line-length 100, исключение миграций и .venv).
- **Frontend:** В services/web добавлен Prettier (^3.4.0), скрипты `npm run format` и `npm run format:check`, конфиг .prettierrc (printWidth 100, semi, singleQuote false) и .prettierignore (.next, node_modules, out, build).
- **Pre-commit:** В корне добавлен .pre-commit-config.yaml: ruff-pre-commit (--fix), black, локальные хуки — frontend eslint (cd services/web && npm run lint) и frontend prettier (cd services/web, для каждого файла путь относительно services/web). Установка: `pip install pre-commit && pre-commit install`; ручной прогон: `pre-commit run --all-files`.

### Проблемы
- Нет. Pre-commit для frontend требует окружения с node/npm (запуск из корня репозитория в WSL/Ubuntu).

---

## 2025-02-20 — Observability: request_id, логи, readiness, тесты

### Наблюдения

- Выполнены рекомендации из docs/Architecture-Audit.md (приоритеты 1–3): сквозной request_id, структурированные логи, readiness probe, интеграционные тесты.

### Решения

- **request_id и структурированные логи:** Добавлен RequestIdMiddleware (X-Request-Id из заголовка или UUID), контекстные переменные в services.api.logging_config (request_id, tenant_id). Логирование переведено на structlog с JSON в stdout (уровень, request_id, tenant_id, timestamp). В роутере orders request_id передаётся в Celery-задачи (publish_order, notify_new_order, notify_order_cancelled); в воркере тот же request_id подставляется в логи. Зависимость: structlog в pyproject.toml.
- **Readiness probe:** Эндпоинт GET /ready проверяет БД (SELECT 1) и при заданном CELERY_BROKER_URL — Redis. При недоступности зависимостей возвращается 503 с телом {"status": "not_ready", "checks": {...}}. Для k8s/Docker использовать /ready как readiness, /health — liveness.
- **Интеграционные тесты:** В tests/ добавлены conftest.py (client, db, tenant_a/b, token_a/b, channel_a/b, slot_a/b), test_health.py (/health, /ready, X-Request-Id), test_orders.py (создание заказа, список), test_rls.py (тенант A не видит заказы B и наоборот, GET по чужому order_id — 404). Запуск: pytest tests/ (требуется PostgreSQL и ENABLE_DEV_LOGIN=true).

### Проблемы

- Нет открытых.

---

## 2025-02-20 — Полный аудит архитектуры и оценка ухода от Python

### Наблюдения

- Запрос на оценку: насколько эффективнее будет отладка и эксплуатация при отказе от Python; проведён полный аудит архитектуры.

### Решения

- Аудит зафиксирован в **docs/Architecture-Audit.md**. Краткие выводы: (1) Текущая архитектура в целом корректна (границы API/Worker/Bot, RLS, монорепо). (2) Пробелы — не язык, а инструментация: нет request_id/trace_id, структурированных логов, тестов, метрик Prometheus, readiness probe, Sentry, runbook. (3) Уход от Python для текущего масштаба (10k orders/day) не даёт явного выигрыша в отладке и эксплуатации при высоких затратах на переписывание; эффективнее внедрить практики observability и операционные процедуры в текущем стеке. (4) Рекомендованный приоритет: request_id + структурированные логи, readiness probe, интеграционные тесты, затем метрики, Sentry, runbook.

### Проблемы

- Нет открытых.

---

## 2025-02-20 — Выполнение плана архитектурных доработок

### Наблюдения

- План из docs/Architecture-Plan.md выполнен в порядке 3 → 2 → 1.

### Решения

- **Задача 3 (один источник сессии):** Удалена функция `get_db()` из `db/database.py`; остались только `engine` и `SessionLocal`. Все API-зависимости берутся из `services.api.deps`.
- **Задача 2 (опциональный Worker):** В config добавлен `celery_broker_url` (env `CELERY_BROKER_URL`). В orders.py вызовы `.delay()` только при непустом broker; иначе логируется «Worker disabled». README и .env.example обновлены.
- **Задача 1 (админ):** Конфиг `admin_telegram_ids` (env `ADMIN_TELEGRAM_IDS`). В auth — `get_current_admin_user_id`. В deps — `get_db_admin()` с `SET LOCAL row_level_security = off`. admin.py переведён на get_db_admin и get_current_admin_user_id. GET /api/admin/channels возвращает все каналы только при JWT из списка админов.
- Удалён отладочный код _debug_log из services/api/main.py.

### Проблемы

- Нет открытых.

---

## Формат записи

Каждая запись содержит:
- **Дата**
- **Наблюдения** — что замечено (техдолг, риски, возможности)
- **Решения** — принятые архитектурные или технические решения
- **Проблемы** — открытые вопросы или инциденты

---

## 2025-02-20 — Ревью архитектуры и план доработок

### Наблюдения

- Проведено ревью: архитектура, код, тесты, производительность. Admin-эндпоинты используют `get_db()` без tenant — при включённом RLS возвращают пустые данные; роли «админ» нет. Вызовы Celery при недоступном broker тихо логируются. Дублирование: `get_db` в `db.database` и в `services.api.deps`; на фронте `getToken()` в каждом экране.
- Репозиторий пока не инициализирован (нет .git); код готов к первому пушу на GitHub.

### Решения

- Принято: перед дальнейшей разработкой заложить точечные архитектурные правки (сроки не горят). План зафиксирован в **docs/Architecture-Plan.md**: (1) Админ — список admin_telegram_ids в конфиге, зависимость get_current_admin_user_id, сессия get_db_admin с отключением RLS только для админ-роутов; (2) Опциональный worker — не вызывать Celery при пустом broker, логировать «worker disabled»; (3) Один источник сессии — только deps.get_db, убрать дублирование из db.database.
- После сохранения ветки на https://github.com/denisok-ai/LytSlot выполнять план в порядке: задача 3 → задача 2 → задача 1.

### Проблемы

- Нет открытых.

---

## 2025-02-19 — Инициализация архитектурной документации

### Наблюдения

- Проект описан как мульти-тенантная SaaS с целевым масштабом 1000+ каналов и 10k+ заказов/день; критична изоляция по tenant и производительность.
- Стек разнородный: FastAPI, Celery, aiogram 3, Next.js 14, два платёжных провайдера (Stripe, ЮKassa), что потребует чёткого контракта между сервисами и единого формата ошибок/логирования.
- Документация в `docs/` приведена к единому виду: Project.md (архитектура и требования), Tasktracker.md (задачи с приоритетами), Diary.md (решения и проблемы), qa.md (вопросы).

### Решения

- Принята структура документации: **Project.md** — единственный источник правды по целям, архитектуре и этапам; обновлять при изменении архитектуры или новых функциональных требованиях.
- **Tasktracker.md** — задачи с приоритетами (Критический/Высокий/Средний/Низкий), сгруппированы по разделам Project.md; при выполнении — обновлять статус.
- **Diary.md** — использовать для фиксации важных технических решений и проблем, чтобы новые разработчики могли быстро войти в контекст.
- Мульти-тенантность: ключ изоляции — `tenant_id`; реализация — sharding/партиционирование и Row-Level Security в PostgreSQL.

### Проблемы

- Ожидают ответа вопросы из **qa.md** (домен, хостинг, приоритет РФ vs international, модерация, юридические требования).
- Не зафиксирован выбор: монорепо vs отдельные репозитории для backend/bot/frontend — решить до старта разработки.

---

## 2025-02-19 — Старт реализации по детальному промпту (monorepo + 8 шагов)

### Наблюдения

- Принят детальный промпт: монорепо (services/api, bot, worker, web; infra; db; shared; tests), tenant-isolated БД (PostgreSQL + TimescaleDB), FastAPI + Celery + aiogram 3 + Next.js 14, масштаб 10k orders/day.
- Реализация разбита на шаги: 1) db/models+migrations+RLS+seed, 2) shared Pydantic, 3) API + routers + WS, 4) web dashboard, 5) bot FSM, 6) worker tasks, 7) docker-compose + deploy, 8) мониторинг/тесты.

### Решения

- Структура репозитория: **монорепо** с папками services/, infra/, db/, shared/, tests/; документировано в Project.md (п. 6.4).
- БД: таблицы tenants, channels, slots, orders, payments, views (hypertable для аналитики); RLS через `current_setting('app.tenant_id')`; миграции Alembic; seed с демо-каналами.
- Код: production-ready (typing, logging, error handling, OpenAPI); единый стиль и заголовки файлов (@file, @description, @dependencies, @created).

### Проблемы

- Нет открытых на текущий момент; по мере реализации фиксировать в следующих записях Diary.

---

## 2025-02-20 — Auth: Telegram Login + JWT

### Наблюдения

- В коде уже были заглушки auth (verify_telegram_login_init_data с jwt_secret вместо bot token, auth_callback без get_or_create Tenant). Для корректной работы виджета Telegram нужен BOT_TOKEN и алгоритм из документации (secret_key = HMAC-SHA256("WebAppData", bot_token)).

### Решения

- **Верификация initData**: используется BOT_TOKEN из окружения; secret_key = HMAC("WebAppData", bot_token); проверка auth_date не старше 24 ч.
- **auth_callback**: после верификации — get_or_create Tenant по telegram_id (имя из first_name/username или "User {id}"); JWT содержит sub (telegram_id) и tenant_id; в ответ добавлен tenant_id для фронта.
- **Зависимости**: введён get_current_tenant_id (403, если в JWT нет tenant_id); get_db_with_required_tenant для маршрутов, где RLS обязателен (channels, orders).

### Проблемы

- Нет. Refresh token не реализован (при необходимости — отдельная задача).

---

## 2025-02-20 — Тестовые данные (seed по всем сущностям)

### Наблюдения

- Нужны данные для проверки всего функционала: каналы, слоты, заказы, аналитика (views), API-ключи.

### Решения

- **db/seed.py** расширен: один tenant (telegram_id=123456789), два канала (demo_channel, tech_reviews_ru) с разными slot_duration и price_per_slot; 14 слотов по первому каналу, 7 по второму; 3 заказа (разные статусы: published, draft, paid; контент text/link, erid); несколько записей в views для графика аналитики; один API-ключ (тестовый хэш, имя «Тестовый ключ (seed)»). Функция **seed_extra()** добавляет слоты и просмотры к существующему tenant (идемпотентно).
- **scripts/seed-db.sh** — запуск `python -m db.seed` (и опционально `extra`). В README добавлен абзац про тестовые данные и вход с 123456789 в режиме разработки.

### Проблемы

- Нет. Сид выполняется после миграций (db-migrate.sh), таблица api_keys создаётся в 003.

---

## 2025-02-20 — API-ключи в кабинете

### Наблюдения

- Трекер предусматривал генерацию и отзыв API-ключей для партнёров и интеграций.

### Решения

- **Модель ApiKey**: tenant_id, key_hash (SHA-256), name (опционально), created_at. Связь с Tenant. Миграция 003: таблица api_keys, RLS по tenant_id.
- **Эндпоинты**: GET /api/api-keys — список (id, name, created_at, key_preview="••••"); POST /api/api-keys — создание (body: name?), возврат ключа в поле key один раз; DELETE /api/api-keys/:id — отзыв. Авторизация: JWT (get_db_with_required_tenant).
- **Генерация ключа**: префикс lytslot_ + secrets.token_urlsafe(32), хранится только хэш.
- **Фронт (Настройки)**: список ключей, форма создания с опциональным именем, после создания — блок с ключом и кнопкой «Копировать», предупреждение сохранить; кнопка отзыва у каждой строки.

### Проблемы

- Нет. Аутентификация по API-ключу в запросах (X-API-Key) — отдельная задача при необходимости.

---

## 2025-02-20 — OpenAPI и описание API

### Наблюдения

- FastAPI по умолчанию отдаёт /docs (Swagger) и /redoc; спецификация генерируется из кода. Для удобства разработчиков и партнёров нужны понятные теги и подписи к эндпоинтам.

### Решения

- В **main.py** добавлены openapi_tags с описаниями групп (channels, slots, orders, analytics, admin) и расширенное описание приложения (JWT, tenant isolation).
- Во всех роутерах (channels, orders, slots, analytics, admin) у эндпоинтов заданы **summary** (краткие подписи на русском).
- **scripts/export-openapi.py** — вызов app.openapi(), сохранение в docs/openapi.json для версионирования или генерации клиентов.
- В README добавлен абзац про /docs, /redoc и экспорт схемы.

### Проблемы

- Нет.

---

## 2025-02-20 — Rate limiting в API

### Наблюдения

- В middleware уже был RateLimitMiddleware по ключу X-User-Id или IP, но X-User-Id нигде не выставлялся; лимит по сути был только по IP.

### Решения

- **get_user_id_from_token_or_none(token)** в auth.py — опциональная расшифровка JWT, возвращает sub (user_id) или None без исключений (для использования в middleware).
- **RateLimitMiddleware**: ключ формируется из Authorization Bearer — при валидном JWT используется rate:user:{sub}, иначе rate:ip:{client.host}. Redis INCR + EXPIRE 60 сек; при превышении rate_limit_per_minute — ответ 429 с заголовком Retry-After: 60.
- Middleware подключён в main.py (в try/except на случай недоступности Redis).

### Проблемы

- Нет. При недоступности Redis счётчик не ведётся, лимит не применяется (fail-open).

---

## 2025-02-20 — Уведомления в Telegram (новый заказ, отмена, оплата)

### Наблюдения

- Трекер предусматривал таски отправки и шаблоны сообщений для владельцев каналов и рекламодателей.

### Решения

- **send_notification(telegram_id, text)** — таск очереди notifications: отправка личного сообщения в Telegram (chat_id = telegram_id), BOT_TOKEN из env.
- **Шаблоны**: _format_new_order_owner (владельцу канала), _format_new_order_advertiser (рекламодателю), _format_order_cancelled, _format_payment_received.
- **notify_new_order(order_id)** — загружает заказ, шлёт владельцу канала и рекламодателю (order.advertiser_id = telegram_id). Вызывается из API при POST /orders.
- **notify_order_cancelled(order_id)** — вызывается из API при PATCH заказа со статусом cancelled.
- **notify_payment_received(order_id, amount)** — заглушка для вызова из process_webhook после интеграции платежей.

### Проблемы

- Нет. Пользователь должен хотя бы раз написать боту /start, чтобы бот мог слать ему личные сообщения.

---

## 2025-02-20 — Публикация поста в Telegram из таска publish_order

### Наблюдения

- Таск publish_order уже писал в views и выставлял RLS; оставалось реализовать отправку сообщения в канал через Bot API.

### Решения

- В воркере добавлена функция _send_telegram_message(bot_token, chat_id, text) — синхронный POST на api.telegram.org/bot{token}/sendMessage (httpx). chat_id для канала — @username (если в БД username без @, добавляется @).
- В publish_order: формируется текст из order.content["text"], при наличии order.erid добавляется строка с ERID, при наличии content["link"] — ссылка. Если в окружении задан BOT_TOKEN — выполняется отправка; при успехе order.status переводится в PUBLISHED, затем создаётся запись в views и один commit. Если BOT_TOKEN не задан — отправка пропускается, в views всё равно пишется (режим без бота). При ошибке sendMessage — retry таска (до 3 раз).

### Проблемы

- Нет. Бот должен быть добавлен в канал как администратор с правом публикации сообщений.

---

## 2025-02-20 — Celery: воркер, очереди, publish_order и RLS

### Наблюдения

- В services/worker уже были celery_app (Redis broker) и таски publish_order (заглушка с вставкой View), process_webhook. Вставка в views из воркера без tenant_id нарушает RLS.

### Решения

- **celery_app**: добавлены task_routes для ping (default), aggregate_analytics (analytics); task_default_queue = "default".
- **tasks**: таск ping() для проверки воркера; publish_order — перед вставкой View устанавливается app.tenant_id из order.channel.tenant_id (set_config), чтобы RLS разрешал вставку; datetime.now(timezone.utc) для timestamp; таск aggregate_analytics (заглушка).
- **API orders**: после создания заказа вызывается publish_order.delay(str(order.id)); при недоступности Redis/ Celery ошибка только логируется, ответ 201 не отменяется.
- **scripts/run-worker.sh**: запуск worker с очередями default,publish,notifications,analytics, REDIS_URL из env.

### Проблемы

- Нет. Реальная отправка поста в Telegram (Telegram Bot API от имени канала) — следующий шаг.

---

## 2025-02-20 — Бот: FSM и интеграция с API

### Наблюдения

- В services/bot уже были main.py, api_client (get_channels, create_order), start с меню «Мои каналы», «Выбрать слот», «Статистика» без обработки callback и без FSM.
- Для сценария «Выбрать слот» нужен пошаговый поток: канал → слот (на 14 дней) → текст рекламы → подтверждение → POST /api/orders.

### Решения

- **api_client**: добавлены get_token(telegram_id) — POST /api/auth/dev-login (требует ENABLE_DEV_LOGIN=true); get_slots(token, channel_id, date_from, date_to) — GET /api/slots.
- **FSM**: OrderStates (choosing_channel, choosing_slot, entering_content, confirm). MemoryStorage в Dispatcher. В state хранятся token, channel_id, slot_id, content_text.
- **order_flow.py**: callback «slot_picker» — получение токена и каналов, показ кнопок каналов; выбор канала — загрузка слотов на 14 дней, показ свободных; выбор слота — запрос текста; ввод текста — показ сводки и «Подтвердить»/«Отмена»; подтверждение — create_order, очистка state. Callback «order_cancel» и «order_back_channels» для отмены/назад.
- **start.py**: callback «channels» — список каналов по токену; «stats» — заглушка со ссылкой на веб-кабинет. Вынесена _main_menu_kb() для повторного использования после отмены заказа.

### Проблемы

- В продакшене нужен отдельный способ выдачи JWT боту (не dev-login), например по одноразовому коду из веб-кабинета или привязка аккаунта по Telegram Login.

---

## 2025-02-20 — Аналитика: эндпоинты и страница с Recharts

### Наблюдения

- В БД есть таблица views (hypertable TimescaleDB) с полями order_id, timestamp; RLS привязывает просмотры к tenant через order → channel.
- Recharts уже в зависимостях фронта; нужны эндпоинты для сводки и агрегата просмотров по дням.

### Решения

- **API analytics**: роутер `services/api/routers/analytics.py`. GET `/api/analytics/summary` — channels_count, orders_count, views_total, revenue_total (пока 0). GET `/api/analytics/views` — query-параметры date_from, date_to, channel_id (опционально); агрегат по дням через `date_trunc('day', timestamp)` и join с orders для фильтра по channel_id; RLS через get_db_with_required_tenant.
- **Страница «Аналитика»**: сводка в карточках (каналы, заказы, просмотры, выручка); график «Просмотры по дням» (Recharts LineChart); выбор периода (7/30/90 дней) и канала; при отсутствии данных — плейсхолдер.

### Проблемы

- Нет. Revenue и CTR — следующие шаги (модель платежей, клики по ссылкам).

---

## 2025-02-20 — Календарь FullCalendar и заказы из слотов

### Наблюдения

- На странице «Календарь» уже были список слотов по каналу и создание слота; требовалось добавить создание заказа из свободного слота и визуальный календарь (FullCalendar).
- FullCalendar 6 (core, daygrid, timegrid, interaction) подключается через npm; для русской локали используется `@fullcalendar/core/locales/ru`.

### Решения

- **Создание заказа из слота**: на странице «Календарь» у каждого свободного слота — кнопка «Заказать»; форма с полями «Текст рекламы» и «Ссылка»; POST /api/orders с channel_id, slot_id, content. На странице «Заказы» добавлены превью контента и смена статуса (select + PATCH /api/orders/:id).
- **FullCalendar**: добавлен компонент `components/calendar/SlotsCalendar.tsx`; слоты маппятся в события (зелёный — свободен, серый — занят); виды week/day/month; клик по свободному слоту открывает ту же форму создания заказа. Диапазон дат по умолчанию — текущий месяц. Стили FullCalendar подключаются в компоненте (core, daygrid, timegrid).

### Проблемы

- Нет. Установка пакетов (@fullcalendar/*) выполняется в WSL/Ubuntu (`npm install` в services/web); в Windows PATH npm может быть недоступен.

---

## 2025-02-20 — Дизайн-система и прототип портала (премиум UX/UI)

### Наблюдения

- Трекер содержал задачи по Frontend без учёта единого визуального стиля; для SaaS-платформы (B2B, мульти-тенант) важен премиальный, доверительный интерфейс и консистентная навигация.
- В проекте уже есть Next.js 14, Tailwind, TanStack Query; shadcn не подключён — решено использовать собственные компоненты под общую концепцию.

### Решения

- **Дизайн-система**: CSS-переменные в globals.css (цвета, тени, радиусы); расширение Tailwind (accent emerald, shadow-card, шрифт Plus Jakarta Sans через next/font). Акцент emerald выбран для ассоциации с ростом и доверием.
- **Компоненты**: Card, CardTitle, CardDescription; Button и ButtonLink (primary/secondary/ghost, размеры); DashboardShell — фиксированный сайдбар с навигацией (Обзор, Каналы, Календарь, Заказы, Аналитика, Настройки), активное состояние по pathname.
- **Лендинг**: шапка, hero с двумя CTA, блок «Возможности» (4 карточки), нижний CTA, подвал. Все ссылки и кнопки в едином стиле.
- **Дашборд**: обзор с метриками (каналы, заказы, выручка, слоты), список каналов из API, плейсхолдер календаря. Страницы Каналы/Заказы/Календарь/Аналитика/Настройки — маршруты в навигации зарезервированы, контент добавляется по мере реализации.
- **План**: в Tasktracker обновлены раздел 5 (Frontend): дизайн и прототип — «Завершена», дашборд — «В процессе»; следующие шаги — Auth на фронте, затем страницы Каналы/Заказы и формы в том же стиле.

### Проблемы

- Нет. Кириллица отображается системным шрифтом (Plus Jakarta Sans — только Latin); при необходимости можно добавить шрифт с поддержкой кириллицы.

---

## 2025-02-20 — Auth на фронте, страницы Каналы и Заказы

### Наблюдения

- По плану следующие шаги: Auth (логин, guard), страницы Каналы и Заказы в едином стиле дашборда.

### Решения

- **Auth**: Страница /login с Telegram Login Widget (data-telegram-login, data-auth-url на /login/callback). Callback-страница получает GET-параметры от Telegram, собирает init_data, POST в /api/auth/callback, сохраняет access_token в localStorage, редирект на /dashboard. Guard в app/dashboard/layout.tsx: при отсутствии token редирект на /login?from=... . Выход в сайдбаре — очистка localStorage и редирект на /.
- **Каналы**: Страница /dashboard/channels — список каналов (useQuery), форма добавления (username, slot_duration, price_per_slot), useMutation на POST /api/channels.
- **Заказы**: Страница /dashboard/orders — список заказов из GET /api/orders, таблица (id, статус, дата).
- **Плейсхолдеры**: Страницы /dashboard/calendar, /dashboard/analytics, /dashboard/settings с заголовками и блоками «в разработке».
- **Env**: В .env.example добавлены NEXT_PUBLIC_TELEGRAM_BOT_USERNAME и NEXT_PUBLIC_APP_URL для виджета и callback URL.

### Проблемы

- Нет.
