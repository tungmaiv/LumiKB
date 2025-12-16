# Testing Guideline

Quick reference for running tests in LumiKB with all configuration details.

---

## Quick Reference: Credentials & Endpoints

### Test User Accounts

| Account | Email | Password | Role | Notes |
|---------|-------|----------|------|-------|
| **Admin** | `admin@lumikb.example` | `BilHam30` | Superuser | Full admin access |
| **Demo** | `demo@lumikb.example` | `demo123` | Regular user | Has demo KB access |
| **Test Users** | `test.user.N@lumikb.example` | `testuser123` | Regular user | Created by seed-test-users.py |

### API Endpoints

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **Backend API** | `http://localhost:8000` | FastAPI backend |
| **Health Check** | `http://localhost:8000/health` | Service health status |
| **API Docs** | `http://localhost:8000/docs` | Swagger UI |
| **Frontend** | `http://localhost:3000` | Next.js frontend |

### Authentication Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login` | POST | Login (returns session cookie) |
| `/api/v1/auth/logout` | POST | Logout |
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/users/me` | GET | Get current user info |

**Login Request Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@lumikb.example&password=BilHam30" \
  -c cookies.txt
```

### Infrastructure Services

| Service | Host | Port | Credentials | Health Check |
|---------|------|------|-------------|--------------|
| **PostgreSQL** | localhost | 5432 | `lumikb` / `lumikb_dev_password` | `pg_isready -U lumikb -d lumikb` |
| **Redis** | localhost | 6379 | None | `redis-cli ping` |
| **MinIO** | localhost | 9000 (API), 9001 (Console) | `lumikb` / `lumikb_dev_password` | `curl http://localhost:9000/minio/health/live` |
| **Qdrant** | localhost | 6333 (REST), 6334 (gRPC) | None | `curl http://localhost:6333/readyz` |
| **LiteLLM** | localhost | 4000 | API Key: `sk-dev-master-key` | `curl http://localhost:4000/health/readiness` |

### Database Connection Strings

```bash
# PostgreSQL (async)
postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb

# PostgreSQL (sync - for psql CLI)
postgresql://lumikb:lumikb_dev_password@localhost:5432/lumikb

# Redis
redis://localhost:6379/0
```

### Direct Database Access

```bash
# Connect to PostgreSQL
PGPASSWORD=lumikb_dev_password psql -h localhost -U lumikb -d lumikb

# Useful queries
\dt                           # List tables
SELECT * FROM users;          # List users
SELECT * FROM knowledge_bases; # List KBs
SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT 10;
```

---

## Test Environment Setup

### Prerequisites

1. **Docker Desktop** - Required for integration tests and infrastructure
2. **Python 3.11+** with backend virtual environment
3. **Node.js 18+** with frontend dependencies
4. **Ollama** (optional) - For local LLM testing

### Starting Infrastructure

```bash
# Start all infrastructure services
make dev

# Verify services are running
docker ps

# Expected containers:
# - lumikb-postgres
# - lumikb-redis
# - lumikb-minio
# - lumikb-qdrant
# - lumikb-litellm
# - lumikb-celery-worker
# - lumikb-celery-beat
```

### Database Setup

```bash
# Run migrations (from project root)
cd backend && source .venv/bin/activate && alembic upgrade head

# Seed demo data (creates admin user, demo user, sample KB)
make seed
```

---

## Test Commands

### Backend Tests (pytest)

```bash
# From project root
make test-unit          # Unit tests only (fast, no Docker)
make test-integration   # Integration tests (uses testcontainers)
make test-all           # All backend tests
make test-coverage      # Tests with coverage report

# Run specific test file
cd backend && source .venv/bin/activate
pytest tests/unit/test_search_service.py -v
pytest tests/integration/test_chat_api.py -v

# Run tests matching pattern
pytest -k "test_login" -v

# Run with verbose output
pytest -v --tb=short
```

