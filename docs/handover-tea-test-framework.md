# TEA Agent Handover: Test Framework Setup

**From:** Bob (Scrum Master)
**To:** Murat (TEA - Test Engineering Agent)
**Date:** 2025-11-23
**Priority:** BLOCKER for Epic 2

---

## Executive Summary

You are tasked with creating the test framework infrastructure AND executing Story 0.1 (Test Infrastructure Setup). This is a single unified task - the framework creation IS the story implementation.

---

## Execution Order (Updated by TEA)

| Step | Task | Status |
|------|------|--------|
| 1 | Phase A: Tasks 1-8 (Story 0.1 Core) | **COMPLETE** |
| 2 | Phase B: Tasks 9-13 (Production Hardening) | **COMPLETE** |
| 3 | Verify all acceptance criteria (AC 1-10) | **COMPLETE** |
| 4 | Create governance documentation | **COMPLETE** |
| 5 | Return to SM for `*epic-retrospective` | **READY** |

---

## Governance Documentation Created

**Test Framework Specification:** `docs/test-framework-specification.md`

This document codifies the test framework as a mandatory standard for all future epics. It includes:
- Architecture overview and technology stack
- Test levels and marker definitions
- Directory structure requirements
- Fixture and factory patterns
- Quality standards and DoD
- CI/CD integration
- Migration guide for existing tests

---

## Story Reference

**Story File:** `docs/sprint-artifacts/0-1-test-infrastructure-setup.md`

---

## Current State Analysis

### Existing Test Structure
```
backend/tests/
├── __init__.py
├── conftest.py              # Has DB fixtures (Docker Compose dependent)
├── unit/
│   ├── __init__.py
│   ├── test_health.py
│   └── test_audit_service.py
└── integration/
    ├── __init__.py
    ├── test_service_connectivity.py
    ├── test_database.py
    ├── test_auth.py
    ├── test_users.py
    ├── test_password_reset.py
    ├── test_admin_users.py
    ├── test_audit_logging.py
    └── test_seed_data.py
```

### Current pyproject.toml Test Config
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "integration: marks tests as integration tests",
]
```

### Current Makefile Test Commands
```makefile
test-backend:
    cd backend && source .venv/bin/activate && pytest
```

### Current conftest.py
- Uses Docker Compose PostgreSQL (requires `docker compose up`)
- Has `test_engine`, `setup_database`, `db_session` fixtures
- No testcontainers integration
- No Redis fixtures

---

## Gap Analysis (What Needs to Change)

### Phase A Gaps (Story 0.1 Core)

| Area | Current | Required | Gap |
|------|---------|----------|-----|
| **Test Dependencies** | pytest, pytest-asyncio, pytest-cov | + testcontainers[postgres,redis] | MISSING |
| **Pytest Markers** | Only `integration` | + `unit`, `e2e` | MISSING |
| **Makefile Commands** | `test-backend` only | `test-unit`, `test-integration`, `test-all`, `test-coverage` | MISSING |
| **Unit conftest** | None | Separate conftest without DB fixtures | MISSING |
| **Integration fixtures** | Docker Compose dependent | Testcontainers (self-contained) | REFACTOR |

### Phase B Gaps (Production Hardening - Added by TEA)

| Area | Current | Required | Gap | Risk |
|------|---------|----------|-----|------|
| **Data Factories** | None | faker-based factories with overrides | MISSING | MEDIUM |
| **Fixture Architecture** | Basic db_session | Composable auth/API fixtures | MISSING | LOW-MEDIUM |
| **CI Pipeline** | None | GitHub Actions with lint/test/coverage | MISSING | HIGH |
| **Quality Enforcement** | None | pytest-timeout, strict markers | MISSING | LOW |
| **Documentation** | None | Test README with marker strategy | MISSING | LOW |

---

## Implementation Tasks (Aligned with Story 0.1)

### Task 1: Install Test Dependencies
**File:** `backend/pyproject.toml`

Add to `[project.optional-dependencies]` dev section:
```toml
dev = [
    # ... existing ...
    "testcontainers[postgres,redis]>=4.0.0",
]
```

Then run: `pip install -e ".[dev]"`

---

### Task 2: Configure Pytest Markers
**File:** `backend/pyproject.toml`

Update `[tool.pytest.ini_options]`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short -m 'not e2e' --strict-markers"
markers = [
    "unit: Fast tests without external dependencies",
    "integration: Tests requiring testcontainers (PostgreSQL, Redis)",
    "e2e: Full stack tests requiring docker-compose",
]
```

