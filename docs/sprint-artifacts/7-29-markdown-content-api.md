# Story 7-29: Markdown Content API Endpoint (Backend)

**Epic:** 7 - Infrastructure & DevOps
**Story Points:** 2
**Status:** done
**Created:** 2025-12-11

---

## User Story

**As a** frontend developer,
**I want** an API endpoint to retrieve the markdown content of a document,
**So that** I can render it in the chunk viewer with precise highlighting.

---

## Background

Story 7-28 implements markdown generation during document parsing. This story exposes that markdown content via a REST API endpoint for the frontend to consume.

The endpoint enables the chunk viewer to display document content in a format that supports accurate character-based highlighting using `char_start` and `char_end` positions.

---

## Acceptance Criteria

### AC-7.29.1: Endpoint Implemented
**Given** a document has `markdown_content` in parsed.json
**When** I call `GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content`
**Then** I receive 200 with JSON body containing `markdown_content` and `generated_at`

**Implementation Notes:**
- Add new route to `backend/app/api/v1/documents.py`
- Reuse existing document/KB access patterns

### AC-7.29.2: 404 for Older Documents
**Given** a document was processed before markdown generation was added
**When** I call the endpoint
**Then** I receive 404 with message "Markdown content not available for this document"

**Implementation Notes:**
- Check if `markdown_content` field exists and is non-null in parsed.json
- Return 404 with clear error message

### AC-7.29.3: 400 for Processing Documents
**Given** a document has status PROCESSING or PENDING
**When** I call the endpoint
**Then** I receive 400 with message "Document is still processing"

**Implementation Notes:**
- Check document status before attempting to read parsed content
- Return appropriate error for in-progress documents

### AC-7.29.4: Response Schema
**Given** markdown content is available
**Then** response includes:
- `markdown_content: string` (the full markdown text)
- `generated_at: datetime` (when markdown was generated)
- `document_id: UUID`

**Implementation Notes:**
```python
class MarkdownContentResponse(BaseModel):
    """Response for markdown content endpoint."""
    document_id: UUID
    markdown_content: str
    generated_at: datetime
```

### AC-7.29.5: Permission Check
**Given** user does not have read access to the KB
**When** they call the endpoint
**Then** they receive 403 Forbidden

**Implementation Notes:**
- Reuse existing `get_kb_with_read_access` dependency
- Same permission model as other document endpoints

### AC-7.29.6: Integration Tests
**Given** integration tests for the endpoint exist
**Then** all success and error scenarios are covered:
- 200 with valid markdown content
- 404 for document without markdown
- 400 for processing document
- 403 for unauthorized access
- 404 for non-existent document/KB

---

## Technical Design

### New Pydantic Schema

| File | Addition |
|------|----------|
| `backend/app/schemas/document.py` | `MarkdownContentResponse` schema |

```python
# backend/app/schemas/document.py

class MarkdownContentResponse(BaseModel):
    """Response schema for document markdown content endpoint.

    Story 7-29: Returns generated markdown for chunk viewer highlighting.
    """
    document_id: UUID
    markdown_content: str = Field(..., description="Full document content in Markdown format")
    generated_at: datetime = Field(..., description="When markdown was generated during parsing")
```

### API Endpoint

| Method | Path | Handler |
|--------|------|---------|
| GET | `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content` | `get_markdown_content` |

```python
# backend/app/api/v1/documents.py

@router.get(
    "/{doc_id}/markdown-content",
    response_model=MarkdownContentResponse,
    responses={
        400: {"description": "Document is still processing"},
        403: {"description": "Forbidden - no read access"},
        404: {"description": "Document or markdown not found"},
    },
)
async def get_markdown_content(
    kb_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
    minio: MinioClient = Depends(get_minio_client),
) -> MarkdownContentResponse:
    """Get markdown content for a document.

    Used by chunk viewer for precise highlighting.
    """
    # 1. Verify KB access
    kb = await get_kb_with_read_access(kb_id, current_user, db)

    # 2. Get document
    document = await get_document_or_404(db, kb_id, doc_id)

    # 3. Check status
    if document.status in (DocumentStatus.PENDING, DocumentStatus.PROCESSING):
        raise HTTPException(
            status_code=400,
            detail="Document is still processing"
        )

    # 4. Read parsed content from MinIO
    parsed_content = await read_parsed_json(minio, doc_id)

    # 5. Check markdown availability
    if not parsed_content or not parsed_content.get("markdown_content"):
        raise HTTPException(
            status_code=404,
            detail="Markdown content not available for this document"
        )

    return MarkdownContentResponse(
        document_id=doc_id,
        markdown_content=parsed_content["markdown_content"],
        generated_at=parsed_content.get("parsed_at", document.processing_completed_at),
    )
```