### Frontend Tests (Vitest + Testing Library)

```bash
make test-frontend           # Run frontend unit tests
make test-frontend-watch     # Watch mode
make test-frontend-coverage  # With coverage report

# Run specific test file
cd frontend && npm run test:run -- src/hooks/__tests__/useAdminStats.test.tsx
```

### E2E Tests (Playwright)

```bash
make test-e2e         # Run E2E tests (headless)
make test-e2e-ui      # Interactive UI mode
make test-e2e-headed  # See browser while testing

# Run specific test file
cd frontend && npx playwright test e2e/tests/admin/dashboard.spec.ts

# Run with debug mode
cd frontend && npx playwright test --debug
```

---

## Test Types and Docker Requirements

| Test Type | Docker Required | Auto-Starts Containers | Notes |
|-----------|-----------------|------------------------|-------|
| Backend Unit | NO | NO | Fast, mocked dependencies |
| Backend Integration | YES | YES (testcontainers) | Auto-provisions Postgres, Redis, Qdrant |
| Frontend Unit | NO | NO | Uses jsdom, mocked API |
| E2E | YES | NO | Requires full stack running |

### Integration Tests with Testcontainers

Integration tests automatically provision isolated Docker containers:

```python
# Tests use these fixtures from conftest.py:
@pytest.fixture(scope="session")
def postgres_container():
    # Auto-starts PostgreSQL 16 container

@pytest.fixture(scope="session")
def redis_container():
    # Auto-starts Redis 7 container

@pytest.fixture(scope="session")
def qdrant_container():
    # Auto-starts Qdrant v1.15 container
```

**Important:** Integration tests need Docker daemon running but do NOT need `make dev`.

---

## Running E2E Tests Locally

E2E tests require the full stack to be running:

```bash
# Terminal 1: Start infrastructure
make dev

# Terminal 2: Start backend
make dev-backend

# Terminal 3: Start frontend
make dev-frontend

# Terminal 4: Run E2E tests
make test-e2e         # Headless
make test-e2e-headed  # See browser
make test-e2e-ui      # Interactive UI
```

### E2E Test Authentication

E2E tests use the auth fixture for pre-authenticated state:
- Uses admin account by default
- Auth state saved in `frontend/.auth/` directory

---

## Viewing Logs

### Docker Container Logs

```bash
# View all container logs
make logs

# View ERROR logs from all containers
make logs-errors

# View WARNING logs from all containers
make logs-warnings

# Follow logs in real-time
make logs-follow

# View Celery logs (worker + beat)
make logs-celery

# View specific service logs
make logs-backend SERVICE=postgres
make logs-backend SERVICE=celery-worker
make logs-backend SERVICE=litellm
```

### Direct Docker Logs

```bash
# View specific container
docker logs lumikb-postgres --tail 100
docker logs lumikb-celery-worker --tail 100 -f

# View all containers
docker compose -f infrastructure/docker/docker-compose.yml logs

# Filter logs
docker logs lumikb-celery-worker 2>&1 | grep -i error
```

### Backend Application Logs

When running `make dev-backend`, logs appear in the terminal with structlog formatting:
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Failures requiring attention

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `Connection refused` on port 8000 | Start backend: `make dev-backend` |
| `Connection refused` on port 3000 | Start frontend: `make dev-frontend` |
| `Connection refused` on port 5432 | Start infrastructure: `make dev` |
| Tests fail with `database does not exist` | Run migrations: `cd backend && alembic upgrade head` |
| No test users exist | Run seed: `make seed` |
| Integration tests timeout | Ensure Docker daemon is running |
| Qdrant "Too many open files" | Restart Qdrant: `docker restart lumikb-qdrant` |

### Checking Service Health

