#!/usr/bin/env bash
# @file: podman-up.sh
# @description: Полный перезапуск стека под Podman (сборка + up). Устраняет ошибки зависимостей и short-name.
# @dependencies: podman-compose
# @created: 2025-02-20
set -e
cd "$(dirname "$0")/.."
echo "=== LytSlot: остановка и удаление контейнеров (без очистки граф зависимостей ломается при повторном up) ==="
podman-compose -f infra/docker-compose.yml down --remove-orphans 2>/dev/null || true
# Удалить возможные «висячие» контейнеры проекта по метке
podman ps -a --filter "label=io.podman.compose.project=infra" -q 2>/dev/null | xargs -r podman rm -f 2>/dev/null || true
echo "=== сборка образов ==="
podman-compose -f infra/docker-compose.yml build
echo "=== запуск контейнеров ==="
podman-compose -f infra/docker-compose.yml up -d
echo "=== готово. API: http://localhost:8000/docs ==="
