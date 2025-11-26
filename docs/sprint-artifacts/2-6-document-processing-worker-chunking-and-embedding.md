# Story 2.6: Document Processing Worker - Chunking and Embedding

Status: done

## Story

As a **system**,
I want **to chunk parsed documents and generate embeddings**,
So that **content can be stored in Qdrant for semantic search**.

## Acceptance Criteria

1. **Given** a document has been parsed successfully (`.parsed.json` exists in MinIO) **When** the chunking step runs **Then**:
   - Text is split into semantic chunks using LangChain's `RecursiveCharacterTextSplitter`
   - Target chunk size: 500 tokens
   - Chunk overlap: 50 tokens (10%)
   - Each chunk retains metadata: `document_id`, `document_name`, `page_number`, `section_header`, `char_start`, `char_end`, `chunk_index`

2. **Given** chunks are created **When** the embedding step runs **Then**:
   - Embeddings are generated via LiteLLM proxy (default: `text-embedding-ada-002`)
   - Embedding dimensions: 1536
   - Batch size: 20 chunks per API request
   - Rate limit handling: exponential backoff on 429 responses (max 5 retries)

3. **Given** embeddings are generated **When** the indexing step runs **Then**:
   - Vectors are upserted to Qdrant collection `kb_{kb_id}`
   - Point ID format: `{doc_id}_{chunk_index}` (deterministic for idempotent retries)
   - Each point payload includes: `document_id`, `document_name`, `page_number`, `section_header`, `chunk_text`, `char_start`, `char_end`, `chunk_index`

4. **Given** all steps complete successfully **When** the worker finishes **Then**:
   - Document status is updated to `READY`
   - `chunk_count` is set on the document record
   - `processing_completed_at` timestamp is set
   - Outbox event is marked as processed
   - Parsed content JSON is deleted from MinIO (cleanup)

5. **Given** embedding API returns 429 (rate limit) **When** retry logic runs **Then**:
   - Exponential backoff is applied: 30s, 60s, 120s, 240s, 300s (max)
   - After 5 retries, task fails and document status is set to `FAILED`
   - `last_error` contains "Embedding rate limit exceeded after 5 retries"

6. **Given** embedding returns token limit exceeded error **When** a single chunk exceeds token limit **Then**:
   - The oversized chunk is split further (halved recursively until fits)
   - Re-embedded with smaller chunks
   - Original metadata preserved with adjusted `char_start`/`char_end`

7. **Given** Qdrant upsert fails **When** max retries (3) exhausted **Then**:
   - Document status is set to `FAILED`
   - `last_error` contains the Qdrant error message
   - Any partial vectors are NOT cleaned up (idempotent retry will overwrite)

8. **Given** this is a document re-upload (existing vectors exist) **When** processing completes **Then**:
   - New vectors are upserted with same point ID pattern
   - Old vectors with orphaned chunk indices are deleted
   - Atomic switch: new vectors available before old orphans removed

## Tasks / Subtasks

- [x] **Task 1: Create chunking module** (AC: 1, 6)
  - [x] Create `backend/app/workers/chunking.py`
  - [x] Implement `chunk_document(parsed_content: ParsedContent) -> list[DocumentChunk]`
  - [x] Use `RecursiveCharacterTextSplitter` with `chunk_size=500`, `chunk_overlap=50`
  - [x] Configure token counting using `tiktoken` (cl100k_base encoding for ada-002)
  - [x] Preserve page_number and section_header metadata from parsed elements
  - [x] Calculate char_start/char_end offsets for each chunk
  - [x] Handle oversized chunks by recursive splitting

- [x] **Task 2: Create embedding module** (AC: 2, 5, 6)
  - [x] Create `backend/app/workers/embedding.py`
  - [x] Implement `generate_embeddings(chunks: list[DocumentChunk]) -> list[Embedding]`
  - [x] Use LiteLLM client to call embedding API
  - [x] Batch chunks in groups of 20 for efficiency
  - [x] Implement exponential backoff for 429 responses (30s, 60s, 120s, 240s, 300s)
  - [x] Handle token limit errors by re-chunking and retrying
  - [x] Add retry decorator with max_retries=5

- [x] **Task 3: Create Qdrant indexing module** (AC: 3, 7, 8)
  - [x] Create `backend/app/workers/indexing.py`
  - [x] Implement `index_document(doc_id: str, kb_id: str, embeddings: list[Embedding]) -> int`
  - [x] Use `QdrantClient` from `backend/app/integrations/qdrant_client.py`
  - [x] Generate deterministic point IDs: `{doc_id}_{chunk_index}`
  - [x] Upsert vectors with full metadata payload
  - [x] Return chunk_count for document record update
  - [x] Implement `cleanup_orphan_chunks(doc_id: str, kb_id: str, max_index: int)` for re-uploads

