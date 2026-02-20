# Сохранение ветки на GitHub

Однократная настройка: инициализация git, привязка к репозиторию, первый коммит и пуш.

**Репозиторий:** https://github.com/denisok-ai/LytSlot

---

## Шаги (выполнять в терминале из корня проекта)

### 1. Инициализация репозитория

```bash
cd ~/projects/LytSlot
git init
```

### 2. Добавить remote

```bash
git remote add origin https://github.com/denisok-ai/LytSlot.git
```

Если репозиторий на GitHub уже создан с README/license — при первом пуше может понадобиться `git pull origin main --allow-unrelated-histories` (или `master`), затем разрешить конфликты при необходимости. Если репозиторий **пустой** — следующий шаг без pull.

### 3. Добавить файлы и первый коммит

```bash
git add .
git status   # проверьте, что в коммит не попали .env, .venv, node_modules
git commit -m "Initial: monorepo LytSlot Pro (API, web, bot, worker, db, RLS, seed)"
```

### 4. Ветка и пуш

Обычно основная ветка на GitHub — `main`:

```bash
git branch -M main
git push -u origin main
```

Если GitHub попросит авторизацию: логин + пароль или Personal Access Token (рекомендуется). По SSH:

```bash
git remote set-url origin git@github.com:denisok-ai/LytSlot.git
git push -u origin main
```

---

## После пуша

- Дальнейшие изменения архитектуры — по плану в **docs/Architecture-Plan.md**.
- Каждую задачу из плана удобно делать в отдельном коммите (или отдельной ветке, затем merge в main).