```bash
# Quick health check script
echo "=== PostgreSQL ===" && PGPASSWORD=lumikb_dev_password psql -h localhost -U lumikb -d lumikb -c "SELECT 1" 2>/dev/null && echo "OK" || echo "FAILED"
echo ""
echo "=== Redis ===" && redis-cli ping
echo ""
echo "=== Qdrant ===" && curl -s http://localhost:6333/readyz
echo ""
echo "=== LiteLLM ===" && curl -s http://localhost:4000/health/readiness | head -1
echo ""
echo "=== Backend ===" && curl -s http://localhost:8000/health | head -1
```

### Resetting Test Environment

```bash
# Stop and remove all containers + volumes
docker compose -f infrastructure/docker/docker-compose.yml down -v

# Restart fresh
make dev

# Recreate database
cd backend && alembic upgrade head

# Reseed data
make seed
```

---

## CI/CD Behavior

| Test Type | Trigger | Notes |
|-----------|---------|-------|
| Backend Unit | Push/PR | Fast, no Docker needed |
| Backend Integration | Push/PR | Uses testcontainers |
| Frontend Unit | Push/PR | Vitest with jsdom |
| E2E | Manual only | Requires `workflow_dispatch` |

### Running E2E in CI

E2E tests are currently **manual-only** in GitHub Actions. To run:

1. Go to Actions tab in GitHub
2. Select "E2E Tests" workflow
3. Click "Run workflow"
4. Choose environment (local/staging)

This will be automated when full Docker Compose CI setup is complete.

---

## Test Specifications

For detailed patterns, fixtures, and best practices:

| Document | Purpose |
|----------|---------|
| [testing-backend-specification.md](testing-backend-specification.md) | pytest markers, fixtures, factories |
| [testing-frontend-specification.md](testing-frontend-specification.md) | Vitest, Testing Library patterns |
| [testing-e2e-specification.md](testing-e2e-specification.md) | Playwright, Page Objects, CI setup |

---

## Quick Tips

### Backend

- Use `@pytest.mark.unit` for tests without external dependencies
- Use `@pytest.mark.integration` for tests requiring database
- Integration tests use testcontainers - no manual Docker setup needed
- Use factories from `tests/factories/` for test data

### Frontend

- Co-locate tests in `__tests__/` directories next to components
- Use `screen.getByRole()` and `screen.getByLabelText()` for accessible queries
- Use `userEvent` instead of `fireEvent` for realistic interactions
- Mock API calls with MSW or vi.mock()

### E2E

- Use Page Object Model pattern (see `frontend/e2e/pages/`)
- Tests use auth fixture for pre-authenticated state
- Artifacts (screenshots, videos) saved on failure
- Use `test.describe()` to group related tests

---

## Backend Unit Test Patterns: Dependency Injection Mocking

This section documents the recommended patterns for mocking dependencies in backend unit tests. Following these patterns ensures tests are isolated, maintainable, and aligned with the codebase architecture.

### Core Pattern: Service Initialization with Mock Session

Services use SQLAlchemy AsyncSession for database operations. The standard pattern:

```python
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_session():
    """Create mock AsyncSession with query chain."""
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session

@pytest.fixture
def sample_model():
    """Create a sample model instance for testing."""
    return MyModel(id=uuid4(), name="Test")

class TestMyService:
    @pytest.mark.asyncio
    async def test_get_item_returns_model(self, mock_session, sample_model):
        # Arrange: Configure mock to return sample_model
        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_model
        mock_session.execute = AsyncMock(return_value=result)

        service = MyService(session=mock_session)

        # Act
        item = await service.get_item(sample_model.id)

        # Assert
        assert item == sample_model
        mock_session.execute.assert_called_once()
```

### Mocking Qdrant Client (Vector Database)

The Qdrant client uses `query_points()` for semantic search:

