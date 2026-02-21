# LytSlot Pro — удобные команды для разработки и деплоя
# Использование: make <цель>
# На сервере с Podman используйте скрипт: ./scripts/deploy-update.sh (он сам выберет docker/podman)

COMPOSE_FILE := infra/docker-compose.yml
COMPOSE_PROFILE := --profile full
# Автоопределение: docker compose или podman-compose
COMPOSE_CMD := $(shell (command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 && echo "docker compose") || (command -v podman-compose >/dev/null 2>&1 && echo "podman-compose") || echo "docker compose")

.PHONY: help deploy-update deploy-pull-update deploy-up deploy-build deploy-logs deploy-ps deploy-down \
	ci-local docker-up docker-up-minimal

help:
	@echo "LytSlot Pro — основные команды"
	@echo ""
	@echo "Деплой на сервере (Docker/Podman):"
	@echo "  make deploy-update        обновить стек (build + up -d + миграции)"
	@echo "  make deploy-pull-update   git pull и обновить стек"
	@echo "  make deploy-up            только поднять контейнеры (без сборки)"
	@echo "  make deploy-build         только собрать образы"
	@echo "  make deploy-logs          логи всех сервисов"
	@echo "  make deploy-ps            список контейнеров"
	@echo "  make deploy-down          остановить контейнеры"
	@echo ""
	@echo "Локально:"
	@echo "  make docker-up            полный стек (docker compose)"
	@echo "  make docker-up-minimal    минимальный стек (без бота и воркера)"
	@echo "  make ci-local             линтеры и тесты как в CI"

# Обновление (локально Podman или на сервере Docker)
deploy-update:
	bash scripts/deploy-update.sh

deploy-pull-update:
	bash scripts/deploy-update.sh --pull

deploy-up:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) $(COMPOSE_PROFILE) up -d

deploy-build:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) build

deploy-logs:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) $(COMPOSE_PROFILE) logs -f

deploy-ps:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) $(COMPOSE_PROFILE) ps

deploy-down:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) $(COMPOSE_PROFILE) down

# Локальный запуск стека (один раз поднять)
docker-up:
	./scripts/docker-up-full.sh

docker-up-minimal:
	./scripts/docker-up-full.sh --minimal

# Проверка как в CI (без Docker)
ci-local:
	ruff check db shared services tests
	black --check db shared services tests
	cd services/web && npm ci && npm run lint && npm run build
	pytest tests/ -v --tb=short
