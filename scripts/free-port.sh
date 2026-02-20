#!/usr/bin/env bash
# Освобождает порт (по умолчанию 3000). Запускать из WSL/Ubuntu: bash scripts/free-port.sh [PORT]
set -e
PORT="${1:-3000}"
if ! command -v lsof &>/dev/null; then
  echo "Установите lsof: sudo apt install lsof"
  exit 1
fi
PID=$(lsof -t -i ":$PORT" 2>/dev/null || true)
if [ -z "$PID" ]; then
  echo "Порт $PORT не занят."
  exit 0
fi
echo "Порт $PORT занят процессом PID=$PID. Завершаю..."
kill -9 $PID 2>/dev/null || true
echo "Готово. Запустите сервер снова."
