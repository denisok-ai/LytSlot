# Развёртывание с нуля на сервере (один запуск)

Полное развёртывание LytSlot на чистой Ubuntu 24.04. Вам нужно ввести только **пароль от сервера (SSH)** и при приватном репозитории — **логин и токен GitHub**.

---

## Требования к серверу

- **ОС:** Ubuntu 24.04 (после переустановки подойдёт).
- **Доступ:** `ssh root@IP` (пароль или ключ).
- **Порты:** на сервере должны быть доступны 22 (SSH), 3000 (Web), 8000 (API). Закрытые у хостера порты (25, 3389 и т.д.) не используются.

Рекомендуемые характеристики: от 2 GB RAM, 2 CPU, 40 GB диск (как у вашего тестового сервера).

---

## Одна команда с вашей машины

Из каталога с клонированным репозиторием LytSlot:

```bash
chmod +x scripts/deploy-from-local.sh scripts/server-bootstrap.sh
./scripts/deploy-from-local.sh 72.56.117.159
```

Или без аргумента (подставится IP по умолчанию 72.56.117.159):

```bash
./scripts/deploy-from-local.sh
```

**Что будет запрошено:**

1. **Пароль от сервера** — при подключении по SSH (если не используете ключ).
2. **GitHub** — только если репозиторий **приватный**. На сервере при `git clone` попросят:
   - **Username:** ваш логин GitHub;
   - **Password:** пароль или **Personal Access Token** (рекомендуется: GitHub → Settings → Developer settings → Personal access tokens → Generate).

Для **публичного** репозитория пароль GitHub не нужен.

---

## Что делает скрипт на сервере

1. Обновляет пакеты, ставит git, Docker и docker-compose.
2. Клонирует репозиторий в `/opt/lytslot` (или `INSTALL_DIR`).
3. Создаёт `.env` из `.env.example`, если его ещё нет.
4. Собирает образы с `CACHEBUST` (актуальный код), поднимает полный стек (db, redis, api, web, bot, worker).
5. Ждёт готовности API, применяет миграции и seed.
6. При включённом ufw — открывает порты 22, 80, 443, 3000, 8000.
7. Выводит ссылки на API и Web.

После выполнения откройте в браузере:

- **Web:** http://72.56.117.159:3000  
- **API (документация):** http://72.56.117.159:8000/docs  

---

## Свой репозиторий или ветка

```bash
REPO_URL=https://github.com/ВАШ_ЛОГИН/LytSlot.git BRANCH=main ./scripts/deploy-from-local.sh 72.56.117.159
```

Или другой каталог на сервере:

```bash
INSTALL_DIR=/home/app/lytslot ./scripts/deploy-from-local.sh 72.56.117.159
```

---

## Если запускаете скрипт прямо на сервере

Зайдите по SSH и выполните (скрипт нужно сначала скопировать на сервер или вставить содержимое):

```bash
ssh root@72.56.117.159
# затем на сервере:
curl -sL https://raw.githubusercontent.com/denisok-ai/LytSlot/main/scripts/server-bootstrap.sh -o /tmp/server-bootstrap.sh
chmod +x /tmp/server-bootstrap.sh
sudo bash /tmp/server-bootstrap.sh
```

Либо скопируйте `scripts/server-bootstrap.sh` на сервер (например через scp) и запустите там `bash /root/server-bootstrap.sh`.

---

## После развёртывания

- Настройка продакшена: отредактируйте на сервере `/opt/lytslot/.env` (JWT_SECRET, BOT_TOKEN и т.д.) и перезапустите:  
  `docker compose -f infra/docker-compose.yml --profile full up -d --force-recreate api bot worker`.
- Обновление кода: на сервере `cd /opt/lytslot && bash scripts/deploy-update.sh --pull --no-cache` (или `make deploy-pull-update`).
