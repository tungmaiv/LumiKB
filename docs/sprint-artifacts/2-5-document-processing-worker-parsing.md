# Story 2.5: Document Processing Worker - Parsing

Status: done

## Story

As a **system**,
I want **to parse uploaded documents and extract text**,
So that **content can be chunked and embedded for semantic search**.

## Acceptance Criteria

1. **Given** a document is in PENDING status with an outbox event `document.process` **When** the Celery worker picks up the processing event **Then**:
   - The document status is updated to `PROCESSING`
   - `processing_started_at` timestamp is set
   - The file is downloaded from MinIO using the stored `file_path`
   - File checksum is validated against the stored checksum

2. **Given** a PDF document **When** parsing completes **Then**:
   - Text content is extracted using `unstructured.partition_pdf()`
   - Page numbers are extracted and preserved in metadata
   - Any images/figures are noted but text is prioritized

3. **Given** a DOCX document **When** parsing completes **Then**:
   - Text content is extracted using `unstructured.partition_docx()`
   - Section headers are extracted and preserved
   - Text formatting is converted to plain text

4. **Given** a Markdown document **When** parsing completes **Then**:
   - Text content is extracted using `unstructured.partition_md()`
   - Heading structure is extracted and preserved

5. **Given** parsing extracts less than 100 characters of text **When** validation runs **Then**:
   - Document status is set to `FAILED`
   - `last_error` is set to "No text content found (extracted {n} chars, minimum 100)"

6. **Given** a scanned PDF (image-only, no extractable text) **When** parsing completes **Then**:
   - Document status is set to `FAILED`
   - `last_error` is set to "Document appears to be scanned (OCR required - MVP 2)"

7. **Given** a password-protected PDF **When** parsing fails **Then**:
   - Document status is set to `FAILED`
   - `last_error` is set to "Password-protected PDF cannot be processed"

8. **Given** parsing fails for any reason **When** max retries (3) are exhausted **Then**:
   - Document status is set to `FAILED`
   - `last_error` contains the failure reason
   - `retry_count` is incremented to reflect total attempts
   - Outbox event is marked as processed (to stop retries)

9. **Given** parsing completes successfully **When** the worker finishes **Then**:
   - Parsed content (text + metadata) is stored temporarily for chunking step (Story 2.6)
   - Worker emits a success log with document_id and extracted_chars count
   - Temporary files are cleaned up from `/tmp/{task_id}/`

## Tasks / Subtasks

- [x] **Task 1: Set up Celery worker infrastructure** (AC: 1)
  - [x] Create `backend/app/workers/celery_app.py` with Celery configuration
  - [x] Configure Redis as broker and result backend
  - [x] Set up task routing and queues: `default`, `document_processing`
  - [x] Configure task visibility timeout (10 minutes for document processing)
  - [x] Add `celery` command to `docker-compose.yaml` for worker

- [x] **Task 2: Create outbox processor task** (AC: 1)
  - [x] Create `backend/app/workers/outbox_tasks.py`
  - [x] Implement `process_outbox_events()` periodic task (runs every 10 seconds)
  - [x] Query outbox for unprocessed events (`processed_at IS NULL`, `attempts < 5`)
  - [x] Dispatch to appropriate handler based on `event_type`
  - [x] Mark events as processed or increment attempts on failure

- [x] **Task 3: Create document parsing task** (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9)
  - [x] Create `backend/app/workers/document_tasks.py`
  - [x] Implement `process_document(doc_id: str)` Celery task:
    - Update status to PROCESSING, set `processing_started_at`
    - Download file from MinIO to `/tmp/{task_id}/`
    - Validate checksum matches stored value
    - Parse based on MIME type (PDF, DOCX, MD)
    - Validate extracted text length >= 100 chars
    - Store parsed content for next step
    - Handle all failure modes with appropriate error messages
  - [x] Configure task with `bind=True`, `max_retries=3`, `retry_backoff=True`

- [x] **Task 4: Create unstructured parsing utilities** (AC: 2, 3, 4, 6, 7)
  - [x] Create `backend/app/workers/parsing.py`
  - [x] Implement `parse_pdf(file_path: str) -> ParsedContent`
    - Use `unstructured.partition_pdf()` with strategy="auto"
    - Extract page numbers from element metadata
    - Detect scanned PDFs (no text elements extracted)
    - Handle password-protected PDFs (catch exception)
  - [x] Implement `parse_docx(file_path: str) -> ParsedContent`
    - Use `unstructured.partition_docx()`
    - Extract section headers from Title/Heading elements
  - [x] Implement `parse_markdown(file_path: str) -> ParsedContent`
    - Use `unstructured.partition_md()`
    - Extract heading structure
  - [x] Define `ParsedContent` dataclass with: `text`, `elements`, `metadata`

