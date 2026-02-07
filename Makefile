.PHONY: help up down restart logs build clean health test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-app: ## View logs from app service
	docker-compose logs -f app

logs-qdrant: ## View logs from qdrant service
	docker-compose logs -f qdrant

build: ## Build the app image
	docker-compose build

rebuild: ## Rebuild and restart services
	docker-compose up -d --build

clean: ## Stop and remove all containers, volumes, and images
	docker-compose down -v
	docker system prune -f

health: ## Check health of all services
	@echo "=== Service Status ==="
	docker-compose ps
	@echo ""
	@echo "=== App Health Check ==="
	curl -s http://localhost:8000/api/v1/health | jq . || echo "App not responding"
	@echo ""
	@echo "=== Qdrant Health Check ==="
	curl -s http://localhost:6333/health | jq . || echo "Qdrant not responding"

test: ## Run tests
	docker-compose exec app uv run pytest

shell: ## Open shell in app container
	docker-compose exec app bash

install: ## Setup environment file
	@if [ ! -f .env ]; then \
		cp .env.docker.example .env; \
		echo "Created .env file. Please edit it and add your OPENAI_API_KEY."; \
	else \
		echo ".env file already exists."; \
	fi
