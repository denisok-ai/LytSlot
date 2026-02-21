#!/usr/bin/env bash
# Запуск с вашей машины: подключается к серверу по SSH и выполняет полное развёртывание с нуля.
# Вам нужно будет ввести: 1) пароль от сервера (SSH), 2) при приватном репо — логин и токен GitHub.
#
# Использование:
#   ./scripts/deploy-from-local.sh
#   ./scripts/deploy-from-local.sh 72.56.117.159
#   SERVER_USER=root REPO_URL=https://github.com/ВАШ/LytSlot.git ./scripts/deploy-from-local.sh 72.56.117.159
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_IP="${1:-72.56.117.159}"
SERVER_USER="${SERVER_USER:-root}"
REPO_URL="${REPO_URL:-https://github.com/denisok-ai/LytSlot.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/lytslot}"

echo "Сервер: $SERVER_USER@$SERVER_IP"
echo "Репозиторий: $REPO_URL (ветка: $BRANCH)"
echo "Каталог на сервере: $INSTALL_DIR"
echo ""
echo "Сейчас будет запрошен пароль от сервера (SSH)."
echo "Если репозиторий приватный — затем на сервере запросят логин и пароль (или токен) GitHub."
echo ""
read -r -p "Нажмите Enter для продолжения..."

ssh -o StrictHostKeyChecking=accept-new "$SERVER_USER@$SERVER_IP" \
  "REPO_URL='$REPO_URL' BRANCH='$BRANCH' INSTALL_DIR='$INSTALL_DIR' bash -s" \
  < "$SCRIPT_DIR/server-bootstrap.sh"

echo ""
echo "Развёртывание завершено. Откройте в браузере:"
echo "  http://$SERVER_IP:3000"
echo "  http://$SERVER_IP:8000/docs"