- [x] **Task 5: Create parsed content storage mechanism** (AC: 9)
  - [x] Define strategy for passing parsed content to chunking task (Story 2.6)
  - [x] Option B: Store as JSON in MinIO at `{kb_id}/{doc_id}/.parsed.json` ✓ CHOSEN
  - [x] Implement chosen storage approach at `backend/app/workers/parsed_content_storage.py`
  - [x] Include metadata: `extracted_chars`, `page_count`, `section_count`

- [x] **Task 6: Add unstructured library dependencies** (AC: 2, 3, 4)
  - [x] Add `unstructured[pdf,docx,md]` to `pyproject.toml`
  - [x] Add `poppler-utils` to Dockerfile for PDF parsing
  - [x] Add `tesseract-ocr` placeholder comment (for MVP 2 OCR)
  - [x] Verify parsing works in Docker environment

- [x] **Task 7: Update settings for worker configuration** (AC: 1)
  - [x] Add to `backend/app/core/config.py`:
    - `CELERY_BROKER_URL` (Redis)
    - `CELERY_RESULT_BACKEND` (Redis)
    - `DOCUMENT_PROCESSING_TIMEOUT` (600 seconds)
    - `MAX_PARSING_RETRIES` (3)
  - [x] Add environment variables to `.env`

- [x] **Task 8: Write unit tests for parsing utilities** (AC: 2, 3, 4, 5, 6, 7)
  - [x] Create `backend/tests/unit/test_parsing.py`
  - [x] Test PDF parsing with text extraction and page metadata
  - [x] Test DOCX parsing with section headers
  - [x] Test Markdown parsing with heading structure
  - [x] Test empty document detection (<100 chars)
  - [x] Test scanned PDF detection (mock unstructured response)
  - [x] Test password-protected PDF handling (mock exception)

- [x] **Task 9: Write integration tests for document processing** (AC: 1, 8, 9)
  - [x] Create `backend/tests/integration/test_document_processing.py`
  - [x] Test outbox event triggers processing
  - [x] Test status transitions: PENDING → PROCESSING → (READY via 2.6 | FAILED)
  - [x] Test retry mechanism on transient failures
  - [x] Test max retries exhaustion marks FAILED
  - [x] Test cleanup of temporary files
  - [x] Use test fixtures: `sample.md`

- [x] **Task 10: Add worker health check endpoint** (AC: 1)
  - [x] Add `GET /api/v1/health/workers` endpoint
  - [x] Check Celery worker availability via `ping` task
  - [x] Return worker count and queue depth

## Dev Notes

### Learnings from Previous Story

**From Story 2-4-document-upload-api-and-storage (Status: done)**

- **MinIO Integration Available**: `MinIOService` class at `backend/app/integrations/minio_client.py` with:
  - `download_file(kb_id, object_path) -> bytes` - USE THIS to fetch documents
  - `file_exists(kb_id, object_path) -> bool` - Verify file before download
- **Document Model**: Extended with `file_path`, `checksum`, `processing_started_at`, `processing_completed_at`, `retry_count`, `last_error`
- **Outbox Pattern**: `document.process` event type already used. Outbox table has `aggregate_id` (document_id), `payload` with `{"document_id": ..., "kb_id": ...}`
- **Checksum**: SHA-256 stored in `document.checksum` - validate on download
- **Status Machine**: `PENDING` → `PROCESSING` → `READY` | `FAILED`
- **Service Pattern**: `DocumentService` at `backend/app/services/document_service.py` for transaction handling
- **Test Patterns**: Factories at `tests/factories/document_factory.py`, fixtures at `tests/fixtures/`

