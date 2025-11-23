# LumiKB Test Framework Specification

**Version:** 1.0.0
**Effective Date:** 2025-11-23
**Owner:** TEA (Test Engineering Agent)
**Status:** APPROVED

---

## Executive Summary

This document defines the mandatory test framework architecture for the LumiKB project. All future epics, stories, and code changes MUST adhere to these specifications. Deviations require explicit approval and documented rationale.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Test Levels & Markers](#test-levels--markers)
3. [Directory Structure](#directory-structure)
4. [Fixtures & Factories](#fixtures--factories)
5. [Running Tests](#running-tests)
6. [Writing Tests](#writing-tests)
7. [Quality Standards](#quality-standards)
8. [CI/CD Integration](#cicd-integration)
9. [Migration Guide](#migration-guide)
10. [Governance](#governance)

---

## Architecture Overview

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Test Runner | pytest | >=8.0.0 |
| Async Support | pytest-asyncio | >=0.24.0 |
| Coverage | pytest-cov | >=5.0.0 |
| Timeout Enforcement | pytest-timeout | >=2.3.0 |
| Container Isolation | testcontainers | >=4.0.0 |
| Test Data Generation | faker | >=24.0.0 |
| HTTP Client | httpx | >=0.27.0 |

### Core Principles

1. **Isolation**: Each test runs in complete isolation via database rollback
2. **Determinism**: No flaky tests - no hard waits, no random data without seeds
3. **Speed**: Unit tests < 5s, Integration tests < 30s, E2E tests < 90s
4. **Self-Contained**: Integration tests use testcontainers, not docker-compose
5. **Explicit Intent**: Factories with overrides make test data intent clear

---

## Test Levels & Markers

### Marker Definitions

| Marker | Scope | Dependencies | Timeout | Use Case |
|--------|-------|--------------|---------|----------|
| `@pytest.mark.unit` | Function/class logic | None | 5s | Pure functions, business logic, utilities |
| `@pytest.mark.integration` | Service boundaries | Testcontainers | 30s | DB operations, API contracts, service interactions |
| `@pytest.mark.e2e` | Full user journeys | Docker Compose | 90s | Critical paths, multi-system flows |
| `@pytest.mark.smoke` | Quick validation | Varies | 10s | Deployment verification, critical path checks |
| `@pytest.mark.slow` | Long-running | Varies | 5min | Load tests, stress tests, performance benchmarks |

### Marker Application Rules

1. **Every test file MUST have a `pytestmark`** at module level:
   ```python
   # In unit tests
   pytestmark = pytest.mark.unit

   # In integration tests
   pytestmark = pytest.mark.integration
   ```

2. **Individual tests can have additional markers**:
   ```python
   @pytest.mark.smoke
   @pytest.mark.integration
   async def test_critical_auth_flow():
       ...
   ```

3. **E2E tests are excluded by default** (via `addopts = "-m 'not e2e'"`)

### Decision Matrix: When to Use Which Level

| Scenario | Unit | Integration | E2E |
|----------|------|-------------|-----|
| Testing a utility function | ✅ | ❌ | ❌ |
| Testing database CRUD | ❌ | ✅ | ❌ |
| Testing API endpoint contract | ❌ | ✅ | ❌ |
| Testing user login flow | ❌ | ✅ | ⚠️ |
| Testing checkout with payment | ❌ | ❌ | ✅ |
| Testing email notifications | ❌ | ❌ | ✅ |

---

## Directory Structure

```
backend/tests/
├── conftest.py              # Shared fixtures (client, env setup)
├── README.md                # Quick reference documentation
│
├── factories/               # Data factories
│   ├── __init__.py          # Exports all factories
│   ├── user_factory.py      # User data generation
│   └── document_factory.py  # Document data generation (future)
│
├── fixtures/                # Composable test fixtures
│   ├── __init__.py          # Exports all fixtures
│   └── auth_fixtures.py     # Authentication helpers
│
├── unit/                    # Unit tests (no external deps)
│   ├── __init__.py
│   ├── conftest.py          # Unit-specific config (applies marker)
│   ├── test_*.py            # Test modules
│   └── services/            # Subdirectories for organization
│       └── test_audit.py
│
├── integration/             # Integration tests (testcontainers)
│   ├── __init__.py
│   ├── conftest.py          # Testcontainers fixtures
│   ├── test_*.py            # Test modules
│   └── api/                 # Subdirectories for organization
│       └── test_auth.py
│
└── e2e/                     # End-to-end tests (future)
    ├── __init__.py
    ├── conftest.py          # E2E-specific config
    └── test_*.py
```

### Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Test files | `test_<module>.py` | `test_auth.py` |
| Test functions | `test_<action>_<expected>` | `test_login_returns_jwt_cookie` |
| Test classes | `Test<Component>` | `TestUserService` |
| Factories | `<entity>_factory.py` | `user_factory.py` |
| Factory functions | `create_<entity>` | `create_user()` |

---

## Fixtures & Factories

### Root Fixtures (tests/conftest.py)

```python
"""Shared fixtures available to all test types."""

@pytest.fixture
async def client() -> AsyncClient:
    """HTTP client for API testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

### Integration Fixtures (tests/integration/conftest.py)

```python
"""Testcontainers-based fixtures for integration tests."""

@pytest.fixture(scope="session")
def postgres_container():
    """Session-scoped PostgreSQL container."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Async-compatible connection URL."""
    url = postgres_container.get_connection_url()
    return url.replace("postgresql://", "postgresql+asyncpg://")

@pytest.fixture
async def test_engine(postgres_url):
    """Function-scoped engine (container is reused)."""
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Session with automatic rollback for test isolation."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

### Factory Pattern

```python
"""factories/user_factory.py - Data factory with overrides."""

from faker import Faker
import uuid

fake = Faker()

def create_user(**overrides) -> dict:
    """Generate user data with sensible defaults.

    Usage:
        user = create_user()  # Random user
        admin = create_user(is_superuser=True)  # Admin user
        specific = create_user(email="test@example.com")  # Specific email
    """
    defaults = {
        "id": str(uuid.uuid4()),
        "email": fake.email(),
        "hashed_password": "hashed_test_password_123",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
    }
    defaults.update(overrides)
    return defaults

def create_admin_user(**overrides) -> dict:
    """Convenience factory for admin users."""
    return create_user(is_superuser=True, **overrides)
```

### Adding New Factories

When adding a new entity to the system:

1. Create `tests/factories/<entity>_factory.py`
2. Export from `tests/factories/__init__.py`
3. Follow the override pattern shown above
4. Use `faker` for dynamic data generation

---

## Running Tests

### Makefile Commands

```bash
# Unit tests (fast, no Docker needed)
make test-unit

# Integration tests (requires Docker for testcontainers)
make test-integration

# All tests except E2E
make test-all

# With coverage report
make test-coverage

# Full test suite including E2E (CI only)
cd backend && pytest -v
```

### Direct pytest Commands

```bash
# Run specific marker
pytest -m unit -v
pytest -m integration -v
pytest -m "smoke and integration" -v

# Run specific file
pytest tests/integration/test_auth.py -v

# Run specific test
pytest tests/unit/test_health.py::test_health_check -v

# Run with coverage
pytest --cov=app --cov-report=html -v

# Run with verbose output
pytest -v --tb=long

# Run excluding slow tests
pytest -m "not slow" -v
```

### Local Development Workflow

1. Write/modify code
2. Run `make test-unit` (instant feedback)
3. Run `make test-integration` (verify DB interactions)
4. Push and let CI run full suite

---

## Writing Tests

### Unit Test Template

```python
"""Unit tests for <module>."""

import pytest
from unittest.mock import AsyncMock, patch

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestMyService:
    """Test suite for MyService."""

    @pytest.fixture
    def mock_dependency(self):
        """Mock external dependency."""
        return AsyncMock()

    async def test_method_returns_expected_result(self, mock_dependency):
        """Test that method returns expected result."""
        # Arrange
        service = MyService(dependency=mock_dependency)
        mock_dependency.fetch.return_value = {"data": "value"}

        # Act
        result = await service.process()

        # Assert
        assert result == {"processed": "value"}
        mock_dependency.fetch.assert_called_once()

    async def test_method_handles_error_gracefully(self, mock_dependency):
        """Test that errors are handled without propagating."""
        # Arrange
        mock_dependency.fetch.side_effect = Exception("Connection failed")
        service = MyService(dependency=mock_dependency)

        # Act & Assert (should not raise)
        result = await service.process()
        assert result is None
```

### Integration Test Template

```python
"""Integration tests for <API/service>."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from tests.factories import create_user

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


async def test_create_entity_persists_to_database(
    db_session: AsyncSession,
    client: AsyncClient,
):
    """Test that POST creates entity in database."""
    # Arrange
    user_data = create_user(email="test@example.com")

    # Act
    response = await client.post("/api/v1/users", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data


async def test_get_entity_returns_correct_data(
    db_session: AsyncSession,
    client: AsyncClient,
):
    """Test that GET returns entity from database."""
    # Arrange - seed data
    user_data = create_user()
    # ... insert into db_session ...

    # Act
    response = await client.get(f"/api/v1/users/{user_data['id']}")

    # Assert
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
```

### Anti-Patterns to Avoid

```python
# ❌ BAD: Hard-coded data causes parallel collisions
async def test_user_creation():
    user = {"email": "test@example.com"}  # Will fail in parallel runs

# ✅ GOOD: Factory generates unique data
async def test_user_creation():
    user = create_user()  # Unique email each time


# ❌ BAD: Hard waits cause flakiness
async def test_async_operation():
    await asyncio.sleep(5)  # Non-deterministic

# ✅ GOOD: Wait for specific condition
async def test_async_operation():
    await wait_for(lambda: condition_met(), timeout=5)


# ❌ BAD: Hidden assertions in helpers
async def test_user_flow():
    await verify_user_created(response)  # Where are the assertions?

# ✅ GOOD: Explicit assertions in test body
async def test_user_flow():
    assert response.status_code == 201
    assert response.json()["email"] == expected_email


# ❌ BAD: Conditional test logic
async def test_maybe_works():
    if some_condition:
        assert result == expected
    else:
        assert result is None  # Different behavior = different test

# ✅ GOOD: One test = one behavior
async def test_works_when_condition_true():
    # Setup condition to be true
    assert result == expected

async def test_returns_none_when_condition_false():
    # Setup condition to be false
    assert result is None
```

---

## Quality Standards

### Definition of Done for Tests

Every test MUST:

- [ ] Have appropriate marker (`unit`, `integration`, `e2e`)
- [ ] Complete within timeout (unit: 5s, integration: 30s, e2e: 90s)
- [ ] Be deterministic (same result every run)
- [ ] Be isolated (no shared state between tests)
- [ ] Have explicit assertions in test body
- [ ] Use factories for test data (no hardcoded emails/IDs)
- [ ] Follow naming conventions

### Code Review Checklist

Before approving a PR with tests:

1. Are all tests marked appropriately?
2. Do integration tests use testcontainers fixtures?
3. Are factories used for test data?
4. Are assertions explicit and visible?
5. Is there any hardcoded data that could cause parallel failures?
6. Are there any hard waits (`sleep`, `waitForTimeout`)?
7. Do tests clean up after themselves?

### Coverage Requirements

| Category | Minimum Coverage |
|----------|-----------------|
| Critical paths (auth, payments) | 90% |
| Business logic | 80% |
| Utilities | 70% |
| Overall | 75% |

---

## CI/CD Integration

### GitHub Actions Pipeline

The CI pipeline (`.github/workflows/test.yml`) runs:

1. **Lint**: ruff check + format verification
2. **Unit Tests**: `pytest -m unit` (no Docker)
3. **Integration Tests**: `pytest -m integration` (testcontainers)
4. **Coverage Report**: Generated on PRs

### Pipeline Behavior

| Event | Unit Tests | Integration Tests | Coverage |
|-------|------------|-------------------|----------|
| Push to main/develop | ✅ | ✅ | ❌ |
| Pull Request | ✅ | ✅ | ✅ |

### Local CI Simulation

```bash
# Run what CI runs
make lint-backend && make test-unit && make test-integration
```

---

## Migration Guide

### Migrating Existing Tests to New Framework

1. **Add marker to test file**:
   ```python
   pytestmark = pytest.mark.integration  # or unit
   ```

2. **Replace hardcoded data with factories**:
   ```python
   # Before
   user = {"email": "test@example.com", "password": "test123"}

   # After
   from tests.factories import create_user
   user = create_user()
   ```

3. **Update fixtures to use testcontainers**:
   - Replace `test_engine` from root conftest with integration conftest
   - Ensure `db_session` fixture is used for database tests

4. **Verify test passes in isolation**:
   ```bash
   pytest tests/integration/test_your_file.py -v
   ```

### Adding Tests for New Features

1. Determine test level (unit vs integration vs e2e)
2. Create test file in appropriate directory
3. Add `pytestmark` with correct marker
4. Create factory if new entity type
5. Write tests following templates above
6. Run and verify locally before pushing

---

## Governance

### Enforcement

1. **Pre-commit hooks**: Verify test files have markers
2. **CI gates**: PRs must pass all tests
3. **Code review**: Reviewers check against this spec

### Exceptions

Exceptions to this framework require:

1. Written justification in PR description
2. Approval from TEA or Tech Lead
3. Documented workaround timeline

### Updates to This Document

1. Propose changes via PR to `docs/test-framework-specification.md`
2. Require review from TEA and at least one developer
3. Update version number and effective date

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                 LumiKB Test Framework                       │
├─────────────────────────────────────────────────────────────┤
│ MARKERS                                                     │
│   @pytest.mark.unit        - No deps, <5s                   │
│   @pytest.mark.integration - Testcontainers, <30s           │
│   @pytest.mark.e2e         - Docker Compose, <90s           │
├─────────────────────────────────────────────────────────────┤
│ COMMANDS                                                    │
│   make test-unit           - Fast feedback                  │
│   make test-integration    - DB/API tests                   │
│   make test-coverage       - With HTML report               │
├─────────────────────────────────────────────────────────────┤
│ FACTORIES                                                   │
│   from tests.factories import create_user                   │
│   user = create_user()                                      │
│   admin = create_user(is_superuser=True)                    │
├─────────────────────────────────────────────────────────────┤
│ FIXTURES                                                    │
│   client        - HTTP test client                          │
│   db_session    - DB session with rollback                  │
│   test_engine   - Async SQLAlchemy engine                   │
├─────────────────────────────────────────────────────────────┤
│ RULES                                                       │
│   ✓ Every file has pytestmark                               │
│   ✓ Use factories, not hardcoded data                       │
│   ✓ Explicit assertions in test body                        │
│   ✓ No hard waits (sleep, waitForTimeout)                   │
│   ✓ One test = one behavior                                 │
└─────────────────────────────────────────────────────────────┘
```

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-23 | TEA (Murat) | Initial framework specification |