```python
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

# Use valid UUIDs for KB IDs (not strings like 'kb-123')
TEST_KB_ID_1 = str(uuid4())
TEST_KB_ID_2 = str(uuid4())

def test_search_returns_chunks(search_service):
    """Test semantic search with mocked Qdrant."""
    # Arrange: Create mock point with payload
    mock_point = MagicMock()
    mock_point.score = 0.95
    mock_point.payload = {
        "document_id": "doc-123",
        "document_name": "test.pdf",
        "chunk_text": "Sample content",
        "chunk_index": 0,
        "page_number": 1,
    }

    # Configure query_points response
    mock_query_response = MagicMock()
    mock_query_response.points = [mock_point]

    search_service.qdrant_client = MagicMock()
    search_service.qdrant_client.query_points.return_value = mock_query_response

    # Act & Assert
    # ... run search and verify results
```

### Mocking Internal Methods That Hit Database

When a service method internally calls another method that accesses the database (like `_get_kb_names()`), use `patch.object`:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_search_with_kb_names(search_service):
    """Test search with mocked KB name resolution."""
    # Mock the internal method that would hit the database
    with patch.object(
        search_service,
        "_get_kb_names",
        new_callable=AsyncMock
    ) as mock_get_kb_names:
        mock_get_kb_names.return_value = {
            TEST_KB_ID_1: "Test Knowledge Base"
        }

        # Now the test can run without database access
        result = await search_service.search(query="test", kb_id=TEST_KB_ID_1)

        assert result is not None
```

### Mocking LLM Client (LiteLLM)

For tests involving LLM synthesis:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_synthesize_answer(search_service):
    """Test answer synthesis with mocked LLM."""
    with patch.object(
        search_service.llm_client,
        "complete",
        new_callable=AsyncMock
    ) as mock_complete:
        mock_complete.return_value = "Synthesized answer based on context."

        result = await search_service._synthesize_answer(
            query="What is X?",
            chunks=[mock_chunk],
        )

        assert "answer" in result
        mock_complete.assert_called_once()
```

### Capturing Added Models in `session.add()`

When testing creation logic, capture what was added to the session:

```python
@pytest.mark.asyncio
async def test_create_draft_sets_default_status(self, mock_session):
    """Capture model added to session for assertions."""
    added_draft = None

    def capture_add(draft):
        nonlocal added_draft
        added_draft = draft

    mock_session.add.side_effect = capture_add

    service = DraftService(session=mock_session)
    await service.create_draft(kb_id=uuid4(), user_id=uuid4(), title="Test")

    assert added_draft is not None
    assert added_draft.status == DraftStatus.STREAMING
    mock_session.commit.assert_called_once()
```

### Point ID Generation (UUID5 Deterministic)

Point IDs for vector storage are generated as deterministic UUID5 from document_id + chunk_index:

```python
from uuid import UUID

def test_point_id_is_valid_uuid(self, sample_embeddings):
    """Verify point IDs are valid UUIDs (not strings like 'doc-123_0')."""
    from app.workers.indexing import _create_points

    points = _create_points(sample_embeddings)

    # Point IDs should be valid UUIDs
    UUID(points[0].id)  # Raises ValueError if not valid UUID
    UUID(points[1].id)

    # Different chunks have different IDs
    assert points[0].id != points[1].id
```

### Mocking KBConfigResolver (KB-Level Configuration)

Services like SearchService and ConversationService use `KBConfigResolver` for three-layer configuration precedence. Mock both the resolver and its config methods:

```python
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.kb_config_resolver import KBConfigResolver
from app.schemas.kb_settings import RetrievalConfig, GenerationConfig

@pytest.fixture
def mock_kb_config_resolver():
    """Create mock KBConfigResolver with default configs."""
    resolver = AsyncMock(spec=KBConfigResolver)

    # Return default configs (Pydantic schema defaults)
    resolver.resolve_retrieval_config = AsyncMock(
        return_value=RetrievalConfig()
    )
    resolver.resolve_generation_config = AsyncMock(
        return_value=GenerationConfig()
    )
    resolver.get_kb_system_prompt = AsyncMock(
        return_value="You are a helpful assistant."
    )
    resolver.get_kb_embedding_model = AsyncMock(return_value=None)
    return resolver


@pytest.mark.asyncio
async def test_search_uses_kb_retrieval_config(
    mock_session, mock_redis, mock_kb_config_resolver
):
    """Test SearchService uses KB-level retrieval config."""
    # Arrange: Custom KB config with lower threshold
    custom_config = RetrievalConfig(
        top_k=5,
        similarity_threshold=0.8,
    )
    mock_kb_config_resolver.resolve_retrieval_config = AsyncMock(
        return_value=custom_config
    )

    service = SearchService(
        session=mock_session,
        redis_client=mock_redis,
    )

    # Act
    with patch.object(
        service, "_resolve_retrieval_config",
        new_callable=AsyncMock
    ) as mock_resolve:
        mock_resolve.return_value = custom_config
        result = await service.search(kb_id=TEST_KB_ID, query="test")

    # Assert: Verify KB config was used
    mock_resolve.assert_called_once_with(TEST_KB_ID)


@pytest.mark.asyncio
async def test_conversation_uses_kb_generation_config(
    mock_session, mock_redis, mock_kb_config_resolver
):
    """Test ConversationService uses KB-level generation config."""
    custom_config = GenerationConfig(
        temperature=0.5,
        max_tokens=4096,
    )

    with patch(
        "app.services.conversation_service.KBConfigResolver"
    ) as MockResolver:
        MockResolver.return_value = mock_kb_config_resolver
        mock_kb_config_resolver.resolve_generation_config = AsyncMock(
            return_value=custom_config
        )

        service = ConversationService(
            search_service=mock_search_service,
            session=mock_session,
            redis_client=mock_redis,
        )

        # Assert service initialized with resolver
        assert service._session is not None
        assert service._redis_client is not None
```

**Key Points for KB Config Testing:**

1. **Mock Redis client**: KBConfigResolver requires Redis for caching
2. **Use Pydantic defaults**: `RetrievalConfig()` and `GenerationConfig()` provide valid defaults
3. **Test three-layer precedence**: Request → KB Settings → System Defaults
4. **Mock internal resolver methods**: Use `patch.object()` on service's `_resolve_*_config` methods

### Key Guidelines

1. **Use Valid UUIDs**: Always use `str(uuid4())` for IDs, never strings like `'kb-123'`
2. **Mock at Boundaries**: Mock external services (Qdrant, LiteLLM, Redis) not business logic
3. **Capture Side Effects**: Use `side_effect` to capture `session.add()` calls
4. **Patch Internal Methods**: Use `patch.object()` for methods that hit real services
5. **Verify Interactions**: Assert that mocks were called with expected parameters
6. **Isolate Tests**: Each test should be independent, not relying on shared state
7. **Mock KBConfigResolver**: Services require session + redis for KB config resolution

---

## Environment Variables Reference

### Backend (.env or environment)

```bash
# All prefixed with LUMIKB_
LUMIKB_DATABASE_URL=postgresql+asyncpg://lumikb:lumikb_dev_password@localhost:5432/lumikb
LUMIKB_REDIS_URL=redis://localhost:6379/0
LUMIKB_MINIO_ENDPOINT=localhost:9000
LUMIKB_MINIO_ACCESS_KEY=lumikb
LUMIKB_MINIO_SECRET_KEY=lumikb_dev_password
LUMIKB_QDRANT_HOST=localhost
LUMIKB_QDRANT_PORT=6333
LUMIKB_LITELLM_URL=http://localhost:4000
LUMIKB_LITELLM_API_KEY=sk-dev-master-key
LUMIKB_SECRET_KEY=change-me-in-production
```

### Seed Script Variables

```bash
DEMO_USER_PASSWORD=demo123      # Password for demo user
ADMIN_USER_PASSWORD=BilHam30    # Password for admin user
```
