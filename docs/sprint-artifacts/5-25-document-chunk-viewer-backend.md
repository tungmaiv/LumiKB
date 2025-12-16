# Story 5-25: Document Chunk Viewer - Backend API

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-25
**Status:** done
**Created:** 2025-12-07
**Author:** Bob (Scrum Master)

---

## Story

**As a** user or admin,
**I want** API endpoints to retrieve document chunks and stream original document content,
**So that** the frontend can display a split-pane viewer for citation verification.

---

## Context & Rationale

### Why This Story Matters

Users need to verify that AI-generated citations actually come from source documents. Admins need to inspect document processing quality. This story provides the backend API foundation for the Document Chunk Viewer feature.

**Key Discovery:** The existing architecture already stores:
- Original files in MinIO (PDF, DOCX, MD, TXT preserved)
- Chunk metadata in Qdrant with `char_start`, `char_end`, `page_number`
- Full `chunk_text` in vector payloads

This means minimal backend changes are needed - primarily new endpoints to expose existing data.

### Relationship to Other Stories

**Depends On:**
- **Epic 2**: Document upload and processing pipeline (existing)
- **Story 2.4**: MinIO document storage (existing)

**Enables:**
- **Story 5-26**: Frontend Document Chunk Viewer UI

**Architectural Fit:**
- Extends existing document service
- Queries existing Qdrant collections
- Streams files from existing MinIO storage
- No new infrastructure required

---

## Acceptance Criteria

### AC-5.25.1: Chunk retrieval endpoint returns chunks with metadata

**Given** a document has been processed and indexed
**When** I call `GET /api/v1/documents/{id}/chunks`
**Then** I receive a JSON response containing:
- `chunks`: Array of chunk objects
- `total`: Total number of chunks
- `document_id`: The document UUID

**And** each chunk object contains:
- `chunk_index`: Position in sequence (0-indexed)
- `chunk_text`: Full text content
- `char_start`: Starting character offset in source
- `char_end`: Ending character offset in source
- `page_number`: Page number (PDF only, null for others)
- `paragraph_index`: Paragraph index (DOCX/MD)

**Validation:**
- Integration test: Upload document → process → GET chunks → verify metadata
- Unit test: ChunkService.get_document_chunks() returns correct structure

---

### AC-5.25.2: Chunk search filters by text content

**Given** a document has multiple chunks
**When** I call `GET /api/v1/documents/{id}/chunks?search=authentication`
**Then** only chunks containing "authentication" (case-insensitive) are returned
**And** the `total` reflects the filtered count

**Validation:**
- Integration test: Search chunks → verify only matching chunks returned
- Unit test: ChunkService filters correctly

---

### AC-5.25.3: Chunk pagination supports large documents

**Given** a document has 500+ chunks
**When** I call `GET /api/v1/documents/{id}/chunks?skip=0&limit=50`
**Then** I receive exactly 50 chunks (or fewer if near end)
**And** `total` shows the full count
**And** I can paginate through all chunks

**Validation:**
- Integration test: Verify pagination with skip/limit
- Unit test: Pagination logic correct

---

### AC-5.25.4: Document content endpoint streams original file

**Given** a document exists in MinIO
**When** I call `GET /api/v1/documents/{id}/content`
**Then** the original file is streamed with correct headers:
- `Content-Type`: Matches original MIME type
- `Content-Disposition`: `inline; filename="original_name.pdf"`
- `Content-Length`: File size in bytes

**Validation:**
- Integration test: Download PDF, DOCX, MD, TXT → verify binary integrity
- Unit test: Headers set correctly

---

### AC-5.25.5: DOCX content can be converted to HTML (optional)

**Given** a DOCX document exists
**When** I call `GET /api/v1/documents/{id}/content?format=html`
**Then** the DOCX is converted to semantic HTML using mammoth
**And** the response `Content-Type` is `text/html`
**And** the HTML preserves paragraph structure for highlighting

**Note:** This is optional - frontend may use client-side docx-preview instead.

**Validation:**
- Integration test: Request DOCX as HTML → verify valid HTML structure

---

### AC-5.25.6: Endpoints enforce document access permissions

**Given** I do not have READ access to a KB
**When** I call chunk or content endpoints for a document in that KB
**Then** I receive 403 Forbidden

**Given** the document does not exist
**When** I call chunk or content endpoints
**Then** I receive 404 Not Found

**Validation:**
- Integration test: Verify permission enforcement
- Integration test: Verify 404 for missing documents

---

## Dev Notes

### Learnings from Previous Story

