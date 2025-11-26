# Epic Technical Specification: Knowledge Base & Document Management

Date: 2025-11-23
Author: Tung Vu
Epic ID: 2
Status: Complete

---

## Overview

Epic 2 delivers the Knowledge Base & Document Management capabilities that form the foundation of LumiKB's MATCH functionality. This epic enables users to create, organize, and manage Knowledge Bases while providing a complete document ingestion pipeline that processes documents into searchable, semantically-indexed content.

The epic addresses a core enterprise challenge: getting organizational knowledge INTO the system in a structured, searchable format. Without this capability, the semantic search and document generation features (Epics 3-4) cannot function. This is the "knowledge that never walks out the door" foundation.

**Key Capabilities Delivered:**
- Knowledge Base CRUD with Qdrant collection management
- Role-based KB permissions (READ, WRITE, ADMIN)
- Document upload with support for PDF, DOCX, and Markdown formats
- Async document processing pipeline (parsing → chunking → embedding → indexing)
- Real-time processing status and notifications
- Document lifecycle management including re-upload and deletion
- Cross-service consistency via transactional outbox pattern

## Objectives and Scope

### In-Scope (MVP 1)

**Knowledge Base Management:**
- Create, read, update, and archive Knowledge Bases
- KB-level permission assignment (READ, WRITE, ADMIN)
- Qdrant collection-per-KB isolation model (zero-trust security for enterprise compliance)
- KB statistics (document count, storage usage)

**Document Ingestion:**
- Upload documents via API (PDF, DOCX, MD formats)
- Maximum file size: 50MB (guidance provided for larger documents)
- MinIO object storage for file persistence
- Document metadata tracking
- File checksum validation on upload and retrieval

**Document Processing:**
- Text extraction using unstructured library
- Semantic chunking with LangChain (500 tokens, 50 token overlap)
- Embedding generation via LiteLLM
- Vector storage in Qdrant with rich metadata (critical for Epic 3 citations)
- Status tracking: PENDING → PROCESSING → READY/FAILED
- Processing timeout (10 min max) with automatic retry (max 3 attempts)
- Dead letter queue for permanently failed documents
- Estimated processing time display based on file size

**Document Lifecycle:**
- Document deletion with complete cleanup (storage + vectors)
- Soft-delete with 24-hour recovery window before hard cleanup
- Document re-upload with atomic replacement

**Frontend:**
- KB list and selection UI in sidebar
- Document upload via drag-and-drop
- Processing status indicators (polling every 5 seconds)
- Document list with metadata view

**Data Consistency:**
- Transactional outbox pattern for cross-service operations
- Background reconciliation job (hourly)
- Orphan detection and cleanup

**Monitoring:**
- Processing queue depth monitoring
- Worker health checks
- Orphan detection alerts

### Out-of-Scope (Deferred)

- OCR for scanned documents (MVP 2)
- Document sync from OneDrive/SharePoint/Google Drive (MVP 2)
- Hybrid retrieval (Vector + BM25) (MVP 2)
- Quality scoring for documents (MVP 2)
- Template engine for custom prompts (MVP 3)
- Full-text search within documents (MVP 2)
- Chunked/resumable uploads for files >10MB (MVP 2) - MVP 1 uses simple upload
- WebSocket for real-time status (MVP 2) - MVP 1 uses polling every 5 seconds
- Chunk preview/validation UI (MVP 2) - Users verify via search in Epic 3
- Files >50MB (MVP 2) - Users advised to split large documents

## System Architecture Alignment

This epic implements components defined in the [architecture.md](../architecture.md):

### Backend Services

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **API** | `api/knowledge_bases.py` | KB CRUD endpoints, request validation |
| **API** | `api/documents.py` | Document upload endpoint, multipart handling |
| **Service** | `services/kb_service.py` | KB business logic, permission checks |
| **Service** | `services/document_service.py` | Document orchestration, transaction boundaries |
| **Worker** | `workers/document_tasks.py` | Async processing: parse → chunk → embed → index |

