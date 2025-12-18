SHELL := /bin/bash
.PHONY: dev dev-stop dev-restart test lint migrate seed docker-build clean help test-backend test-unit test-integration test-all test-coverage test-frontend test-frontend-watch test-frontend-coverage test-e2e test-e2e-ui test-e2e-headed logs logs-errors logs-warnings logs-follow logs-celery logs-backend dev-backend-logs prune-doc prune-all check-consistency fix-consistency clear-observability

# Default target
help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                    LumiKB Development Commands                   ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Development:"
	@echo "  make dev                  Start all infrastructure (postgres, qdrant, minio, redis, litellm, celery)"
	@echo "  make dev-stop             Stop infrastructure services"
	@echo "  make dev-restart          Restart infrastructure services"
	@echo "  make dev-backend          Start backend server (uvicorn on port 8000)"
	@echo "  make dev-frontend         Start frontend server (Next.js dev mode)"
	@echo "  make dev-backend-logs     Start backend with output to logs/backend.log"
	@echo ""
	@echo "Logs:"
	@echo "  make logs                 View all container logs"
	@echo "  make logs-errors          View ERROR logs from all containers"
	@echo "  make logs-warnings        View WARNING logs from all containers"
	@echo "  make logs-follow          Follow logs from all containers (live)"
	@echo "  make logs-celery          View Celery worker and beat logs"
	@echo "  make logs-backend         View specific container logs (usage: make logs-backend SERVICE=postgres)"
	@echo ""
	@echo "Backend Testing:"
	@echo "  make test-backend         Run all backend tests"
	@echo "  make test-unit            Run backend unit tests only"
	@echo "  make test-integration     Run backend integration tests (Docker required)"
	@echo "  make test-all             Run all backend tests with verbose output"
	@echo "  make test-coverage        Run backend tests with coverage report"
	@echo ""
	@echo "Frontend Testing:"
	@echo "  make test-frontend        Run frontend tests"
	@echo "  make test-frontend-watch  Run frontend tests in watch mode"
	@echo "  make test-frontend-coverage  Run frontend tests with coverage"
	@echo ""
	@echo "E2E Testing:"
	@echo "  make test-e2e             Run E2E tests (Playwright)"
	@echo "  make test-e2e-ui          Run E2E tests with Playwright UI"
	@echo "  make test-e2e-headed      Run E2E tests in headed browser mode"
	@echo ""
	@echo "All Tests:"
	@echo "  make test                 Run all tests (backend + frontend)"
	@echo ""
	@echo "Linting:"
	@echo "  make lint                 Run all linters (backend + frontend)"
	@echo "  make lint-backend         Run backend linters (ruff check + format)"
	@echo "  make lint-frontend        Run frontend linters (eslint)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate              Run database migrations (alembic upgrade head)"
	@echo "  make seed                 Seed sample data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build         Build production Docker images"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Clean build artifacts (__pycache__, node_modules, etc.)"
	@echo ""
	@echo "Data Management:"
	@echo "  make prune-doc DOC_ID=<uuid>  Delete specific document and all related data"
	@echo "  make prune-all                Delete ALL documents (requires confirmation)"
	@echo "  make check-consistency        Check for orphan items across all data stores"
	@echo "  make fix-consistency          Check and fix orphan items (auto-cleanup)"
	@echo "  make clear-observability      Clear all traces, spans, metrics, and audit events"

# Docker compose file location
DOCKER_COMPOSE := docker compose -f infrastructure/docker/docker-compose.yml

# Development
dev:
	$(DOCKER_COMPOSE) up -d postgres qdrant minio redis litellm celery-worker celery-beat
	@echo "Infrastructure services started (including Celery workers)"
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-stop:
	$(DOCKER_COMPOSE) down
	@echo "Infrastructure services stopped"

dev-restart:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d postgres qdrant minio redis litellm celery-worker celery-beat
	@echo "Infrastructure services restarted (including Celery workers)"

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-backend-logs:
	@mkdir -p logs
	@echo "Starting backend with logs output to logs/backend.log"
	@echo "Use 'tail -f logs/backend.log' in another terminal to follow"
	@echo "Press Ctrl+C to stop"
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | tee ../logs/backend.log

# Logs
logs:
	$(DOCKER_COMPOSE) logs --tail=100

logs-errors:
	@echo "=== ERROR logs from all containers ==="
	$(DOCKER_COMPOSE) logs --tail=500 2>&1 | grep -i "error" || echo "No errors found"

logs-warnings:
	@echo "=== WARNING logs from all containers ==="
	$(DOCKER_COMPOSE) logs --tail=500 2>&1 | grep -i "warning\|warn" || echo "No warnings found"

logs-follow:
	$(DOCKER_COMPOSE) logs -f

logs-celery:
	@echo "=== Celery Worker Logs ==="
	$(DOCKER_COMPOSE) logs celery-worker --tail=50
	@echo ""
	@echo "=== Celery Beat Logs ==="
	$(DOCKER_COMPOSE) logs celery-beat --tail=50

logs-backend:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make logs-backend SERVICE=<service_name>"; \
		echo "Available services: postgres, redis, qdrant, minio, litellm, celery-worker, celery-beat"; \
	else \
		$(DOCKER_COMPOSE) logs $(SERVICE) --tail=100 -f; \
	fi

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && source .venv/bin/activate && pytest

test-unit:
	cd backend && source .venv/bin/activate && pytest -m unit -v

test-integration:
	cd backend && source .venv/bin/activate && pytest -m integration -v

test-all:
	cd backend && source .venv/bin/activate && pytest -v

test-coverage:
	cd backend && source .venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: backend/htmlcov/index.html"

test-frontend:
	cd frontend && npm run test:run

test-frontend-watch:
	cd frontend && npm test

test-frontend-coverage:
	cd frontend && npm run test:coverage

test-e2e:
	cd frontend && npm run test:e2e

test-e2e-ui:
	cd frontend && npm run test:e2e:ui

test-e2e-headed:
	cd frontend && npm run test:e2e:headed

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && source .venv/bin/activate && ruff check . && ruff format --check .

lint-frontend:
	cd frontend && npm run lint

# Database
migrate:
	cd backend && source .venv/bin/activate && alembic upgrade head

seed:
	./infrastructure/scripts/seed-data.sh

# Docker
docker-build:
	$(DOCKER_COMPOSE) build

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts"

# Data Management
prune-doc:
	@if [ -z "$(DOC_ID)" ]; then \
		echo "Usage: make prune-doc DOC_ID=<document-uuid>"; \
		echo "Example: make prune-doc DOC_ID=550e8400-e29b-41d4-a716-446655440000"; \
		exit 1; \
	fi
	./infrastructure/scripts/prune-documents.sh $(DOC_ID)

prune-all:
	./infrastructure/scripts/prune-documents.sh --all

check-consistency:
	./infrastructure/scripts/check-consistency.sh

fix-consistency:
	./infrastructure/scripts/check-consistency.sh --fix

clear-observability:
	@echo "Clearing all observability data..."
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE observability.spans CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE observability.traces CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE observability.document_events CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE observability.chat_messages CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE observability.metrics_aggregates CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE audit.events CASCADE;" > /dev/null
	@docker exec lumikb-postgres psql -U lumikb -d lumikb -c "TRUNCATE TABLE public.kb_access_log CASCADE;" > /dev/null
	@docker exec lumikb-redis redis-cli FLUSHALL > /dev/null
	@echo "All observability data cleared (traces, spans, metrics, audit events, Redis cache)"