### Files to Modify

| File | Changes |
|------|---------|
| `backend/app/schemas/document.py` | Add `MarkdownContentResponse` schema |
| `backend/app/api/v1/documents.py` | Add `get_markdown_content` endpoint |
| `backend/tests/integration/test_markdown_content_api.py` | New test file for endpoint |

### MinIO Storage Access

The endpoint reads from existing `.parsed.json` files that Story 7-28 extends:

```python
async def read_parsed_json(minio: MinioClient, doc_id: UUID) -> dict | None:
    """Read parsed.json from MinIO for a document."""
    try:
        bucket = "lumikb-documents"
        object_name = f"{doc_id}.parsed.json"
        data = await minio.get_object(bucket, object_name)
        return json.loads(data)
    except Exception:
        return None
```

---

## Dependencies

### Prerequisites
- Story 7-28 (Markdown Generation from DOCX/PDF)

### Blocked By
- Story 7-28 must be completed for markdown content to exist

### Blocks
- Story 7-30 (Enhanced Markdown Viewer with Highlighting)

---

## Test Plan

### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_markdown_content_response_schema` | Schema validation | All fields properly typed |
| `test_markdown_content_response_serialization` | JSON serialization | datetime serialized correctly |

### Integration Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_get_markdown_content_success` | Valid document with markdown | 200 with markdown_content |
| `test_get_markdown_content_no_markdown` | Document without markdown | 404 with clear message |
| `test_get_markdown_content_processing` | Document still processing | 400 with "still processing" |
| `test_get_markdown_content_no_access` | User lacks KB access | 403 Forbidden |
| `test_get_markdown_content_not_found` | Document doesn't exist | 404 Not Found |
| `test_get_markdown_content_kb_not_found` | KB doesn't exist | 404 Not Found |

---

## Definition of Done

- [x] `MarkdownContentResponse` schema added to schemas/document.py
- [x] GET endpoint implemented at `/documents/{doc_id}/markdown-content`
- [x] 200 response with markdown content and metadata
- [x] 404 response for documents without markdown
- [x] 400 response for processing documents
- [x] 403 response for unauthorized access
- [x] Integration tests pass for all scenarios (10/10 passing)
- [x] Code review approved
- [x] Ruff lint/format passes

---

## Senior Developer Review (AI)

**Review Date:** 2025-12-11
**Reviewer:** Senior Developer AI (Code Review Agent)
**Outcome:** ✅ APPROVE

### Acceptance Criteria Validation

| AC | Title | Verdict | Evidence |
|----|-------|---------|----------|
| AC-7.29.1 | Endpoint Implemented | ✅ PASS | documents.py:1646-1654 - GET endpoint returns 200 with MarkdownContentResponse |
| AC-7.29.2 | 404 for Older Documents | ✅ PASS | documents.py:1718-1723 - Returns 404 when markdown_content missing |
| AC-7.29.3 | 400 for Processing Documents | ✅ PASS | documents.py:1708-1713 - Status check for PENDING/PROCESSING |
| AC-7.29.4 | Response Schema | ✅ PASS | document.py:559-573 - MarkdownContentResponse with all required fields |
| AC-7.29.5 | Permission Check | ✅ PASS | documents.py:1676-1685 - KBService.check_permission() with READ level |
| AC-7.29.6 | Integration Tests | ✅ PASS | test_markdown_content_api.py - 10/10 tests passing |

### Code Quality Summary

**Strengths:**
- Clean architecture following existing patterns
- Inline AC documentation in code comments
- Proper error handling with logging
- Full type annotations
- Comprehensive test coverage (10 tests)

**Minor Observations (non-blocking):**
- Import statement inside function (lines 1730-1733) could be at module level
- Consider caching headers as future enhancement

### Security Review: ✅ PASS
- Authentication via `current_active_user`
- Authorization via `KBService.check_permission()`
- Parameterized queries via SQLAlchemy ORM
- No information leakage in error messages

---

## Story Context References

- [Sprint Change Proposal](sprint-change-proposal-markdown-first-processing.md) - Feature rationale
- [Story 7-28](7-28-markdown-generation-backend.md) - Prerequisite: markdown generation
- [Epic 7: Infrastructure](../epics/epic-7-infrastructure.md) - Story 7.29
- [documents.py](../../backend/app/api/v1/documents.py) - Endpoint location

---

## Notes

- This story focuses only on the API endpoint
- Frontend consumption is in Story 7-30
- Endpoint is cache-friendly (markdown is immutable once generated)
- Consider adding ETag/Last-Modified headers for caching (optional enhancement)
- Keep response lightweight - only markdown content and metadata
