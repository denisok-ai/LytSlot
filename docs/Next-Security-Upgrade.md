# Next.js: уязвимости и обновление

## Текущее состояние (2025–2026)

В Next.js 10–15.x выявлены две уязвимости (npm audit):

| Advisory | Описание | Патч в 14.x? |
|----------|----------|--------------|
| **GHSA-9g9p-9gw9-jx7f** | DoS через Image Optimizer при настройке `remotePatterns` | Нет |
| **GHSA-h25m-26qc-wcjf** | DoS при десериализации запросов к Server Components (App Router) | Нет |

**Исправленные версии:** 15.5.10, 16.1.5 (и другие 15.x патч-релизы). Для ветки **14.x патчей нет**.

В проекте обновлено до: **Next.js 15.5.10**, React 19 (см. `services/web/package.json`).

---

## Вариант 1: Остаться на 14.x (снижение риска)

- **Image Optimizer (GHSA-9g9p-9gw9-jx7f):** в `next.config.js` не используется `images.remotePatterns`. Пока не добавляете загрузку внешних изображений через `/_next/image` с `remotePatterns` — эта уязвимость не задействована.
- **Server Components DoS (GHSA-h25m-26qc-wcjf):** приложение уязвимо к специально сформированным запросам к App Router. Смягчение: rate limiting (nginx, Cloudflare, WAF), ограничение размера тела запроса.

Имеет смысл не откладывать надолго обновление до патч-версии 15 или 16.

---

## Вариант 2: Обновиться до Next.js 15.5.10 (рекомендуется)

Получаете обе исправления без перехода на 16. Требуется **React 19** и правки по async API (params, cookies, headers и т.д.).

### Шаги

1. **Резервная копия и ветка**
   ```bash
   git checkout -b deps/next-15
   ```

2. **Автоматическая миграция (codemod)**
   ```bash
   cd services/web
   npx @next/codemod@canary upgrade latest
   ```
   Либо обновить только до 15.5.10 (без перехода на 16):
   ```bash
   npm install next@15.5.10 react@^19 react-dom@^19 eslint-config-next@15.5.10
   npm install -D @types/react@^19 @types/react-dom@^19
   ```

3. **Проверка кода**
   - В Next 15 `params` и `searchParams` в страницах/лейаутах приходят как **Promise** — нужно `await params` / `await searchParams`.
   - То же для `cookies()`, `headers()`, `draftMode()` — теперь async. В проекте пока почти не используются.
   - [Официальный гайд по переходу 14 → 15](https://nextjs.org/docs/app/guides/upgrading/version-15).

4. **Сборка и тесты**
   ```bash
   npm run build
   npm run dev
   ```

5. **Остальные уязвимости**
   После обновления Next выполните `npm audit` и при необходимости `npm audit fix` (без `--force`).

---

## Вариант 3: Обновиться до Next.js 16.x

Команда `npm audit fix --force` предлагает установить next@16.1.6. Это мажорное обновление, больше изменений и рисков. Имеет смысл переходить на 16 после успешного перехода на 15.5.10.
