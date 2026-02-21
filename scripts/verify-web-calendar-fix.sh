#!/usr/bin/env bash
# Проверка, что в сборку web попадёт исправленный SlotsCalendar (eventClick as any).
# Запускайте из корня репозитория перед docker compose build.
set -e
FILE="${1:-services/web/components/calendar/SlotsCalendar.tsx}"
if ! grep -q 'as any' "$FILE" 2>/dev/null || ! grep -q 'eventClick=' "$FILE" 2>/dev/null; then
  echo "ОШИБКА: В файле $FILE нет фикса eventClick (ожидается 'as any' в обработчике)."
  echo "Сборка web упадёт. Обновите файл (git pull) или добавьте приведение типа в eventClick."
  exit 1
fi
echo "OK: фикс eventClick найден в $FILE"
