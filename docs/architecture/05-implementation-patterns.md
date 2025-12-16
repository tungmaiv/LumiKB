# Implementation Patterns

← Back to [Architecture Index](index.md) | **Previous**: [04 - GraphRAG Integration](04-graphrag-integration.md)

---

## Novel Pattern Designs

### Pattern 1: Citation Assembly System

The citation system is LumiKB's core differentiator. Every AI-generated statement must trace back to source documents with passage-level precision.

#### Architecture

```
RETRIEVAL PHASE
  Query → Qdrant → Chunks with rich metadata
                        │
                        ▼
  ┌─────────────────────────────────────────┐
  │  Chunk Metadata (stored at index time)  │
  │  - document_id, document_name           │
  │  - page_number, section_header          │
  │  - char_start, char_end, chunk_text     │
  └─────────────────────────────────────────┘

GENERATION PHASE
  System prompt instructs LLM to cite using [1], [2], etc.
  LLM Response: "Authentication uses OAuth 2.0 [1] with MFA [2]..."

CITATION EXTRACTION
  Parse output → Extract [n] markers → Map to source chunks
                        │
                        ▼
  ┌─────────────────────────────────────────┐
  │  Citation Object                        │
  │  {                                      │
  │    "number": 1,                         │
  │    "document_id": "doc-xyz",            │
  │    "document_name": "Acme Proposal.pdf",│
  │    "page": 14,                          │
  │    "section": "Authentication",         │
  │    "excerpt": "OAuth 2.0 with PKCE...", │
  │    "confidence": 0.92                   │
  │  }                                      │
  └─────────────────────────────────────────┘

STREAMING SUPPORT
  SSE Events:
    { "type": "token", "content": "OAuth 2.0 " }
    { "type": "token", "content": "[1]" }
    { "type": "citation", "data": { "number": 1, ... }}
```

#### Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| CitationService | `services/citation_service.py` | Core citation logic |
| ChunkMetadata | Qdrant payload | Rich metadata at index time |
| CitationExtractor | `services/citation_service.py` | Parse [n] from LLM output |
| CitationCard | `components/citations/` | UI display |

### Pattern 2: Transactional Outbox (Cross-Service Consistency)

Document operations touch PostgreSQL, MinIO, and Qdrant. The outbox pattern ensures eventual consistency with failure recovery.

#### Document Status State Machine

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  DOCUMENT LIFECYCLE                  │
                    └─────────────────────────────────────────────────────┘

     ┌──────────┐      upload       ┌──────────┐     worker picks up    ┌────────────┐
     │          │ ─────────────────>│          │ ─────────────────────> │            │
     │  (none)  │                   │ PENDING  │                        │ PROCESSING │
     │          │                   │          │                        │            │
     └──────────┘                   └──────────┘                        └─────┬──────┘
                                                                              │
                                    ┌─────────────────────────────────────────┤
                                    │                                         │
                                    ▼ all steps complete                      ▼ step fails
                              ┌──────────┐                              ┌──────────┐
                              │          │                              │          │
                              │  READY   │                              │  FAILED  │
                              │          │                              │          │
                              └──────────┘                              └────┬─────┘
                                    │                                        │
                                    │ user deletes                           │ retry (manual/auto)
                                    ▼                                        ▼
                              ┌──────────┐                              ┌────────────┐
                              │          │                              │            │
                              │ ARCHIVED │                              │ PROCESSING │
                              │          │                              │  (retry)   │
                              └──────────┘                              └────────────┘

Status Values:
- PENDING:    Document uploaded, waiting for processing
- PROCESSING: Celery worker actively processing (parsing, chunking, embedding)
- READY:      All processing complete, document is searchable
- FAILED:     Processing failed after max retries (check last_error)
- ARCHIVED:   Soft-deleted, retained for audit trail
```

#### Flow

```
1. API REQUEST (synchronous)
   BEGIN TRANSACTION
     INSERT INTO documents (id, name, status='pending')
     INSERT INTO outbox (event_type='doc.created', payload)
   COMMIT
   Return 202 Accepted

