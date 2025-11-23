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
# Unit tests only (fast feedback, no Docker needed)
make test-unit

# Integration tests (uses testcontainers - Docker required)
make test-integration

# All tests except E2E
make test-all

# With coverage report
make test-coverage

# Specific marker
cd backend && pytest -m "smoke" -v

# Run specific test file
cd backend && pytest tests/integration/test_auth.py -v
```

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures (client, env setup)
├── README.md                # This file
├── factories/               # Data factories (create_user, etc.)
│   ├── __init__.py
│   └── user_factory.py
├── fixtures/                # Composable fixtures (auth, api)
│   ├── __init__.py
│   └── auth_fixtures.py
├── unit/                    # Unit tests (no external deps)
│   ├── conftest.py          # Auto-applies @pytest.mark.unit
│   ├── test_health.py
│   └── test_audit_service.py
└── integration/             # Integration tests (testcontainers)
    ├── conftest.py          # Testcontainers fixtures
    ├── test_auth.py
    ├── test_users.py
    └── test_testcontainers_setup.py
```

## Writing Tests

### Unit Test Example

Unit tests should NOT use database or external services. They test pure logic.

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

Integration tests use testcontainers for isolated database access.

```python
import pytest
from tests.factories import create_user

@pytest.mark.integration
async def test_create_user_persists_to_database(db_session, client):
    user_data = create_user(email="test@example.com")
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
```

## Using Factories

Factories generate unique, parallel-safe test data:

```python
from tests.factories import create_user, create_admin_user

# Default user with random email
user = create_user()

# Override specific fields
admin = create_user(is_superuser=True)
specific_user = create_user(email="specific@example.com")

# Convenience factory
admin = create_admin_user()
```

## Test Quality Guidelines

1. **Deterministic**: No random failures, no hard waits
2. **Isolated**: Each test cleans up after itself (via rollback)
3. **Fast**: Unit tests < 5s, Integration tests < 30s
4. **Explicit**: Assertions visible in test body, not hidden in helpers
5. **Focused**: One test = one behavior

## Testcontainers

Integration tests use testcontainers for:
- **PostgreSQL**: Session-scoped container, function-scoped sessions with rollback
- **Redis**: Session-scoped container for cache/session tests

No need to run `docker compose up` - testcontainers handles everything.