**From Story 5-24 (KB Dashboard Filtering):** [Source: docs/sprint-artifacts/5-24-kb-dashboard-filtering.md]
- Pagination pattern established: `page`, `limit` query params with `PaginatedResponse` schema
- Filter params use `Query()` with descriptions for OpenAPI docs
- Count query pattern: `select(func.count()).select_from(query.subquery())`
- URL param sync pattern for frontend hooks

**Applicable to This Story:**
- Reuse pagination pattern for chunk endpoint (`skip`, `limit` params)
- Follow same `Query()` annotation style for OpenAPI documentation
- ChunkService can follow DocumentService patterns for query building

### Architecture Patterns and Constraints

- **Service Layer**: Create ChunkService following existing service patterns (DocumentService, KBService)
- **Qdrant Integration**: Use existing `qdrant_client` for scroll queries with filters
- **MinIO Streaming**: Leverage existing `download_file_stream()` method
- **Permission Model**: Inherit KB READ permission checks from document endpoints

[Source: docs/architecture.md - Service Layer Architecture]
[Source: docs/sprint-artifacts/tech-spec-epic-5.md - Stories 5.25-5.26 Technical Notes]

### Project Structure Notes

New files to create:
```
backend/app/schemas/chunk.py           # DocumentChunk, DocumentChunksResponse
backend/app/services/chunk_service.py  # ChunkService class
backend/tests/unit/test_chunk_service.py
backend/tests/integration/test_chunk_api.py
```

Existing files to modify:
```
backend/app/api/v1/documents.py        # Add /chunks and /content endpoints
backend/app/services/document_service.py  # Add convert_docx_to_html method
backend/pyproject.toml                 # Add mammoth dependency (v0.3.18)
```

### References

- [Tech Spec Epic 5 - Story 5.25](./tech-spec-epic-5.md) - AC definitions, test strategy
- [Architecture](../architecture.md) - Service layer patterns, API conventions
- [Story 5-24](./5-24-kb-dashboard-filtering.md) - Pagination and filtering patterns

---

## Technical Design

### New API Endpoints

**1. GET /api/v1/documents/{document_id}/chunks**

```python
@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    search: str | None = Query(None, description="Filter chunks by text content"),
    skip: int = Query(0, ge=0, description="Number of chunks to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum chunks to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentChunksResponse:
    """Retrieve chunks for a document with optional search and pagination."""
    # Verify document exists and user has access
    document = await document_service.get_document(document_id, current_user)
    if not document:
        raise HTTPException(404, "Document not found")

    # Query Qdrant for chunks
    chunks, total = await chunk_service.get_document_chunks(
        document_id=document_id,
        search=search,
        skip=skip,
        limit=limit,
    )

    return DocumentChunksResponse(
        document_id=document_id,
        chunks=chunks,
        total=total,
        skip=skip,
        limit=limit,
    )
```

**2. GET /api/v1/documents/{document_id}/content**

```python
@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    format: str | None = Query(None, description="Optional format conversion (html for DOCX)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream original document content from MinIO."""
    # Verify document exists and user has access
    document = await document_service.get_document(document_id, current_user)
    if not document:
        raise HTTPException(404, "Document not found")

    # Handle DOCX → HTML conversion if requested
    if format == "html" and document.mime_type == DOCX_MIME_TYPE:
        html_content = await document_service.convert_docx_to_html(document)
        return Response(
            content=html_content,
            media_type="text/html",
        )

    # Stream original file from MinIO
    file_stream = await minio_client.download_file_stream(document.file_path)

    return StreamingResponse(
        file_stream,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.original_filename}"',
            "Content-Length": str(document.file_size_bytes),
        },
    )
```

### New Schemas

**backend/app/schemas/chunk.py**

```python
from pydantic import BaseModel
from uuid import UUID

class DocumentChunk(BaseModel):
    chunk_index: int
    chunk_text: str
    char_start: int
    char_end: int
    page_number: int | None = None
    paragraph_index: int | None = None

class DocumentChunksResponse(BaseModel):
    document_id: UUID
    chunks: list[DocumentChunk]
    total: int
    skip: int
    limit: int
```

### New Service Methods

**backend/app/services/chunk_service.py**

> **Story 7-17 Enhancement (2025-12-17)**: ChunkService now accepts optional `session` and `redis` parameters
> to enable KB-aware embedding model resolution for chunk search. When a KB has a custom embedding model
> configured, the chunk search query embedding uses that model instead of the system default.