---

### Task 3: Create Unit Test conftest
**File:** `backend/tests/unit/conftest.py`

Create minimal conftest for unit tests (NO database fixtures):
```python
"""Unit test configuration - no external dependencies."""

import pytest

# Unit tests should NOT use database fixtures
# If a test needs DB, move it to integration/
```

---

### Task 4: Implement Testcontainers Fixtures
**File:** `backend/tests/integration/conftest.py`

Create new file with testcontainers-based fixtures:
```python
"""Integration test fixtures using testcontainers."""

import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    """Session-scoped PostgreSQL container."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Async-compatible connection URL."""
    url = postgres_container.get_connection_url()
    return url.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def redis_container():
    """Session-scoped Redis container."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def redis_url(redis_container):
    """Redis connection URL."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


@pytest.fixture(scope="session")
async def test_engine(postgres_url):
    """Create async engine for test database."""
    engine = create_async_engine(postgres_url, echo=False)

    # Create schema and tables once per session
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """
    Function-scoped session with automatic rollback.
    Each test gets isolated database state.
    """
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

---

### Task 5: Update Root conftest.py
**File:** `backend/tests/conftest.py`

Refactor to be minimal (shared across unit and integration):
```python
"""Shared pytest fixtures."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set debug mode BEFORE importing app
os.environ.setdefault("LUMIKB_DEBUG", "true")

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

---

### Task 6: Update Makefile
**File:** `Makefile`

Add new test targets:
```makefile
# Testing (updated)
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
```

---

### Task 7: Mark Existing Tests with Markers

Add `@pytest.mark.unit` to:
- `backend/tests/unit/test_health.py`
- `backend/tests/unit/test_audit_service.py`

Add `@pytest.mark.integration` to all files in `backend/tests/integration/`

---

### Task 8: Create Example Tests (Verify Setup)

Create one new unit test and verify one integration test works with testcontainers.

---

## Phase B: Production Hardening (Gap Closure)

> **Added by TEA (Murat)** after gap analysis against test framework best practices.
> These tasks close gaps identified in fixture architecture, data factories, CI pipeline, and quality enforcement.

---

### Task 9: Create Data Factory Infrastructure
**Risk:** MEDIUM - Without factories, tests use hardcoded data causing parallel collisions and schema drift.

**Files:**
- `backend/tests/factories/__init__.py`
- `backend/tests/factories/user_factory.py`
- `backend/tests/factories/document_factory.py`

**Implementation:**
```python
# backend/tests/factories/__init__.py
"""Test data factories for parallel-safe, schema-resilient test data."""

from .user_factory import create_user, create_admin_user
from .document_factory import create_document

__all__ = ["create_user", "create_admin_user", "create_document"]
```

```python
# backend/tests/factories/user_factory.py
"""User factory with sensible defaults and explicit overrides."""

from typing import Any
from faker import Faker
import uuid

fake = Faker()


def create_user(**overrides: Any) -> dict:
    """
    Factory function for user test data.

    Usage:
        user = create_user()  # All defaults
        admin = create_user(is_superuser=True)  # Override specific fields
    """
    return {
        "id": overrides.get("id", str(uuid.uuid4())),
        "email": overrides.get("email", fake.email()),
        "username": overrides.get("username", fake.user_name()),
        "full_name": overrides.get("full_name", fake.name()),
        "hashed_password": overrides.get("hashed_password", "hashed_test_password_123"),
        "is_active": overrides.get("is_active", True),
        "is_superuser": overrides.get("is_superuser", False),
        **{k: v for k, v in overrides.items() if k not in [
            "id", "email", "username", "full_name",
            "hashed_password", "is_active", "is_superuser"
        ]},
    }


def create_admin_user(**overrides: Any) -> dict:
    """Convenience factory for admin users."""
    return create_user(is_superuser=True, **overrides)
```

```python
# backend/tests/factories/document_factory.py
"""Document factory for knowledge base test data."""

from typing import Any
from faker import Faker
import uuid

fake = Faker()


def create_document(**overrides: Any) -> dict:
    """Factory function for document test data."""
    return {
        "id": overrides.get("id", str(uuid.uuid4())),
        "title": overrides.get("title", fake.sentence(nb_words=5)),
        "content": overrides.get("content", fake.paragraphs(nb=3)),
        "owner_id": overrides.get("owner_id", str(uuid.uuid4())),
        "is_public": overrides.get("is_public", False),
        "created_at": overrides.get("created_at", fake.date_time_this_year()),
        **{k: v for k, v in overrides.items() if k not in [
            "id", "title", "content", "owner_id", "is_public", "created_at"
        ]},
    }
```

**Dependencies:** Add `faker>=24.0.0` to `[project.optional-dependencies]` dev section.

---

### Task 10: Enhance Fixture Architecture
**Risk:** LOW-MEDIUM - Current conftest is functional but not composable.

**Files:**
- `backend/tests/fixtures/__init__.py`
- `backend/tests/fixtures/auth_fixtures.py`

**Implementation:**
```python
# backend/tests/fixtures/__init__.py
"""Composable test fixtures following pure-function-first pattern."""

from .auth_fixtures import test_user, authenticated_client, admin_user

__all__ = ["test_user", "authenticated_client", "admin_user"]
```

```python
# backend/tests/fixtures/auth_fixtures.py
"""Authentication fixtures with automatic cleanup."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from tests.factories import create_user, create_admin_user
from app.models.user import User
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """
    Create test user in database with automatic rollback cleanup.

    Returns dict with user data + raw password for auth testing.
    """
    user_data = create_user()
    raw_password = "test_password_123"

    user = User(
        id=user_data["id"],
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data["full_name"],
        hashed_password=get_password_hash(raw_password),
        is_active=user_data["is_active"],
        is_superuser=user_data["is_superuser"],
    )
    db_session.add(user)
    await db_session.flush()

    return {**user_data, "raw_password": raw_password}


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> dict:
    """Create admin user in database."""
    user_data = create_admin_user()
    raw_password = "admin_password_123"

    user = User(
        id=user_data["id"],
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data["full_name"],
        hashed_password=get_password_hash(raw_password),
        is_active=user_data["is_active"],
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()

    return {**user_data, "raw_password": raw_password}


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: dict) -> AsyncClient:
    """
    AsyncClient with Bearer token injected.

    Usage:
        async def test_protected_endpoint(authenticated_client):
            response = await authenticated_client.get("/api/v1/protected")
            assert response.status_code == 200
    """
    token = create_access_token(subject=test_user["id"])
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