2. CELERY WORKER (asynchronous)
   Poll outbox → For each event:
     UPDATE documents SET status='processing'
     Step A: Upload file to MinIO
     Step B: Parse document (unstructured)
     Step C: Chunk document (LangChain)
     Step D: Generate embeddings
     Step E: Store vectors in Qdrant
   All complete: UPDATE documents SET status='ready'
   On failure: UPDATE documents SET status='failed', last_error=...

3. RECONCILIATION JOB (hourly)
   Detect: docs without vectors, orphaned files
   Actions: re-queue, cleanup, alert
```

#### Outbox Schema

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    attempts INT DEFAULT 0,
    last_error TEXT
);
CREATE INDEX idx_outbox_unprocessed ON outbox (created_at)
    WHERE processed_at IS NULL;
```

---

## Design Principles: KISS, DRY, YAGNI

All implementation patterns follow these core principles:

| Principle | Meaning | Application |
|-----------|---------|-------------|
| **KISS** | Keep It Simple, Stupid | Prefer simple solutions over clever ones. If a pattern requires explanation, simplify it. |
| **DRY** | Don't Repeat Yourself | Extract common code AFTER you see it repeated 3+ times, not before. |
| **YAGNI** | You Aren't Gonna Need It | Don't build features or abstractions until there's a concrete need. |

**When to abstract:** Only when you have 3+ concrete examples of repetition. Premature abstraction is worse than duplication.

---

## Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| Database Tables | snake_case, plural | `users`, `knowledge_bases` |
| Database Columns | snake_case | `user_id`, `created_at` |
| API Endpoints | kebab-case, plural | `/api/v1/knowledge-bases` |
| Python Files | snake_case | `auth_service.py` |
| Python Classes | PascalCase | `KnowledgeBase` |
| TypeScript Files | kebab-case | `knowledge-base.tsx` |
| React Components | PascalCase | `CitationCard` |
| Environment Vars | SCREAMING_SNAKE | `DATABASE_URL` |

---

## Date/Time Formatting

All date/time values use consistent formats across the application:

| Context | Format | Example | Library |
|---------|--------|---------|---------|
| API responses | ISO 8601 UTC | `2025-11-23T10:30:00Z` | Native Python `datetime.isoformat()` |
| Database storage | TIMESTAMPTZ | `2025-11-23 10:30:00+00` | PostgreSQL native |
| UI display (full) | Locale-aware | `Nov 23, 2025, 10:30 AM` | `date-fns` with `format()` |
| UI display (relative) | Relative | `2 hours ago` | `date-fns` with `formatDistanceToNow()` |
| File exports | ISO 8601 | `2025-11-23T10:30:00Z` | Native |

```typescript
// frontend/src/lib/utils/date.ts
import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (date: string | Date) =>
  format(new Date(date), 'MMM d, yyyy, h:mm a');

export const formatRelative = (date: string | Date) =>
  formatDistanceToNow(new Date(date), { addSuffix: true });

// Usage in components
<span>{formatDate(document.createdAt)}</span>      // "Nov 23, 2025, 10:30 AM"
<span>{formatRelative(document.updatedAt)}</span>  // "2 hours ago"
```

```python
# backend/app/schemas/base.py
from datetime import datetime, timezone

class TimestampMixin:
    """All timestamps returned as ISO 8601 UTC"""
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat()
        }
```

---

## Code Organization

| Layer | Purpose | Pattern |
|-------|---------|---------|
| `api/` | HTTP routing | Thin controllers, delegate to services |
| `services/` | Business logic | Orchestration, validation, domain rules |
| `repositories/` | Data access | Database queries, external data sources |
| `models/` | Data structures | SQLAlchemy ORM models |
| `schemas/` | API contracts | Pydantic request/response models |
| `workers/` | Async tasks | Celery task definitions |

---

## Error Handling

```python
# Standardized error response
{
    "error": {
        "code": "DOCUMENT_NOT_FOUND",
        "message": "Document with ID xyz not found",
        "details": {"document_id": "xyz"},
        "request_id": "req-abc-123"
    }
}

# HTTP Status Codes
400 - Validation errors
401 - Authentication required
403 - Permission denied
404 - Resource not found
409 - Conflict
422 - Business logic error
500 - Internal server error
503 - Service unavailable
```