- [x] **Task 4: Update document processing task** (AC: 1, 2, 3, 4)
  - [x] Modify `backend/app/workers/document_tasks.py`
  - [x] Add step 4: Load parsed content from MinIO `.parsed.json`
  - [x] Add step 5: Chunk document using `chunk_document()`
  - [x] Add step 6: Generate embeddings using `generate_embeddings()`
  - [x] Add step 7: Index in Qdrant using `index_document()`
  - [x] Add step 8: Update document status to READY, set chunk_count, processing_completed_at
  - [x] Add step 9: Clean up parsed content JSON from MinIO
  - [x] Ensure idempotent retry behavior throughout

- [x] **Task 5: Create/update Qdrant client integration** (AC: 3, 7, 8)
  - [x] Update `backend/app/integrations/qdrant_client.py`
  - [x] Add `upsert_points(collection: str, points: list[PointStruct]) -> None`
  - [x] Add `delete_points_by_filter(collection: str, filter: Filter) -> int`
  - [x] Add `get_collection_info(collection: str) -> CollectionInfo`
  - [x] Add health check method for worker startup validation
  - [x] Configure gRPC connection with timeout settings

- [x] **Task 6: Create LiteLLM embedding client** (AC: 2, 5)
  - [x] Create `backend/app/integrations/litellm_client.py`
  - [x] Implement `get_embeddings(texts: list[str], model: str = "text-embedding-ada-002") -> list[list[float]]`
  - [x] Configure LiteLLM proxy URL from settings
  - [x] Add retry logic with exponential backoff
  - [x] Add cost tracking (log tokens used)
  - [x] Handle batch size limits