**Note:** Update `backend/tests/integration/conftest.py` to import these fixtures.

---

### Task 11: Create CI Pipeline
**Risk:** HIGH - No CI = no quality gate.

**File:** `.github/workflows/test.yml`

**Implementation:**
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run ruff check
        run: cd backend && ruff check .

      - name: Run ruff format check
        run: cd backend && ruff format --check .

  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          cd backend
          pytest -m unit -v --tb=short --timeout=30

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: unit-test-results
          path: backend/test-results/
          retention-days: 7

  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run integration tests
        run: |
          cd backend
          pytest -m integration -v --tb=short --timeout=90

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-results
          path: backend/test-results/
          retention-days: 7

  coverage:
    name: Coverage Report
    runs-on: ubuntu-latest
    needs: [test-unit, test-integration]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term-missing -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          fail_ci_if_error: false
```

---

### Task 12: Add Quality Enforcement Config
**Risk:** LOW - Enforces test quality standards.

**File:** `backend/pyproject.toml` (update)

**Add to `[project.optional-dependencies]` dev section:**
```toml
"pytest-timeout>=2.3.0",
```

**Update `[tool.pytest.ini_options]`:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short -m 'not e2e' --strict-markers --timeout=90"
timeout_method = "thread"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::pytest.PytestUnraisableExceptionWarning",
]
markers = [
    "unit: Fast tests without external dependencies (<5s each)",
    "integration: Tests requiring testcontainers (PostgreSQL, Redis)",
    "e2e: Full stack tests requiring docker-compose",
    "smoke: Critical path tests for quick validation",
    "slow: Tests taking >30s, excluded from default runs",
]
```

---