---

## Logging Strategy

```python
# Structured JSON logs
{
    "timestamp": "2025-11-22T10:30:00Z",
    "level": "INFO",
    "message": "Document processed",
    "request_id": "req-abc-123",
    "user_id": "user-xyz",
    "document_id": "doc-789",
    "duration_ms": 1250
}
```

---

## Common Patterns (KISS/DRY/YAGNI)

### 1. Centralized Exception Handling (DRY)

All errors flow through a single exception handler. Services raise exceptions, middleware formats responses.

```python
# backend/app/core/exceptions.py
class AppException(Exception):
    """Base exception - all custom exceptions inherit from this"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with ID {resource_id} not found",
            status_code=404,
            details={"resource": resource, "id": resource_id}
        )

class PermissionDeniedError(AppException):
    def __init__(self, action: str, resource: str):
        super().__init__(
            code="PERMISSION_DENIED",
            message=f"You don't have permission to {action} this {resource}",
            status_code=403
        )

# backend/app/main.py - Single handler for ALL app errors
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request.state.request_id
            }
        }
    )

# In services - just raise, never handle (KISS)
class KBService:
    async def get(self, kb_id: str) -> KnowledgeBase:
        kb = await self.repo.get(kb_id)
        if not kb:
            raise NotFoundError("knowledge_base", kb_id)
        return kb
```

### 2. Request-Scoped Logging Context (DRY)

Set logging context once in middleware, available everywhere automatically.

```python
# backend/app/core/logging.py
import structlog
from contextvars import ContextVar

request_context: ContextVar[dict] = ContextVar("request_context", default={})

def get_logger():
    """Get logger with current request context automatically included"""
    return structlog.get_logger().bind(**request_context.get())

# backend/app/middleware/logging.py
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request_context.set({
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    })

    logger = get_logger()
    start = time.time()
    logger.info("request_started")

    response = await call_next(request)

    logger.info("request_completed",
                status_code=response.status_code,
                duration_ms=int((time.time() - start) * 1000))
    return response

# In services - context is automatic (KISS)
class DocumentService:
    async def process(self, doc_id: str):
        logger = get_logger()  # Already has request_id, user_id
        logger.info("processing_document", document_id=doc_id)
```

### 3. Pydantic-Only Validation (DRY)

Validation happens ONCE in Pydantic schemas. Services trust validated input.

```python
# backend/app/schemas/document.py
class DocumentCreate(BaseModel):
    """Validation defined HERE, once"""
    name: str = Field(..., min_length=1, max_length=255)
    kb_id: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Document name cannot be empty")
        return v.strip()

# In API route - Pydantic validates automatically
@router.post("/")
async def upload_document(data: DocumentCreate):  # Validated!
    return await service.create(data)

# In service - NO re-validation (YAGNI)
class DocumentService:
    async def create(self, data: DocumentCreate):
        # data is ALREADY validated, just use it
        doc = Document(name=data.name, kb_id=data.kb_id)
```

### 4. Generic Repository Base (DRY)

Standard CRUD operations in base class. Only override for unique queries.

```python
# backend/app/repositories/base.py
class BaseRepository(Generic[ModelType]):
    """Generic CRUD - add specific methods only when needed (YAGNI)"""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: str) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def list(self, skip: int = 0, limit: int = 20) -> list[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

# Specific repository - ONLY unique methods
class DocumentRepository(BaseRepository[Document]):
    async def get_by_kb(self, kb_id: str) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        return result.scalars().all()
```

### 5. Dependency Injection (KISS)

FastAPI's `Depends()` with simple factory functions.

```python
# backend/app/api/deps.py
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

def get_repository(repo_class):
    async def _get_repo(session: AsyncSession = Depends(get_db)):
        return repo_class(session)
    return _get_repo

def get_service(service_class, repo_class):
    async def _get_service(repo = Depends(get_repository(repo_class))):
        return service_class(repo)
    return _get_service

# Usage - one-liner (KISS)
@router.get("/{kb_id}")
async def get_kb(
    kb_id: str,
    service: KBService = Depends(get_service(KBService, KBRepository))
):
    return await service.get(kb_id)
```