```python
class ChunkService:
    def __init__(
        self,
        kb_id: UUID,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
    ):
        self.kb_id = kb_id
        self.collection_name = f"kb_{kb_id}"
        # KB config resolver for embedding model resolution (Story 7-17)
        self._kb_config_resolver: KBConfigResolver | None = None
        if session and redis:
            self._kb_config_resolver = KBConfigResolver(session, redis)

    async def get_document_chunks(
        self,
        document_id: UUID,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DocumentChunk], int]:
        """Retrieve chunks from Qdrant for a document."""
        # Build filter for document_id
        filter_conditions = [
            FieldCondition(
                key="document_id",
                match=MatchValue(value=str(document_id)),
            )
        ]

        # Get all chunks for this document
        results = self.qdrant.scroll(
            collection_name=self._get_collection_name(document_id),
            scroll_filter=Filter(must=filter_conditions),
            limit=10000,  # Get all for filtering/pagination
            with_payload=True,
        )

        chunks = []
        for point in results[0]:
            payload = point.payload
            chunk = DocumentChunk(
                chunk_index=payload.get("chunk_index", 0),
                chunk_text=payload.get("chunk_text", ""),
                char_start=payload.get("char_start", 0),
                char_end=payload.get("char_end", 0),
                page_number=payload.get("page_number"),
                paragraph_index=payload.get("paragraph_index"),
            )

            # Apply search filter if provided
            if search:
                if search.lower() not in chunk.chunk_text.lower():
                    continue

            chunks.append(chunk)

        # Sort by chunk_index
        chunks.sort(key=lambda c: c.chunk_index)

        total = len(chunks)

        # Apply pagination
        paginated_chunks = chunks[skip : skip + limit]

        return paginated_chunks, total
```

### DOCX to HTML Conversion (Optional)

```python
# backend/app/services/document_service.py

import mammoth

async def convert_docx_to_html(self, document: Document) -> str:
    """Convert DOCX to semantic HTML for viewing."""
    # Download from MinIO
    file_bytes = await self.minio_client.download_file(document.file_path)

    # Convert using mammoth
    result = mammoth.convert_to_html(BytesIO(file_bytes))

    return result.value
```

**Note:** mammoth is a Python package that needs to be added to dependencies.

---

## Tasks

### Backend Tasks

- [ ] **Task 1: Create chunk schema** (AC: 5.25.1)
  - Add `DocumentChunk` and `DocumentChunksResponse` schemas
  - Write 1 unit test for schema validation

- [ ] **Task 2: Implement ChunkService** (AC: 5.25.1, 5.25.2, 5.25.3)
  - Query Qdrant for document chunks (AC: 5.25.1)
  - Implement search filtering (AC: 5.25.2)
  - Implement pagination (AC: 5.25.3)
  - Write 4 unit tests

- [ ] **Task 3: Add GET /documents/{id}/chunks endpoint** (AC: 5.25.1, 5.25.2, 5.25.3, 5.25.6)
  - Wire up ChunkService
  - Permission checks (AC: 5.25.6)
  - Write 3 integration tests

- [ ] **Task 4: Add GET /documents/{id}/content endpoint** (AC: 5.25.4, 5.25.6)
  - Stream file from MinIO (AC: 5.25.4)
  - Set correct headers (AC: 5.25.4)
  - Write 3 integration tests

- [ ] **Task 5: Add DOCX → HTML conversion (optional)** (AC: 5.25.5)
  - Add mammoth dependency (v0.3.18)
  - Implement conversion method
  - Write 1 integration test

- [ ] **Task 6: Permission and error handling tests** (AC: 5.25.6)
  - Test 403 for unauthorized access
  - Test 404 for missing documents
  - Write 2 integration tests

---

## Definition of Done

- [ ] All 6 acceptance criteria validated
- [ ] Backend: 14 tests passing (5 unit, 9 integration)
- [ ] No linting errors (Ruff)
- [ ] Type safety enforced (mypy)
- [ ] API documentation updated (OpenAPI auto-generated)
- [ ] Code reviewed

---

## Dependencies

- **Blocked By:** None (builds on existing infrastructure)
- **Blocks:** Story 5-26 (Frontend UI)

---

## Story Points

**Estimate:** 3 story points (1 day)

---

## Notes

- Existing Qdrant payloads already contain `char_start`, `char_end`, `page_number`
- MinIO download_file_stream method already exists
- DOCX conversion is optional - frontend may use client-side `docx-preview` instead
- Search is client-side filtering after Qdrant scroll (acceptable for <10K chunks per doc)

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-07 | Bob (SM) | Initial story created from Party Mode discussion |
| 2025-12-07 | Bob (SM) | Added Dev Notes with Learnings, Architecture, References sections |
| 2025-12-07 | Bob (SM) | Added Project Structure Notes; Added AC references to all tasks; Specified mammoth version (v0.3.18) |
| 2025-12-17 | Dev Agent | Story 7-17 Enhancement: ChunkService now uses KB's configured embedding model for chunk search via KBConfigResolver (AC-5.25.3 extended). Fixed qdrant-client 1.16+ API compatibility (search → query_points). |