[Source: docs/sprint-artifacts/2-4-document-upload-api-and-storage.md#Dev-Agent-Record]

### Architecture Patterns and Constraints

**From Tech Spec and Architecture:**

| Constraint | Requirement | Source |
|------------|-------------|--------|
| Task Queue | Celery with Redis broker, AOF persistence | architecture.md#Decision-Summary |
| Parsing Library | unstructured with format-specific loaders | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Timeouts | 60s per format for parsing, 10 min visibility timeout | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Retry Logic | 3 retries with exponential backoff | tech-spec-epic-2.md#Failure-Handling-Strategy |
| Temp Storage | `/tmp/{task_id}/` for downloaded files | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Content Validation | Minimum 100 chars extracted | tech-spec-epic-2.md#Processing-Pipeline-Detail |

**Document Processing Pipeline (This Story = Steps 1-3):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DOWNLOAD (5s timeout)                                        │
│    ├─ Fetch from MinIO: kb-{uuid}/{doc-uuid}/{filename}         │
│    ├─ Validate checksum matches                                 │
│    └─ Store in /tmp/{task_id}/                                  │
│                                                                  │
│ 2. PARSE (60s timeout per format)                               │
│    ├─ PDF: unstructured.partition_pdf()                         │
│    │   └─ Extract: text, page_number, coordinates               │
│    ├─ DOCX: unstructured.partition_docx()                       │
│    │   └─ Extract: text, section_headers                        │
│    └─ MD: unstructured.partition_md()                           │
│        └─ Extract: text, heading_levels                         │
│                                                                  │
│ 3. VALIDATE                                                      │
│    ├─ Check extracted_text.length > 100 chars                   │
│    ├─ If empty: mark FAILED "No text content found"             │
│    └─ If scanned PDF detected: mark FAILED "OCR required"       │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼ (Story 2.6: Chunking & Embedding)
```

**Celery Task Configuration:**

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # seconds
    retry_backoff=True,
    retry_backoff_max=300,
    soft_time_limit=540,  # 9 min
    time_limit=600,       # 10 min hard limit
    acks_late=True,       # Ensure task completion before ack
)
def process_document(self, doc_id: str) -> None:
    ...
```

**Outbox Processing Pattern:**

```python
# Run every 10 seconds via Celery Beat
@celery_app.task
def process_outbox_events():
    events = outbox_repo.get_pending_events(limit=100)
    for event in events:
        try:
            dispatch_event(event)
            outbox_repo.mark_processed(event.id)
        except Exception as e:
            outbox_repo.increment_attempts(event.id, str(e))
```

### Project Structure Notes

**Files to Create:**

```
backend/
├── app/
│   └── workers/
│       ├── __init__.py              # NEW
│       ├── celery_app.py            # NEW - Celery configuration
│       ├── outbox_tasks.py          # NEW - Outbox processor
│       ├── document_tasks.py        # NEW - Document processing task
│       └── parsing.py               # NEW - Parsing utilities
└── tests/
    ├── fixtures/
    │   ├── sample.pdf               # NEW - Test PDF file
    │   ├── sample.docx              # NEW - Test DOCX file
    │   └── sample.md                # NEW - Test Markdown file
    ├── unit/
    │   └── test_parsing.py          # NEW - Parsing unit tests
    └── integration/
        └── test_document_processing.py  # NEW - Processing integration tests
```

**Files to Modify:**

```
backend/
├── app/
│   ├── core/
│   │   └── config.py                # ADD Celery settings
│   └── integrations/
│       └── minio_client.py          # ADD download_file() if missing
├── pyproject.toml                   # ADD unstructured dependencies
├── Dockerfile                       # ADD poppler-utils for PDF
└── docker-compose.yaml              # ADD celery worker service
```

### Testing Requirements

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| `pytestmark` on all test files | testing-backend-specification.md | CI gate |
| Factories for test data | testing-backend-specification.md | Code review |
| Unit tests < 5s | testing-backend-specification.md | `pytest-timeout` |
| Integration tests < 30s | testing-backend-specification.md | `pytest-timeout` |
| Mock unstructured in unit tests | testing-backend-specification.md | Unit isolation |
| Real parsing in integration tests | testing-backend-specification.md | Full stack validation |

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Processing-Pipeline-Detail] - Full pipeline specification
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Edge-Case-Handling] - Error handling patterns
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Failure-Handling-Strategy] - Retry configuration
- [Source: docs/architecture.md#Decision-Summary] - Celery + Redis decision
- [Source: docs/epics.md#Story-2.5] - Original story definition and ACs
- [Source: docs/testing-backend-specification.md] - Testing patterns for backend
- [Source: docs/coding-standards.md] - Python coding standards

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

**Completed:** 2025-11-24
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing (19/19)

**Implementation Summary:**
- Celery worker infrastructure with Redis broker
- Outbox processor for reliable event processing
- Document parsing using unstructured library (PDF, DOCX, Markdown)
- Parsed content storage in MinIO as JSON
- Worker health check endpoints
- Full test coverage with unit and integration tests

### File List

**Files Created:**
- `backend/app/workers/__init__.py`
- `backend/app/workers/celery_app.py`
- `backend/app/workers/outbox_tasks.py`
- `backend/app/workers/document_tasks.py`
- `backend/app/workers/parsing.py`
- `backend/app/workers/parsed_content_storage.py`
- `backend/app/api/v1/health.py`
- `backend/tests/unit/test_parsing.py`
- `backend/tests/integration/test_document_processing.py`
- `backend/tests/fixtures/sample.md`

**Files Modified:**
- `backend/app/core/config.py`
- `backend/app/integrations/minio_client.py`
- `backend/app/main.py`
- `backend/app/api/v1/__init__.py`
- `infrastructure/docker/docker-compose.yml`
- `backend/Dockerfile`
- `backend/pyproject.toml`
- `backend/tests/factories/document_factory.py`
- `backend/tests/factories/kb_factory.py`

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-24 | Initial draft created from tech-spec-epic-2.md, architecture.md, epics.md, and story 2-4 learnings | SM Agent (Bob) |
