# Story 0.1: Test Infrastructure Setup

Status: draft

## Story

As a **developer**,
I want **a robust test infrastructure with proper isolation and pytest markers**,
So that **I can write reliable tests that run consistently in local dev and CI/CD**.

## Priority

**BLOCKER for Epic 2** - Must be completed before starting Epic 2 stories.

## Estimate

2-4 hours focused work

## Acceptance Criteria

1. **Given** I want to run fast unit tests **When** I execute `make test-unit` **Then** tests run without requiring Docker or any external services **And** complete in under 30 seconds

2. **Given** I want to run integration tests **When** I execute `make test-integration` **Then** testcontainers automatically provision PostgreSQL and Redis **And** each test session gets fresh, isolated containers **And** containers are destroyed after tests complete

3. **Given** I have a test that modifies database state **When** the test completes (pass or fail) **Then** all changes are rolled back **And** the next test starts with clean state

4. **Given** I want to run all tests **When** I execute `make test-all` **Then** both unit and integration tests run **And** a coverage report is generated

5. **Given** the test infrastructure is set up **When** I check the project structure **Then** I see organized test directories:
   - `backend/tests/unit/` for unit tests
   - `backend/tests/integration/` for integration tests
   - `backend/tests/conftest.py` with shared fixtures

## Tasks / Subtasks

- [ ] **Task 1: Install test dependencies** (AC: 2)
  - [ ] Add testcontainers[postgres,redis] to pyproject.toml dev dependencies
  - [ ] Add pytest-cov for coverage reporting
  - [ ] Run `pip install -e ".[dev]"` to install

- [ ] **Task 2: Configure pytest markers** (AC: 1, 2)
  - [ ] Update `pytest.ini` or `pyproject.toml` with markers:
    - `unit`: Fast tests without external dependencies
    - `integration`: Tests requiring testcontainers
    - `e2e`: Full stack tests (future use)
  - [ ] Set default to skip e2e tests: `addopts = -m "not e2e"`

- [ ] **Task 3: Create test directory structure** (AC: 5)
  - [ ] Create `backend/tests/unit/` directory
  - [ ] Create `backend/tests/unit/conftest.py` (no DB fixtures)
  - [ ] Update `backend/tests/integration/conftest.py` for testcontainers
  - [ ] Add `__init__.py` files as needed

- [ ] **Task 4: Implement testcontainers fixtures** (AC: 2, 3)
  - [ ] Create PostgreSQL container fixture (session-scoped)
  - [ ] Create Redis container fixture (session-scoped)
  - [ ] Create async database session fixture with transaction rollback
  - [ ] Ensure Alembic migrations run on test database

- [ ] **Task 5: Create Makefile test commands** (AC: 1, 2, 4)
  - [ ] Add `test-unit` target
  - [ ] Add `test-integration` target
  - [ ] Add `test-all` target
  - [ ] Add `test-coverage` target with HTML report

- [ ] **Task 6: Create example tests** (AC: 1, 2, 3)
  - [ ] Create one example unit test (e.g., test a utility function)
  - [ ] Migrate one existing integration test to use testcontainers pattern
  - [ ] Verify transaction rollback works correctly

- [ ] **Task 7: Document test infrastructure** (AC: 5)
  - [ ] Add comments in conftest.py explaining fixture usage
  - [ ] Update any existing test documentation

## Dev Notes

### Architecture Constraints

From [architecture.md](../architecture.md):
- Python 3.11 required
- PostgreSQL 16 for database
- Redis 7+ for cache/sessions
- pytest with async support (pytest-asyncio)

### Testcontainers Pattern

```python
# backend/tests/integration/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
def postgres_container():
    """Session-scoped PostgreSQL container"""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Async-compatible connection URL"""
    # testcontainers returns sync URL, convert to async
    url = postgres_container.get_connection_url()
    return url.replace("postgresql://", "postgresql+asyncpg://")

@pytest.fixture(scope="session")
def redis_container():
    """Session-scoped Redis container"""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture
async def db_session(postgres_url):
    """
    Function-scoped session with automatic rollback.
    Each test gets isolated database state.
    """
    engine = create_async_engine(postgres_url)

    # Run migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()

    await engine.dispose()
```

### Pytest Markers Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Fast tests without external dependencies",
    "integration: Tests requiring testcontainers (PostgreSQL, Redis)",
    "e2e: Full stack tests requiring docker-compose",
]
addopts = "-m 'not e2e' --strict-markers"
asyncio_mode = "auto"
```

### Makefile Commands

```makefile
.PHONY: test test-unit test-integration test-all test-coverage

test-unit:
	cd backend && pytest -m unit -v

test-integration:
	cd backend && pytest -m integration -v

test-all:
	cd backend && pytest -v

test-coverage:
	cd backend && pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: backend/htmlcov/index.html"
```

### Current State (from Epic 1)

Existing test files:
- `backend/tests/conftest.py` - Has async fixtures for Docker Compose
- `backend/tests/integration/test_service_connectivity.py` - 7 tests (Docker Compose dependent)
- `backend/tests/unit/test_config.py` - 2 unit tests exist

### Out of Scope

The following are explicitly OUT OF SCOPE for this story:
- Qdrant testcontainer (will be added in Story 2.6)
- MinIO testcontainer (will be added in Story 2.4)
- E2E/Playwright setup (will be added before Epic 3)
- Frontend test infrastructure (separate story if needed)
- Full coverage thresholds and enforcement

### Dependencies

- Story 1.2 (Database Schema) - COMPLETED
- Story 1.3 (Docker Compose) - COMPLETED

### References

- [Meeting Minutes - Party Mode 2025-11-23](../meeting-minutes-party-mode-2025-11-23.md)
- [Architecture Document](../architecture.md)
- [Testcontainers Python Docs](https://testcontainers-python.readthedocs.io/)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-23 | Initial draft created from party-mode discussion | Murat (TEA) |