### Data Stores

| Store | Purpose | Key Design |
|-------|---------|------------|
| **PostgreSQL** | `knowledge_bases`, `kb_permissions`, `documents`, `outbox` tables | Source of truth, transactional consistency |
| **Qdrant** | One collection per KB (`kb_{uuid}`) | Vector storage, 1536 dimensions (OpenAI ada-002) |
| **MinIO** | Document files at `kb-{uuid}/{doc-uuid}/{filename}` | Durable object storage with checksums |
| **Redis** | Celery task queue | AOF persistence for task durability |

### Processing Pipeline Flow

```
Upload Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ API Layer: Validate → Store in MinIO → Record in PostgreSQL │
│            (all in single transaction with outbox event)    │
└─────────────────────────────────────────────────────────────┘
     │
     ▼ (async via Celery)
┌─────────────────────────────────────────────────────────────┐
│ Worker: Parse (unstructured) → Chunk (LangChain 500/50)     │
│         → Embed (LiteLLM) → Index (Qdrant)                  │
│         → Update status READY/FAILED                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| **ADR-002** | Collection-per-KB for Qdrant | Zero-trust isolation for enterprise compliance |
| **ADR-003** | Transactional Outbox pattern | Cross-service consistency without distributed transactions |
| **ADR-005** | Citation-First chunk metadata | Rich metadata enables Epic 3/4 citation features |

### External Service Configuration

| Service | Configuration | Health Check |
|---------|---------------|--------------|
| **Qdrant** | Collection with 1536 dimensions, cosine similarity | Connection test on worker startup |
| **MinIO** | Bucket per environment, versioning disabled | Bucket existence check on startup |
| **LiteLLM** | OpenAI ada-002 via proxy, 3 retry with exponential backoff | Embedding test on worker startup |
| **Redis** | AOF persistence enabled, maxmemory-policy noeviction | Connection test on API/worker startup |

### Failure Handling Strategy

| Failure Point | Detection | Recovery |
|---------------|-----------|----------|
| MinIO write fails | Exception during upload | Return 500, no DB record created |
| PostgreSQL transaction fails | Exception during commit | MinIO file orphaned → reconciliation job cleans |
| Worker crashes mid-task | Celery visibility timeout (10 min) | Task requeued, idempotent retry |
| LiteLLM rate limited | 429 response | Exponential backoff, max 5 retries |
| Qdrant upsert fails | Exception from client | Retry 3x, then mark document FAILED |

### Scaling Strategy

| Component | Scaling Approach |
|-----------|------------------|
| **API** | Horizontal via k8s replicas |
| **Celery Workers** | Horizontal, add workers for throughput |
| **Qdrant** | Vertical initially, sharding in MVP 2 |
| **MinIO** | S3-compatible, managed service in production |

## Coding & Testing Standards Compliance

All stories in this epic MUST adhere to the following project standards:

### Mandatory Standards References

| Standard | Document | Applies To |
|----------|----------|------------|
| **Coding Standards** | [docs/coding-standards.md](../coding-standards.md) | All code |
| **Backend Testing** | [docs/testing-backend-specification.md](../testing-backend-specification.md) | Python/FastAPI |
| **Frontend Testing** | [docs/testing-frontend-specification.md](../testing-frontend-specification.md) | React/Next.js |
| **E2E Testing** | [docs/testing-e2e-specification.md](../testing-e2e-specification.md) | User journeys |

### Backend Requirements (Per Story)

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| Type hints on all functions | coding-standards.md | `mypy` in CI |
| Async/await for all I/O | coding-standards.md | Code review |
| Pydantic models for request/response | coding-standards.md | API layer |
| Centralized exception pattern | coding-standards.md | `app/core/exceptions.py` |
| structlog for logging | coding-standards.md | `app/core/logging.py` |
| `pytestmark` on all test files | testing-backend-specification.md | CI gate |
| Factories for test data (no hardcoded) | testing-backend-specification.md | Code review |
| Unit tests < 5s, Integration < 30s | testing-backend-specification.md | `pytest-timeout` |
| Testcontainers for DB tests | testing-backend-specification.md | Integration tests |

### Frontend Requirements (Per Story)

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| TypeScript strict mode | coding-standards.md | `tsconfig.json` |
| Components in kebab-case files | coding-standards.md | Lint |
| Zustand for state management | coding-standards.md | Architecture |
| Co-located `__tests__` directories | testing-frontend-specification.md | Structure |
| Vitest + Testing Library | testing-frontend-specification.md | `npm test` |
| `userEvent` over `fireEvent` | testing-frontend-specification.md | Code review |
| Accessible queries (role, label, text) | testing-frontend-specification.md | Code review |
| 70% coverage minimum | testing-frontend-specification.md | CI gate |

### E2E Requirements (Critical Paths Only)

| Journey | Priority | Standard |
|---------|----------|----------|
| KB creation + document upload | P1 | testing-e2e-specification.md |
| Document processing status | P1 | testing-e2e-specification.md |
| Document list with metadata | P2 | testing-e2e-specification.md |

### Story Definition of Done Checklist

Every story in this epic must satisfy:

```
Backend:
- [ ] Type hints on all new functions
- [ ] Pydantic schemas for API contracts
- [ ] Unit tests with @pytest.mark.unit (coverage ≥80%)
- [ ] Integration tests with @pytest.mark.integration (DB operations)
- [ ] Factories used for test data (tests/factories/)
- [ ] No hardcoded test emails/IDs
- [ ] Logging with structlog for key operations
- [ ] Exception handling via centralized pattern