### Pattern Summary

| Pattern | Principle | Rule |
|---------|-----------|------|
| Exception Handling | DRY | Define exceptions once, handler formats all errors |
| Logging | DRY | Set context in middleware, `get_logger()` everywhere |
| Validation | DRY + YAGNI | Pydantic validates, services trust input |
| Repository | DRY + YAGNI | Generic base, add methods only when needed |
| Dependency Injection | KISS | Simple factory functions, one-liner usage |

---

## Testing Conventions

### Test File Organization

| Stack | Test Location | Naming Pattern | Example |
|-------|---------------|----------------|---------|
| Backend unit | `backend/tests/unit/` | `test_{module}.py` | `test_citation_service.py` |
| Backend integration | `backend/tests/integration/` | `test_{feature}_integration.py` | `test_document_upload_integration.py` |
| Frontend unit | `frontend/__tests__/` | `{component}.test.tsx` | `CitationCard.test.tsx` |
| Frontend E2E | `frontend/e2e/` | `{feature}.spec.ts` | `document-upload.spec.ts` |

### Backend Testing (pytest)

```python
# backend/tests/conftest.py - Shared fixtures
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.core.config import settings

@pytest.fixture
async def db_session():
    """Fresh database session for each test"""
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Test client with database override"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_qdrant(mocker):
    """Mock Qdrant client for unit tests"""
    return mocker.patch("app.integrations.qdrant_client.QdrantClient")

# backend/tests/unit/test_citation_service.py - Unit test example
import pytest
from app.services.citation_service import CitationService

class TestCitationService:
    async def test_extract_citations_from_text(self):
        """Test citation marker extraction"""
        service = CitationService()
        text = "OAuth 2.0 [1] with MFA [2] is required."

        citations = service.extract_markers(text)

        assert len(citations) == 2
        assert citations[0].number == 1
        assert citations[1].number == 2

    async def test_no_citations_returns_empty(self):
        """Test handling of text without citations"""
        service = CitationService()
        result = service.extract_markers("No citations here")
        assert result == []
```

### Frontend Testing (Jest + React Testing Library)

```typescript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testMatch: ['**/__tests__/**/*.test.{ts,tsx}'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};

// frontend/jest.setup.ts
import '@testing-library/jest-dom';

// frontend/__tests__/components/CitationCard.test.tsx
import { render, screen } from '@testing-library/react';
import { CitationCard } from '@/components/citations/CitationCard';

describe('CitationCard', () => {
  const mockCitation = {
    number: 1,
    documentName: 'Security Policy.pdf',
    page: 14,
    excerpt: 'OAuth 2.0 with PKCE flow...',
  };

  it('renders citation number and document name', () => {
    render(<CitationCard citation={mockCitation} />);

    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('Security Policy.pdf')).toBeInTheDocument();
  });

  it('shows page number when provided', () => {
    render(<CitationCard citation={mockCitation} />);

    expect(screen.getByText('Page 14')).toBeInTheDocument();
  });
});
```

### Mocking Strategy

| What to Mock | When | How |
|--------------|------|-----|
| External APIs (LiteLLM, Qdrant) | Unit tests | `pytest-mock` / `jest.mock()` |
| Database | Unit tests only | In-memory SQLite or mocks |
| Database | Integration tests | Test PostgreSQL instance |
| File system (MinIO) | Unit tests | Mock boto3/minio client |
| Time/dates | When testing time-sensitive logic | `freezegun` / `jest.useFakeTimers()` |

### Test Commands

```bash
# Backend
cd backend
pytest                           # Run all tests
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests only
pytest -k "citation"            # Tests matching pattern
pytest --cov=app --cov-report=html  # With coverage

# Frontend
cd frontend
npm test                        # Run all tests
npm test -- --watch            # Watch mode
npm test -- --coverage         # With coverage
npm run test:e2e               # E2E tests (Playwright)
```

---

**Previous**: [04 - GraphRAG Integration](04-graphrag-integration.md) | **Next**: [06 - Data & API](06-data-and-api.md) | **Index**: [Architecture](index.md)
