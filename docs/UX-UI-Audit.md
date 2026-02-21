# Аудит UX/UI и связей с API/БД

Проверка макетов страниц, отображаемых полей и соответствия API и БД (дата: 2025-02-20).

---

## 1. Обзор страниц и маршрутов

| Страница | Маршрут | Назначение |
|----------|---------|------------|
| Лендинг | `/` | Hero, возможности, CTA |
| Вход | `/login` | Telegram Login Widget + режим разработки |
| Callback | `/login/callback` | Обработка initData, сохранение JWT |
| Обзор | `/dashboard` | Сводные метрики, список каналов, плейсхолдер календаря |
| Каналы | `/dashboard/channels` | CRUD каналов (username, слот, цена, активность) |
| Календарь | `/dashboard/calendar` | Слоты по каналу, создание слота, форма заказа, FullCalendar |
| Заказы | `/dashboard/orders` | Список заказов, превью контента, смена статуса |
| Аналитика | `/dashboard/analytics` | Сводка (каналы, заказы, просмотры, выручка), график просмотров по дням |
| Настройки | `/dashboard/settings` | API-ключи: список, создание (показ ключа один раз), отзыв |

Навигация: сайдбар `DashboardShell` ведёт на все разделы; выход очищает токен и редиректит на `/`.

---

## 2. Поля и связи с API/БД

### 2.1 Каналы (channels)

- **API:** `GET/POST /api/channels`, `GET/PATCH /api/channels/:id`
- **Схема ответа:** id, tenant_id, username, slot_duration, price_per_slot, is_active
- **БД (Channel):** те же поля + created_at, updated_at (в API не отдаются — ок для MVP)
- **Фронт:** все поля из ответа отображаются и редактируются. Связь с БД через RLS (tenant_id).

**Итог:** поля совпадают, связи есть.

### 2.2 Слоты (slots)

- **API:** `GET /api/slots?channel_id=&date_from=&date_to=`, `POST /api/slots` (channel_id, datetime)
- **Схема ответа:** id, channel_id, datetime, status, created_at (SlotResponse)
- **БД (Slot):** id, channel_id, datetime, status, created_at
- **Фронт:** список слотов по каналу и периоду; создание слота (datetime-local → строка "YYYY-MM-DD HH:mm:00"); форма заказа (текст, ссылка). FullCalendar получает слоты с полями id, channel_id, datetime, status.

**Итог:** поля совпадают. Формат datetime принимается Pydantic.

### 2.3 Заказы (orders)

- **API:** `GET/POST /api/orders`, `GET/PATCH /api/orders/:id`
- **Схема ответа:** id, advertiser_id, channel_id, slot_id, content, erid, status, created_at, updated_at
- **БД (Order):** те же поля
- **Фронт:** таблица — ID (обрезанный), контент (превью text/link), статус (селект), дата создания. Не отображаются: channel_id, slot_id (какой канал/слот), erid, updated_at, advertiser_id — при необходимости можно добавить колонки или подсказки.

**Итог:** связи с БД есть; отображение минимальное, но достаточное для MVP. Статусы на фронте переведены на человекочитаемые подписи (Черновик, Оплачен и т.д.).

### 2.4 Аналитика (analytics)

- **API:** `GET /api/analytics/summary` → channels_count, orders_count, views_total, revenue_total; `GET /api/analytics/views?date_from=&date_to=&channel_id=` → [{ date, views }]
- **БД:** Channel, Order, View (hypertable TimescaleDB)
- **Фронт:** сводка в карточках; график Recharts по дням; фильтр по каналу и периоду (7/30/90 дней).

**Итог:** поля и связи есть. revenue_total в API пока 0 (задел под платежи).

### 2.5 API-ключи (api-keys)

- **API:** `GET/POST /api/api-keys`, `DELETE /api/api-keys/:id`
- **Ответ списка:** id, name, created_at, key_preview ("••••"); при создании — id, name, created_at, key (один раз)
- **БД (ApiKey):** id, tenant_id, key_hash, name, created_at
- **Фронт:** таблица (имя, ключ-preview, создан), форма создания (имя опционально), блок с показом нового ключа и копированием.

**Итог:** поля совпадают, связи есть.

### 2.6 Обзор (dashboard)

- **Было:** метрики «Заказы сегодня», «Выручка (мес)», «Слотов активно» — плейсхолдеры "—"; кнопка «Войти через Telegram» вела на `/api/auth/callback` (не страница входа).
- **Стало:** запрос к `GET /api/analytics/summary`; в карточках выводятся channels_count, orders_count, views_total, revenue_total; кнопка входа ведёт на `/login`.

---

## 3. UX/UI замечания и рекомендации

### Что сделано хорошо
- Единый стиль: DashboardShell, Card, Button, emerald-акцент, Plus Jakarta Sans (из конфига).
- Пустые состояния: «Пока нет каналов», «Пока нет заказов», «Нет слотов за период», «Нет данных за период» в аналитике.
- Ошибки: сообщения под формами и в карточках, подсказка про API на порту 8000 на странице каналов.
- Навигация: сайдбар с активным состоянием, выход из кабинета.
- Формы: лейблы, placeholder'ы, кнопки «Создать»/«Отмена»/«Сохранить».
- Защита дашборда: редирект на `/login` при отсутствии токена (layout).

### Рекомендации на будущее
- **Заказы:** при необходимости добавить колонки «Канал» и «Слот» (по channel_id/slot_id можно подгружать имена через API или расширить ответ orders вложенными объектами).
- **Каналы:** при необходимости показывать даты created_at/updated_at (потребуется добавить поля в ChannelResponse).
- **Обзор:** «Заказы сегодня» и «Слотов активно» можно считать отдельно (отдельный эндпоинт или расширить summary), если нужна именно дневная/активная метрика.
- **Доступность:** проверить фокус и aria-атрибуты в формах и модальных блоках.
- **Мобильная версия:** сайдбар фиксирован по ширине; на малых экранах рассмотреть выдвижное меню.

---

## 4. Сводная таблица: все ли поля отображаются

| Сущность | Поля в API/БД | Отображаются на фронте | Примечание |
|----------|----------------|------------------------|------------|
| Channel | id, tenant_id, username, slot_duration, price_per_slot, is_active | Да (все кроме tenant_id в списке) | tenant_id не нужен в UI |
| Slot | id, channel_id, datetime, status | Да | created_at не обязателен в списке |
| Order | id, advertiser_id, channel_id, slot_id, content, erid, status, created_at, updated_at | id, content (превью), status, created_at | channel/slot/erid/updated_at — опционально добавить |
| Summary | channels_count, orders_count, views_total, revenue_total | Да (в т.ч. на обзоре) | revenue_total пока 0 |
| Views | date, views | Да (график) | — |
| ApiKey | id, name, created_at, key_preview / key | Да | key только при создании |

**Вывод:** критические поля отображаются; связи с БД и API соответствуют контрактам. Недостающие отображения (например, канал/слот в заказе) помечены как рекомендации для следующих итераций.