- [x] **Task 7: Add configuration settings** (AC: 2, 5)
  - [x] Update `backend/app/core/config.py`:
    - `LITELLM_PROXY_URL` (default: http://litellm:4000)
    - `EMBEDDING_MODEL` (default: text-embedding-ada-002)
    - `EMBEDDING_BATCH_SIZE` (default: 20)
    - `EMBEDDING_MAX_RETRIES` (default: 5)
    - `CHUNK_SIZE` (default: 500)
    - `CHUNK_OVERLAP` (default: 50)
  - [x] Add to `.env.example`

- [x] **Task 8: Add dependencies** (AC: 1, 2, 3)
  - [x] Add to `backend/pyproject.toml`:
    - `langchain>=0.3.0,<1.0.0`
    - `langchain-text-splitters>=0.3.0,<1.0.0`
    - `tiktoken>=0.8.0,<1.0.0`
    - `litellm>=1.50.0,<2.0.0`
    - `qdrant-client>=1.10.0,<2.0.0`
  - [x] Update `backend/Dockerfile` if any system dependencies needed
  - [x] Run `pip install` and verify imports

- [x] **Task 9: Write unit tests for chunking** (AC: 1, 6)
  - [x] Create `backend/tests/unit/test_chunking.py`
  - [x] Test chunk size limits (500 tokens target)
  - [x] Test chunk overlap (50 tokens)
  - [x] Test metadata preservation (page_number, section_header)
  - [x] Test char_start/char_end accuracy
  - [x] Test oversized chunk handling (recursive split)
  - [x] Test empty document handling

- [x] **Task 10: Write unit tests for embedding** (AC: 2, 5, 6)
  - [x] Create `backend/tests/unit/test_embedding.py`
  - [x] Test batch processing (groups of 20)
  - [x] Test exponential backoff on 429 (mock LiteLLM)
  - [x] Test max retries exceeded behavior
  - [x] Test token limit error handling
  - [x] Test embedding dimension validation (1536)

- [x] **Task 11: Write unit tests for indexing** (AC: 3, 7, 8)
  - [x] Create `backend/tests/unit/test_indexing.py`
  - [x] Test point ID generation (`{doc_id}_{chunk_index}`)
  - [x] Test payload structure completeness
  - [x] Test upsert idempotency
  - [x] Test orphan chunk cleanup for re-uploads
  - [x] Test Qdrant error handling

- [x] **Task 12: Write integration tests for full pipeline** (AC: 1, 2, 3, 4, 8)
  - [x] Create `backend/tests/integration/test_chunking_embedding.py`
  - [x] Test full flow: parsed content -> chunks -> embeddings -> Qdrant
  - [x] Test status transitions: PROCESSING -> READY
  - [x] Test chunk_count accuracy
  - [x] Test cleanup of parsed JSON
  - [x] Test re-upload with orphan cleanup
  - [x] Use real Qdrant (testcontainers or docker-compose test)
  - [x] Mock LiteLLM with deterministic embeddings

## Dev Notes

### Learnings from Previous Story

**From Story 2-5-document-processing-worker-parsing (Status: done)**

- **Celery Infrastructure**: Worker configured at `backend/app/workers/celery_app.py` with Redis broker, task routing to `document_processing` queue
- **Parsed Content Storage**: JSON stored in MinIO at `{kb_id}/{doc_id}/.parsed.json` via `ParsedContentStorage` class
- **ParsedContent Dataclass**: Available at `backend/app/workers/parsing.py` with `text`, `elements`, `metadata` fields
- **Document Status Machine**: `PENDING` -> `PROCESSING` -> `READY` | `FAILED`
- **MinIO Client**: `download_file()` and `file_exists()` available at `backend/app/integrations/minio_client.py`
- **Task Configuration**: Use `bind=True`, `max_retries=3`, `retry_backoff=True` pattern
- **Test Patterns**: Factories at `tests/factories/`, fixtures at `tests/fixtures/sample.md`

[Source: docs/sprint-artifacts/2-5-document-processing-worker-parsing.md#Dev-Agent-Record]

### Architecture Patterns and Constraints

**From Tech Spec and Architecture:**

| Constraint | Requirement | Source |
|------------|-------------|--------|
| Chunk Size | 500 tokens target, 50 overlap | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Embedding Model | text-embedding-ada-002 via LiteLLM | architecture.md#Decision-Summary |
| Embedding Dimensions | 1536 | tech-spec-epic-2.md#Qdrant-Collection-Schema |
| Batch Size | 20 chunks per embedding request | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Qdrant Collection | `kb_{kb_uuid}`, cosine similarity | tech-spec-epic-2.md#Qdrant-Collection-Schema |
| Point ID Pattern | `{doc_uuid}_{chunk_index}` | tech-spec-epic-2.md#Processing-Pipeline-Detail |
| Rate Limit Handling | Exponential backoff, max 5 retries | tech-spec-epic-2.md#Failure-Handling-Strategy |

**Document Processing Pipeline (This Story = Steps 4-6):**

```
Previous Story (2.5):
┌─────────────────────────────────────────────────────────────────┐
│ 1-3. DOWNLOAD → PARSE → VALIDATE                                 │
│      Output: .parsed.json in MinIO                               │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
This Story (2.6):
┌─────────────────────────────────────────────────────────────────┐
│ 4. CHUNK (30s timeout)                                           │
│    ├─ Load .parsed.json from MinIO                               │
│    ├─ Splitter: RecursiveCharacterTextSplitter                   │
│    ├─ Chunk size: 500 tokens                                     │
│    ├─ Overlap: 50 tokens (10%)                                   │
│    └─ Preserve metadata: page, section, char_start, char_end     │
│                                                                  │
│ 5. EMBED (5s per chunk, batch of 20)                             │
│    ├─ Model: text-embedding-ada-002 via LiteLLM                  │
│    ├─ Dimensions: 1536                                           │
│    ├─ Retry: 5x with exponential backoff (429 handling)          │
│    └─ Batch size: 20 chunks per request                          │
│                                                                  │
│ 6. INDEX (30s timeout)                                           │
│    ├─ Collection: kb_{kb_uuid}                                   │
│    ├─ Point ID: {doc_uuid}_{chunk_index}                         │
│    ├─ Payload: full metadata for citations                       │
│    └─ Upsert: idempotent for retry safety                        │
│                                                                  │
│ 7. COMPLETE                                                      │
│    ├─ Update document: status=READY, chunk_count=N               │
│    ├─ Update processing_completed_at                             │
│    ├─ Mark outbox event as processed                             │
│    └─ Cleanup: delete .parsed.json from MinIO                    │
└─────────────────────────────────────────────────────────────────┘
```

**Qdrant Point Payload Schema (Citation-Critical):**

```json
{
  "document_id": "uuid-string",
  "document_name": "Annual Report 2024.pdf",
  "page_number": 15,
  "section_header": "Financial Highlights",
  "chunk_text": "Revenue increased by 23% year-over-year...",
  "char_start": 12450,
  "char_end": 12950,
  "chunk_index": 42
}
```

**Embedding Batch Configuration:**

```python
# Optimal batch settings for LiteLLM + OpenAI
EMBEDDING_BATCH_SIZE = 20  # Max chunks per request
EMBEDDING_TIMEOUT = 30     # seconds per batch
EMBEDDING_RETRY_DELAYS = [30, 60, 120, 240, 300]  # exponential backoff
```

### Project Structure Notes

**Files to Create:**

```
backend/
├── app/
│   ├── workers/
│   │   ├── chunking.py           # NEW - Text chunking utilities
│   │   ├── embedding.py          # NEW - Embedding generation
│   │   └── indexing.py           # NEW - Qdrant indexing
│   └── integrations/
│       ├── qdrant_client.py      # UPDATE - Add upsert/delete methods
│       └── litellm_client.py     # NEW - Embedding client
└── tests/
    ├── unit/
    │   ├── test_chunking.py      # NEW
    │   ├── test_embedding.py     # NEW
    │   └── test_indexing.py      # NEW
    └── integration/
        └── test_chunking_embedding.py  # NEW
```

**Files to Modify:**

```
backend/
├── app/
│   ├── workers/
│   │   └── document_tasks.py     # ADD chunking/embedding/indexing steps
│   ├── integrations/
│   │   └── qdrant_client.py      # ADD upsert_points, delete_points methods
│   └── core/
│       └── config.py             # ADD embedding/chunking settings
├── pyproject.toml                # ADD langchain, tiktoken, litellm, qdrant-client
└── .env.example                  # ADD LITELLM_PROXY_URL, EMBEDDING_MODEL
```

### Testing Requirements

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| `pytestmark` on all test files | testing-backend-specification.md | CI gate |
| Mock LiteLLM in unit tests | testing-backend-specification.md | Unit isolation |
| Real Qdrant in integration tests | testing-backend-specification.md | Testcontainers |
| Deterministic embeddings for tests | testing-backend-specification.md | Mock responses |
| Unit tests < 5s | testing-backend-specification.md | `pytest-timeout` |
| Integration tests < 30s | testing-backend-specification.md | `pytest-timeout` |

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Processing-Pipeline-Detail] - Full pipeline specification
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Qdrant-Collection-Schema] - Vector payload schema
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Failure-Handling-Strategy] - Retry configuration
- [Source: docs/architecture.md#Decision-Summary] - LiteLLM + Qdrant decisions
- [Source: docs/epics.md#Story-2.6] - Original story definition and ACs
- [Source: docs/testing-backend-specification.md] - Testing patterns for backend
- [Source: docs/coding-standards.md] - Python coding standards

## Dev Agent Record

### Completion Notes
**Completed:** 2025-11-24
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

### Context Reference

- [2-6-document-processing-worker-chunking-and-embedding.context.xml](docs/sprint-artifacts/2-6-document-processing-worker-chunking-and-embedding.context.xml)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- Implementation order: dependencies → config → litellm client → qdrant client → chunking → embedding → indexing → document_tasks

### Completion Notes List

- ✅ Implemented chunking module with RecursiveCharacterTextSplitter, tiktoken tokenizer, metadata preservation
- ✅ Implemented embedding module with LiteLLM client, batching, exponential backoff, token limit handling
- ✅ Implemented indexing module with deterministic point IDs, upsert, orphan cleanup
- ✅ Updated document_tasks.py to run full pipeline: chunk → embed → index → READY status
- ✅ Added Qdrant client methods: upsert_points, delete_points_by_filter, get_collection_info, health_check
- ✅ Created LiteLLM embedding client with retry logic and cost tracking
- ✅ Added config settings: embedding_model, embedding_batch_size, chunk_size, chunk_overlap
- ✅ Added dependencies: langchain-text-splitters, tiktoken (litellm, qdrant-client already existed)
- ✅ All 168 unit tests pass, 7 integration tests pass

### File List

**New Files:**
- backend/app/workers/chunking.py
- backend/app/workers/embedding.py
- backend/app/workers/indexing.py
- backend/app/integrations/litellm_client.py
- backend/tests/unit/test_chunking.py
- backend/tests/unit/test_embedding.py
- backend/tests/unit/test_indexing.py
- backend/tests/integration/test_chunking_embedding.py

**Modified Files:**
- backend/app/workers/document_tasks.py
- backend/app/integrations/qdrant_client.py
- backend/app/core/config.py
- backend/pyproject.toml

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-24 | Initial draft created from tech-spec-epic-2.md, architecture.md, epics.md, and story 2-5 learnings | SM Agent (Bob) |
| 2025-11-24 | Implementation complete: chunking, embedding, indexing modules with full test coverage | Dev Agent (Amelia) |
