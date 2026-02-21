# Обновление инфраструктуры (Docker / Podman)

Единый скрипт **`scripts/deploy-update.sh`** используется для обновления **на внешнем сервере** (Docker) и **локально** (Podman): сам выбирает `podman-compose`, `docker compose` или `docker-compose`, проверяет фикс календаря перед сборкой web.

---

## Внешний сервер (одна команда)

После SSH на сервер выполните **в корне репозитория** (например `/opt/lytslot`):

```bash
cd /opt/lytslot
bash scripts/deploy-update.sh --pull --no-cache
```

Это: `git pull`, проверка календаря, сборка образов (web без кэша), перезапуск контейнеров (полный профиль: api, web, db, redis, bot, worker), миграции и seed.

**Первый раз развернуть сервер с нуля** (с локальной машины):

```bash
bash scripts/deploy-from-local.sh 72.56.117.159
```

Введёте пароль SSH и при необходимости логин/токен GitHub. На сервере установится Docker, клонируется репо, создастся .env и запустится тот же `deploy-update.sh` (сборка, up, миграции).

---

## Локально (одна команда)

В корне репозитория (каталог с `infra/` и `scripts/`):

```bash
cd ~/projects/LytSlot
bash scripts/deploy-update.sh --pull
```

Локально обычно используется Podman; скрипт поднимет минимальный стек (api, web, db, redis). Полный стек (bot, worker) — только на сервере с Docker.

Если скрипт исполняемый: `./scripts/deploy-update.sh --pull`.  
При «Permission denied» используйте **`bash scripts/deploy-update.sh`**.

| Флаг | Описание |
|------|----------|
| `--pull` | Сначала `git pull` |
| `--no-cache` | Пересобрать образ web без кэша (актуальный код) |
| `--minimal` | Только api, web, db, redis |
| `--full` | + bot, worker (по умолчанию) |
| `--skip-verify` | Не проверять фикс календаря перед сборкой |

Примеры:
- Обновить с pull и пересобрать web без кэша: `bash scripts/deploy-update.sh --pull --no-cache`
- Только поднять контейнеры (без сборки): вручную, см. ниже.

---

## Вручную (если скрипта нет или нужны отдельные шаги)

```bash
cd /path/to/LytSlot
git pull
docker compose -f infra/docker-compose.yml --profile full build
docker compose -f infra/docker-compose.yml --profile full up -d
# Дождаться готовности API (несколько секунд), затем:
docker compose -f infra/docker-compose.yml --profile full exec -T api python -m alembic upgrade head
docker compose -f infra/docker-compose.yml --profile full exec -T api python -m db.seed
```

Если на сервере **Podman** вместо Docker:

```bash
cd /path/to/LytSlot
git pull
podman-compose -f infra/docker-compose.yml --profile full build
podman-compose -f infra/docker-compose.yml --profile full up -d
podman-compose -f infra/docker-compose.yml --profile full exec -T api python -m alembic upgrade head
podman-compose -f infra/docker-compose.yml --profile full exec -T api python -m db.seed
```

### Вариант Б: Только перезапуск (без сборки)

Если образы не менялись и нужно только перезапустить контейнеры:

```bash
cd /path/to/LytSlot
docker compose -f infra/docker-compose.yml --profile full up -d
```

### Проверка и логи

```bash
docker compose -f infra/docker-compose.yml --profile full ps
docker compose -f infra/docker-compose.yml --profile full logs -f api
curl -s http://localhost:8000/ready
```

---

## Быстрые команды (в корне репозитория)

| Действие | Команда |
|----------|---------|
| **Обновить всё** (сборка + перезапуск + миграции) | `bash scripts/deploy-update.sh` |
| **git pull и обновить** | `bash scripts/deploy-update.sh --pull` |
| **pull + пересборка web без кэша** | `bash scripts/deploy-update.sh --pull --no-cache` |
| **Минимальный стек** (без бота и воркера) | `bash scripts/deploy-update.sh --minimal` |
| **Полный стек** (по умолчанию) | `bash scripts/deploy-update.sh --full` |

Локально (Podman) и на сервере (Docker) скрипт сам выберет команду. Если «Permission denied» — всегда можно вызвать через `bash scripts/deploy-update.sh`.

### Если скрипта нет на сервере (`No such file or directory`)

Выполните вручную (из корня репозитория на сервере, например `/opt/lytslot`). Для **docker-compose** (через дефис):

```bash
cd /opt/lytslot
git pull
docker-compose -f infra/docker-compose.yml --profile full build --no-cache web
docker-compose -f infra/docker-compose.yml --profile full up -d
docker-compose -f infra/docker-compose.yml --profile full exec -T api python -m alembic upgrade head
docker-compose -f infra/docker-compose.yml --profile full exec -T api python -m db.seed
```

Если на сервере плагин **docker compose** (без дефиса): замените `docker-compose` на `docker compose` в командах выше.

---

## Через Makefile

Если установлен `make` и в каталоге есть `Makefile`:

| Действие | Команда |
|----------|---------|
| Обновить стек (build + up + миграции) | `make deploy-update` |
| git pull и обновить | `make deploy-pull-update` |
| Только поднять контейнеры | `make deploy-up` |
| Только собрать образы | `make deploy-build` |
| Логи | `make deploy-logs` |
| Список контейнеров | `make deploy-ps` |
| Остановить | `make deploy-down` |
| Справка по всем целям | `make help` |

Makefile сам выбирает `docker compose` или `podman-compose` по наличию в системе.

---

## Что делает `deploy-update.sh`

1. Определяет команду: **podman-compose** (если есть Podman), иначе **docker compose** или **docker-compose**.
2. По желанию: `git pull` (флаг `--pull`).
3. Проверка фикса календаря: скрипт `verify-web-calendar-fix.sh` убеждается, что в коде есть `eventClick={handleEventClick as any}` (иначе сборка web падает). Обход: `--skip-verify`.
4. Сборка образов с `CACHEBUST`; при `--no-cache` образ web пересобирается без кэша.
5. Перезапуск контейнеров: `up -d` с профилем (полный или минимальный).
6. Ожидание готовности API (`/ready`, до 60 с).
7. Миграции и seed в контейнере API.

Секреты и переменные окружения берутся из `.env` в корне проекта (скрипт их не перезаписывает).

---

## GitHub: сборка и публикация образов

Workflow **Docker Build & Push** (`.github/workflows/docker-build.yml`) при push в `main` или тегах `v*` собирает образы и публикует их в **GitHub Container Registry** (ghcr.io). На сервере можно либо собирать образы локально (Вариант А выше), либо подтягивать их из ghcr.io (нужна отдельная настройка compose под pull из реестра).

---

## Типичный цикл обновления

Локально (Podman) или на сервере (Docker):

```bash
cd ~/projects/LytSlot
bash scripts/deploy-update.sh --pull
```

После обновления проверьте:

- API: `http://ВАШ_СЕРВЕР:8000/ready`
- Web: `http://ВАШ_СЕРВЕР:3000`

Если что-то пошло не так — логи: `make deploy-logs` или  
`docker compose -f infra/docker-compose.yml --profile full logs -f api`.