Frontend:
- [ ] TypeScript strict compliance
- [ ] Component tests in __tests__/ directory
- [ ] Uses Testing Library accessible queries
- [ ] No fireEvent (use userEvent)
- [ ] Coverage ≥70%

E2E (if applicable):
- [ ] Page Object Model used
- [ ] No hard waits (use waitFor)
- [ ] Works in CI (headless)
```

## Detailed Design

### Data Models

#### PostgreSQL Tables

**knowledge_bases**
```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, archived
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_kb_owner ON knowledge_bases(owner_id);
CREATE INDEX idx_kb_status ON knowledge_bases(status);
```

**kb_permissions**
```sql
CREATE TABLE kb_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(10) NOT NULL, -- READ, WRITE, ADMIN
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(kb_id, user_id)
);
CREATE INDEX idx_kbp_user ON kb_permissions(user_id);
CREATE INDEX idx_kbp_kb ON kb_permissions(kb_id);
```

**documents**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path
    checksum VARCHAR(64) NOT NULL, -- SHA-256
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, ready, failed
    chunk_count INTEGER DEFAULT 0,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    last_error TEXT,
    retry_count INTEGER DEFAULT 0,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    deleted_at TIMESTAMPTZ, -- soft delete
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_doc_kb ON documents(kb_id);
CREATE INDEX idx_doc_status ON documents(status);
CREATE INDEX idx_doc_deleted ON documents(deleted_at) WHERE deleted_at IS NOT NULL;
```

**outbox**
```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- document.process, document.delete, kb.delete
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_outbox_pending ON outbox(created_at) WHERE processed_at IS NULL;
```

#### Qdrant Collection Schema

```json
{
  "collection_name": "kb_{uuid}",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "payload_schema": {
    "document_id": "keyword",
    "document_name": "text",
    "page_number": "integer",
    "section_header": "text",
    "chunk_text": "text",
    "char_start": "integer",
    "char_end": "integer",
    "chunk_index": "integer"
  }
}
```

### API Endpoints

#### Knowledge Base Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v1/knowledge-bases` | Create KB | `KBCreate` | `KBResponse` |
| GET | `/api/v1/knowledge-bases` | List user's KBs | - | `List[KBSummary]` |
| GET | `/api/v1/knowledge-bases/{id}` | Get KB details | - | `KBResponse` |
| PATCH | `/api/v1/knowledge-bases/{id}` | Update KB | `KBUpdate` | `KBResponse` |
| DELETE | `/api/v1/knowledge-bases/{id}` | Archive KB | - | 204 |
| POST | `/api/v1/knowledge-bases/{id}/permissions` | Add permission | `PermissionCreate` | `PermissionResponse` |
| DELETE | `/api/v1/knowledge-bases/{id}/permissions/{user_id}` | Remove permission | - | 204 |