### Task 13: Expand Marker Strategy Documentation
**Risk:** LOW - Documents when to use which marker.

**File:** `backend/tests/README.md`

**Implementation:**
```markdown
# Test Suite Documentation

## Test Markers

| Marker | Use When | Execution Time | Dependencies |
|--------|----------|----------------|--------------|
| `@pytest.mark.unit` | Testing pure functions, business logic | <5s | None |
| `@pytest.mark.integration` | Testing DB operations, API contracts | <30s | Testcontainers |
| `@pytest.mark.e2e` | Testing full user journeys | <90s | Docker Compose |
| `@pytest.mark.smoke` | Critical path quick validation | <10s | Varies |
| `@pytest.mark.slow` | Long-running tests (load, stress) | >30s | Varies |

## Running Tests

```bash
# Unit tests only (fast feedback)
make test-unit

# Integration tests (requires Docker)
make test-integration

# All tests except E2E
make test-all

# With coverage report
make test-coverage

# Specific marker
cd backend && pytest -m "smoke" -v
```

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures (client, env setup)
├── factories/               # Data factories (create_user, create_document)
│   ├── __init__.py
│   ├── user_factory.py
│   └── document_factory.py
├── fixtures/                # Composable fixtures (auth, api)
│   ├── __init__.py
│   └── auth_fixtures.py
├── unit/                    # Unit tests (no external deps)
│   ├── conftest.py
│   ├── test_health.py
│   └── test_audit_service.py
└── integration/             # Integration tests (testcontainers)
    ├── conftest.py
    ├── test_auth.py
    └── test_users.py
```

## Writing Tests

### Unit Test Example
```python
import pytest
from app.utils.validators import validate_email

@pytest.mark.unit
def test_validate_email_accepts_valid_email():
    assert validate_email("user@example.com") is True

@pytest.mark.unit
def test_validate_email_rejects_invalid_email():
    assert validate_email("not-an-email") is False
```

### Integration Test Example
```python
import pytest
from tests.factories import create_user

@pytest.mark.integration
async def test_create_user_persists_to_database(db_session, client):
    user_data = create_user(email="test@example.com")
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
```
```

---

## Acceptance Criteria Checklist

### Phase A - Story 0.1 (REQUIRED)

| AC | Criteria | Verification Command |
|----|----------|---------------------|
| 1 | `make test-unit` runs without Docker, < 30s | `time make test-unit` |
| 2 | `make test-integration` uses testcontainers | `make test-integration` (no docker compose needed) |
| 3 | DB changes rollback after each test | Check test isolation |
| 4 | `make test-all` runs both suites | `make test-all` |
| 5 | Directory structure matches spec | `tree backend/tests/` |

### Phase B - Production Hardening (RECOMMENDED)

| AC | Criteria | Verification Command |
|----|----------|---------------------|
| 6 | Data factories generate unique test data | `pytest tests/factories/ -v` |
| 7 | Auth fixtures provide authenticated client | `pytest -m integration -k auth -v` |
| 8 | CI pipeline defined | `cat .github/workflows/test.yml` |
| 9 | Tests have timeout enforcement | Check `pyproject.toml` for timeout config |
| 10 | Test README documents marker strategy | `cat backend/tests/README.md` |

---

## Out of Scope (DO NOT IMPLEMENT)

- Qdrant testcontainer (Story 2.6)
- MinIO testcontainer (Story 2.4)
- E2E/Playwright setup (before Epic 3)
- Frontend test infrastructure
- Coverage thresholds

---

## Architecture Constraints

From `docs/architecture.md`:
- Python 3.11+
- PostgreSQL 16
- Redis 7+
- pytest-asyncio with `asyncio_mode = "auto"`

---

## References

- Story File: `docs/sprint-artifacts/0-1-test-infrastructure-setup.md`
- Architecture: `docs/architecture.md`
- Meeting Minutes: `docs/meeting-minutes-party-mode-2025-11-23.md`
- Testcontainers Docs: https://testcontainers-python.readthedocs.io/

---

## Handoff Confirmation

Once all tasks complete and ACs pass:
1. Mark story tasks as complete in the story file
2. Update story status from `draft` to `done`
3. Return control to SM (Bob) for `*epic-retrospective`

---

**SM Sign-off:** Bob (Scrum Master)
**Date:** 2025-11-23
