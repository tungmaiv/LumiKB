SHELL := /bin/bash
.PHONY: dev test lint migrate seed docker-build clean help test-backend test-unit test-integration test-all test-coverage test-frontend test-frontend-watch test-frontend-coverage test-e2e test-e2e-ui test-e2e-headed

# Default target
help:
	@echo "LumiKB Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev                Start infrastructure services"
	@echo "  make dev-backend        Start backend server"
	@echo "  make dev-frontend       Start frontend server"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run all tests"
	@echo "  make test-backend       Run all backend tests"
	@echo "  make test-unit          Run backend unit tests only"
	@echo "  make test-integration   Run backend integration tests (Docker required)"
	@echo "  make test-all           Run all backend tests"
	@echo "  make test-coverage      Run backend tests with coverage"
	@echo "  make test-frontend      Run frontend tests"
	@echo "  make test-frontend-watch  Run frontend tests in watch mode"
	@echo "  make test-frontend-coverage  Run frontend tests with coverage"
	@echo "  make test-e2e           Run E2E tests (Playwright)"
	@echo "  make test-e2e-ui        Run E2E tests with UI"
	@echo "  make test-e2e-headed    Run E2E tests in headed mode"
	@echo ""
	@echo "Linting:"
	@echo "  make lint               Run all linters"
	@echo "  make lint-backend       Run backend linters (ruff)"
	@echo "  make lint-frontend      Run frontend linters (eslint)"
	@echo ""
	@echo "Other:"
	@echo "  make migrate            Run database migrations"
	@echo "  make seed               Seed sample data"
	@echo "  make docker-build       Build production images"
	@echo "  make clean              Clean build artifacts"

# Docker compose file location
DOCKER_COMPOSE := docker compose -f infrastructure/docker/docker-compose.yml

# Development
dev:
	$(DOCKER_COMPOSE) up -d postgres qdrant minio redis
	@echo "Infrastructure services started"
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

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