#### Document Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v1/knowledge-bases/{kb_id}/documents` | Upload document | `multipart/form-data` | 202 `DocumentResponse` |
| GET | `/api/v1/knowledge-bases/{kb_id}/documents` | List documents | `?page&limit&status` | `PaginatedDocuments` |
| GET | `/api/v1/knowledge-bases/{kb_id}/documents/{id}` | Get document | - | `DocumentResponse` |
| GET | `/api/v1/knowledge-bases/{kb_id}/documents/{id}/status` | Get status | - | `DocumentStatus` |
| DELETE | `/api/v1/knowledge-bases/{kb_id}/documents/{id}` | Delete document | - | 204 |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents/{id}/retry` | Retry failed | - | 202 |

### Pydantic Schemas

```python
# schemas/knowledge_base.py
class KBCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)

class KBUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)

class KBSummary(BaseModel):
    id: str
    name: str
    document_count: int
    permission_level: str
    updated_at: datetime

class KBResponse(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    status: str
    document_count: int
    total_size_bytes: int
    created_at: datetime
    updated_at: datetime

# schemas/document.py
class DocumentResponse(BaseModel):
    id: str
    name: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    chunk_count: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    last_error: str | None
    uploaded_by: str
    created_at: datetime

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
```

### Processing Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ DOCUMENT PROCESSING PIPELINE (Celery Task)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DOWNLOAD (5s timeout)                                                    │
│     ├─ Fetch from MinIO: kb-{uuid}/{doc-uuid}/{filename}                     │
│     ├─ Validate checksum matches                                             │
│     └─ Store in /tmp/{task_id}/                                              │
│                                                                              │
│  2. PARSE (60s timeout per format)                                           │
│     ├─ PDF: unstructured.partition_pdf()                                     │
│     │   └─ Extract: text, page_number, coordinates                           │
│     ├─ DOCX: unstructured.partition_docx()                                   │
│     │   └─ Extract: text, section_headers                                    │
│     └─ MD: unstructured.partition_md()                                       │
│         └─ Extract: text, heading_levels                                     │
│                                                                              │
│  3. VALIDATE                                                                 │
│     ├─ Check extracted_text.length > 100 chars                               │
│     ├─ If empty: mark FAILED "No text content found"                         │
│     └─ If scanned PDF detected: mark FAILED "OCR required (MVP 2)"           │
│                                                                              │
│  4. CHUNK (30s timeout)                                                      │
│     ├─ Splitter: RecursiveCharacterTextSplitter                              │
│     ├─ Chunk size: 500 tokens                                                │
│     ├─ Overlap: 50 tokens (10%)                                              │
│     └─ Preserve metadata: page, section, char_start, char_end                │
│                                                                              │
│  5. EMBED (5s per chunk, batch of 20)                                        │
│     ├─ Model: text-embedding-ada-002 via LiteLLM                             │
│     ├─ Dimensions: 1536                                                      │
│     ├─ Retry: 5x with exponential backoff (429 handling)                     │
│     └─ Batch size: 20 chunks per request                                     │
│                                                                              │
│  6. INDEX (30s timeout)                                                      │
│     ├─ Collection: kb_{kb_uuid}                                              │
│     ├─ Point ID: {doc_uuid}_{chunk_index}                                    │
│     ├─ Payload: full metadata for citations                                  │
│     └─ Upsert: idempotent for retry safety                                   │
│                                                                              │
│  7. COMPLETE                                                                 │
│     ├─ Update document: status=READY, chunk_count=N                          │
│     ├─ Update processing_completed_at                                        │
│     ├─ Mark outbox event as processed                                        │
│     └─ Cleanup /tmp/{task_id}/                                               │
│                                                                              │
│  ERROR HANDLING                                                              │
│     ├─ Any step fails: retry up to 3 times                                   │
│     ├─ After 3 retries: mark FAILED with last_error                          │
│     └─ Cleanup temp files on any exit                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Edge Case Handling

| Category | Edge Case | Detection | Handling |
|----------|-----------|-----------|----------|
| **Upload** | File >50MB | API validation | 413 response, clear message |
| **Upload** | Zero-byte file | API validation | 400 response |
| **Upload** | Invalid MIME type | API validation | 400 response |
| **Parsing** | Password-protected PDF | unstructured exception | FAILED + "Password-protected PDF" |
| **Parsing** | Scanned PDF (no text) | chunk_count = 0 | FAILED + "Document appears to be scanned" |
| **Chunking** | Empty after parse | len(chunks) == 0 | FAILED + "No text content found" |
| **Embedding** | Rate limit (429) | LiteLLM status | Exponential backoff, retry 5x |
| **Embedding** | Token limit exceeded | LiteLLM exception | Split chunk, re-embed |
| **Indexing** | Dimension mismatch | Qdrant exception | FAILED + alert to admin |
| **Infra** | Worker crash | Visibility timeout | Task requeued automatically |

### Frontend Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `kb-selector.tsx` | `components/kb/` | Sidebar KB list with permission icons |
| `kb-create-modal.tsx` | `components/kb/` | Create KB form dialog |
| `document-list.tsx` | `components/documents/` | Paginated document table |
| `document-card.tsx` | `components/documents/` | Single document with status |
| `upload-dropzone.tsx` | `components/documents/` | Drag-drop upload area |
| `upload-progress.tsx` | `components/documents/` | Multi-file upload progress |
| `processing-status.tsx` | `components/documents/` | Status badge with polling |

### Service Layer Design

```python
# services/kb_service.py
class KBService:
    async def create(self, data: KBCreate, user: User) -> KnowledgeBase
    async def get(self, kb_id: str, user: User) -> KnowledgeBase
    async def list_for_user(self, user: User) -> list[KBSummary]
    async def update(self, kb_id: str, data: KBUpdate, user: User) -> KnowledgeBase
    async def archive(self, kb_id: str, user: User) -> None
    async def add_permission(self, kb_id: str, user_id: str, level: str, admin: User) -> None
    async def check_permission(self, kb_id: str, user: User, required: str) -> bool

# services/document_service.py
class DocumentService:
    async def upload(self, kb_id: str, file: UploadFile, user: User) -> Document
    async def list(self, kb_id: str, user: User, page: int, limit: int) -> PaginatedResult
    async def get(self, doc_id: str, user: User) -> Document
    async def delete(self, doc_id: str, user: User) -> None
    async def retry(self, doc_id: str, user: User) -> None
    async def get_status(self, doc_id: str, user: User) -> DocumentStatus

# workers/document_tasks.py
@celery_app.task(bind=True, max_retries=3)
def process_document(self, doc_id: str) -> None
    # Full pipeline: download → parse → chunk → embed → index → complete
```

### Service Blueprint

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTSTAGE (User-Facing)                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  User Action     →  Drag file to   →  See progress  →  See PENDING  →  See READY      │
│                     upload zone        bar               status         + chunk count   │
│  UI Component    →  UploadDropzone →  UploadProgress → DocumentCard → DocumentCard    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                    LINE OF INTERACTION                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  API Endpoint    →  POST /documents → GET /documents/{id}/status  →  GET /documents    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                    LINE OF VISIBILITY                                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                    BACKSTAGE (Services)                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  DocumentService →  Validate file  →  Upload to    →  Create DB   →  Emit outbox      │
│                     (type, size)      MinIO           record          event            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                    SUPPORT PROCESSES                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  OutboxWorker    →  Poll outbox   →  Dispatch to Celery                                │
│  DocumentTask    →  Download file →  Parse → Chunk → Embed → Index → Update status    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## Non-Functional Requirements

### Performance Requirements

| Metric | Target | Measurement | Rationale |
|--------|--------|-------------|-----------|
| **Upload response time** | <2s for 50MB | API latency (P95) | User feedback immediacy |
| **Document list load** | <500ms | Frontend metric | Smooth KB navigation |
| **Status polling** | <200ms | API latency (P95) | Minimal UI blocking |
| **Processing throughput** | 10 docs/min/worker | Queue metrics | Scalable with worker count |
| **Embedding batch** | 20 chunks/request | LiteLLM config | Balance cost vs latency |

### Scalability Requirements

| Component | MVP 1 Target | Scaling Strategy |
|-----------|--------------|------------------|
| **Documents per KB** | 1,000 | Pagination, lazy loading |
| **KBs per user** | 50 | Query optimization |
| **Concurrent uploads** | 5 per user | Rate limiting |
| **Queue depth** | 500 pending | Horizontal worker scaling |
| **Vector points per KB** | 100,000 | Qdrant sharding (MVP 2) |

### Reliability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Data durability** | 99.99% | PostgreSQL WAL, MinIO replication |
| **Processing completion** | 99% within 10 min | Retry mechanism, dead letter queue |
| **Zero data loss on failure** | 100% | Transactional outbox pattern |
| **Orphan cleanup** | <24 hours | Hourly reconciliation job |

### Security Requirements

| Requirement | Implementation | Validation |
|-------------|----------------|------------|
| **Permission enforcement** | Check on every endpoint | Integration tests |
| **File validation** | MIME type + magic bytes | Unit tests |
| **Sandboxed parsing** | Isolated worker process | Architecture review |
| **Checksum verification** | SHA-256 on upload/download | Integration tests |
| **Rate limiting** | 10 uploads/min/user | API middleware |
| **Storage quota** | 1GB per KB (configurable) | Service layer check |

### Observability Requirements

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| **Queue depth** | Gauge | >100 pending |
| **Processing time** | Histogram | P95 >5 min |
| **Failed documents** | Counter | >5% failure rate |
| **Worker health** | Heartbeat | Missing >30s |
| **Storage usage** | Gauge | >80% quota |
| **Embedding cost** | Counter | >$10/day |

## Dependencies and Integrations

### Internal Dependencies

| Dependency | Source | Required By | Integration Point |
|------------|--------|-------------|-------------------|
| **User authentication** | Epic 1 | All endpoints | JWT middleware |
| **User model** | Epic 1 | KB ownership, permissions | Foreign key |
| **API framework** | Epic 1 | All endpoints | FastAPI app |
| **Database session** | Epic 1 | All services | Async SQLAlchemy |
| **Error handling** | Epic 1 | All code | `app/core/exceptions.py` |
| **Logging** | Epic 1 | All code | `app/core/logging.py` |

### External Service Dependencies

| Service | Version | Purpose | Failure Mode |
|---------|---------|---------|--------------|
| **PostgreSQL** | 15+ | Source of truth | Fatal - service unavailable |
| **Qdrant** | 1.7+ | Vector storage | Fatal for search, graceful for upload |
| **MinIO** | Latest | File storage | Fatal - upload fails |
| **Redis** | 7+ | Celery broker | Fatal - processing stops |
| **LiteLLM** | 1.0+ | Embedding proxy | Retry with backoff |

### Library Dependencies

| Library | Version | Purpose | Pinned |
|---------|---------|---------|--------|
| **unstructured** | ^0.10 | Document parsing | Yes |
| **langchain** | ^0.1 | Text chunking | Yes |
| **litellm** | ^1.0 | Embedding API | Yes |
| **qdrant-client** | ^1.7 | Vector operations | Yes |
| **minio** | ^7.2 | Object storage client | Yes |
| **celery** | ^5.3 | Task queue | Yes |

### Integration Contracts

```python
# Expected from Epic 1
from app.core.auth import get_current_user  # Returns User model
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.logging import get_logger
from app.db.session import get_async_session

# Provided to Epic 3
from app.services.kb_service import KBService  # KB access with permission check
from app.models.document import Document  # Document model for search context
# Qdrant collection naming: kb_{uuid}
# Chunk metadata schema (see Qdrant Collection Schema above)
```

## Acceptance Criteria and Traceability

### Story-to-Requirement Traceability

| Story | PRD Requirement | Architecture Component | Acceptance Criteria |
|-------|-----------------|------------------------|---------------------|
| **2.1** KB CRUD | FR-KB-001 | `kb_service.py`, PostgreSQL | KB created with Qdrant collection |
| **2.2** KB Permissions | FR-KB-002 | `kb_permissions` table | READ/WRITE/ADMIN enforced |
| **2.3** Document Upload | FR-DOC-001 | `document_service.py`, MinIO | File stored, DB record created |
| **2.4** Processing Worker | FR-DOC-002 | `document_tasks.py`, Celery | Document processed to READY |
| **2.5** Chunking | FR-DOC-003 | LangChain splitter | 500 tokens, 50 overlap |
| **2.6** Embedding | FR-DOC-004 | LiteLLM, Qdrant | Vectors indexed with metadata |
| **2.7** Status API | FR-DOC-005 | Status endpoint | Real-time status returned |
| **2.8** Document List | FR-DOC-006 | List endpoint, React table | Paginated with filters |
| **2.9** Document Delete | FR-DOC-007 | Soft delete, cleanup job | Vectors + files removed |
| **2.10** Outbox Pattern | NFR-CONSISTENCY | `outbox` table, worker | Zero data loss |
| **2.11** Re-upload | FR-DOC-008 | Atomic replacement | Old vectors replaced |
| **2.12** KB UI | FR-KB-003 | React components | KB CRUD in sidebar |

### Epic-Level Acceptance Criteria

| ID | Criterion | Validation Method |
|----|-----------|-------------------|
| **AC-E2-01** | User can create KB and see it in sidebar | E2E test |
| **AC-E2-02** | User can upload PDF/DOCX/MD up to 50MB | Integration test |
| **AC-E2-03** | Document processing completes within 10 minutes | Performance test |
| **AC-E2-04** | Failed documents show clear error message | Manual QA |
| **AC-E2-05** | Deleted documents are fully removed within 24h | Integration test |
| **AC-E2-06** | User without permission cannot access KB | Security test |
| **AC-E2-07** | System recovers from worker crash | Chaos test |
| **AC-E2-08** | Processing status updates every 5 seconds in UI | E2E test |

### Definition of Done (Epic Level)

```
Epic 2 is DONE when:
- [ ] All 12 stories completed and merged
- [ ] Unit test coverage ≥80% for backend
- [ ] Frontend test coverage ≥70%
- [ ] E2E tests pass for critical paths (upload, process, list)
- [ ] No P1/P2 bugs open
- [ ] Performance targets met (see NFRs)
- [ ] Security review completed
- [ ] Documentation updated (API docs, README)
- [ ] Deployed to staging and smoke tested
```

## Risks and Test Strategy

### Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|-------------|--------|------------|-------|
| **R1** | LiteLLM rate limiting causes processing delays | High | Medium | Exponential backoff, queue depth monitoring | Dev |
| **R2** | Large PDFs cause worker memory exhaustion | Medium | High | 50MB limit, streaming parsing | Dev |
| **R3** | Qdrant collection corruption | Low | Critical | Snapshot backups, collection isolation | Ops |
| **R4** | MinIO unavailability blocks uploads | Low | High | Health checks, circuit breaker | Ops |
| **R5** | Orphaned vectors after failed deletes | Medium | Medium | Reconciliation job, monitoring | Dev |
| **R6** | Embedding costs exceed budget | Medium | High | Cost tracking, per-KB limits | PM |
| **R7** | Password-protected PDFs fail silently | Medium | Low | Clear error message, user guidance | Dev |
| **R8** | Worker deadlock on malformed files | Low | Medium | Task timeout, sandboxed parsing | Dev |

### Test Strategy

#### Unit Tests (Backend)

| Component | Test Focus | Coverage Target |
|-----------|------------|-----------------|
| `kb_service.py` | Permission logic, CRUD operations | 90% |
| `document_service.py` | Upload validation, status transitions | 85% |
| `document_tasks.py` | Pipeline step isolation, error handling | 80% |
| Pydantic schemas | Validation rules, edge cases | 95% |

#### Integration Tests (Backend)

| Scenario | Dependencies | Approach |
|----------|--------------|----------|
| KB CRUD with Qdrant | PostgreSQL, Qdrant | Testcontainers |
| Document upload flow | PostgreSQL, MinIO | Testcontainers |
| Processing pipeline | All services | Docker Compose |
| Permission enforcement | PostgreSQL | Testcontainers |

#### Frontend Tests

| Component | Test Type | Priority |
|-----------|-----------|----------|
| `kb-selector.tsx` | Component | P1 |
| `upload-dropzone.tsx` | Component + Integration | P1 |
| `document-list.tsx` | Component | P1 |
| `processing-status.tsx` | Component | P2 |
| Upload flow | Integration | P1 |

#### E2E Tests (Playwright)

| Journey | Steps | Priority |
|---------|-------|----------|
| **KB Creation** | Login → Create KB → Verify in sidebar | P1 |
| **Document Upload** | Select KB → Upload file → See PENDING | P1 |
| **Processing Complete** | Upload → Wait → See READY + chunk count | P1 |
| **Document Delete** | Select doc → Delete → Confirm removed | P2 |
| **Permission Denied** | Try access KB without permission → See error | P2 |

#### Performance Tests

| Test | Tool | Success Criteria |
|------|------|------------------|
| Upload throughput | k6 | 10 concurrent uploads, <2s each |
| Processing latency | Custom script | 10 docs processed in <10 min |
| List query performance | k6 | 1000 docs, <500ms response |
| Status polling load | k6 | 100 concurrent polls, <200ms |

#### Security Tests

| Test | Method | Validation |
|------|--------|------------|
| Permission bypass | Manual penetration | No unauthorized access |
| Malicious file upload | Automated scan | Files sanitized |
| SQL injection | OWASP ZAP | No vulnerabilities |
| Rate limit enforcement | k6 | Limits enforced |

### Test Environment

```yaml
# docker-compose.test.yml additions
services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: lumikb_test

  test-qdrant:
    image: qdrant/qdrant:v1.7.0

  test-minio:
    image: minio/minio
    command: server /data

  test-redis:
    image: redis:7-alpine
```

### Test Data Strategy

| Data Type | Source | Management |
|-----------|--------|------------|
| Users | Factories (`UserFactory`) | Created per test |
| KBs | Factories (`KBFactory`) | Created per test |
| Documents | Fixture files (small PDF, DOCX, MD) | In `tests/fixtures/` |
| Embeddings | Mocked LiteLLM responses | Deterministic vectors |

---

## Appendix: Story Summary

| Story | Title | Complexity | Dependencies |
|-------|-------|------------|--------------|
| 2.1 | Knowledge Base CRUD API | M | Epic 1 auth |
| 2.2 | KB Permission Management | M | 2.1 |
| 2.3 | Document Upload Endpoint | L | 2.1 |
| 2.4 | Document Processing Worker | XL | 2.3 |
| 2.5 | Text Chunking Implementation | M | 2.4 |
| 2.6 | Embedding Generation & Indexing | M | 2.5 |
| 2.7 | Processing Status API | S | 2.4 |
| 2.8 | Document List UI | M | 2.7 |
| 2.9 | Document Deletion | M | 2.6 |
| 2.10 | Transactional Outbox | L | 2.3 |
| 2.11 | Document Re-upload | M | 2.9 |
| 2.12 | KB Management UI | M | 2.1, 2.2 |

---

*Generated by Epic Tech Context Workflow - BMad Method*
*Last Updated: 2025-11-23*
