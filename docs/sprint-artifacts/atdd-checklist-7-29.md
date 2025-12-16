# ATDD Checklist: Story 7-29 - Markdown Content API Endpoint

## Story Overview
**Story ID:** 7-29
**Title:** Markdown Content API Endpoint
**Epic:** 7 - Production Readiness & Configuration
**ATDD Status:** ✅ COMPLETE (tests scaffolded, require Docker for execution)
**Date:** 2025-12-11

## Test Coverage Summary

| Test Type | Count | Status |
|-----------|-------|--------|
| Integration Tests | 10 | ✅ Scaffolded (Docker required) |
| **Total** | **10** | ✅ |

## Acceptance Criteria Traceability

### AC-7.29.1: Endpoint Implementation
**Requirement:** GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content returns markdown

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| MCA-I-01 | Valid document with markdown returns 200 | Integration | P0 | ✅ Scaffolded |
| MCA-I-02 | Response includes document_id, markdown_content, generated_at | Integration | P0 | ✅ Scaffolded |

### AC-7.29.2: 404 for Older Documents
**Requirement:** Documents without markdown return 404 with clear message

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| MCA-I-03 | Document without markdown_content returns 404 | Integration | P0 | ✅ Scaffolded |
| MCA-I-04 | Document without parsed_content returns 404 | Integration | P0 | ✅ Scaffolded |
| MCA-I-05 | Non-existent document returns 404 | Integration | P0 | ✅ Scaffolded |
| MCA-I-06 | Non-existent KB returns 403 | Integration | P1 | ✅ Scaffolded |

### AC-7.29.3: 400 for Processing Documents
**Requirement:** Documents still processing return 400 with status info

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| MCA-I-07 | Document with PENDING status returns 400 | Integration | P0 | ✅ Scaffolded |
| MCA-I-08 | Document with PROCESSING status returns 400 | Integration | P0 | ✅ Scaffolded |

### AC-7.29.4: Response Schema
**Requirement:** Response includes document_id, markdown_content, generated_at

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| MCA-I-02 | Response schema validation | Integration | P0 | ✅ Scaffolded |

### AC-7.29.5: Permission Check
**Requirement:** User must have READ permission on KB

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| MCA-I-09 | User without KB access returns 403 | Integration | P0 | ✅ Scaffolded |
| MCA-I-10 | Unauthenticated request returns 401 | Integration | P0 | ✅ Scaffolded |

### AC-7.29.6: Integration Tests
**Requirement:** Integration tests cover all response codes

| Test ID | Test Description | Type | Priority | Status |
|---------|------------------|------|----------|--------|
| - | TestGetMarkdownContentSuccess (2 tests) | Integration | P0 | ✅ Scaffolded |
| - | TestGetMarkdownContentNotFound (4 tests) | Integration | P0 | ✅ Scaffolded |
| - | TestGetMarkdownContentProcessing (2 tests) | Integration | P0 | ✅ Scaffolded |
| - | TestGetMarkdownContentUnauthorized (2 tests) | Integration | P0 | ✅ Scaffolded |

## Test Files

### Integration Tests
1. **Main Test File:** `backend/tests/integration/test_markdown_content_api.py`
   - `TestGetMarkdownContentSuccess` - 2 tests (200 responses)
   - `TestGetMarkdownContentNotFound` - 4 tests (404 responses)
   - `TestGetMarkdownContentProcessing` - 2 tests (400 responses)
   - `TestGetMarkdownContentUnauthorized` - 2 tests (401/403 responses)

## Test Execution Commands

```bash
# Run integration tests (requires Docker)
cd backend && .venv/bin/pytest tests/integration/test_markdown_content_api.py -v

# With Docker Desktop socket
DOCKER_HOST=unix:///home/tungmv/.docker/desktop/docker.sock \
TESTCONTAINERS_RYUK_DISABLED=true \
.venv/bin/pytest tests/integration/test_markdown_content_api.py -v
```

## Test Structure

```python
# tests/integration/test_markdown_content_api.py

class TestGetMarkdownContentSuccess:
    async def test_get_markdown_content_returns_200(...)  # AC-7.29.1
    async def test_get_markdown_content_response_schema(...)  # AC-7.29.4

class TestGetMarkdownContentNotFound:
    async def test_get_markdown_content_no_markdown_returns_404(...)  # AC-7.29.2
    async def test_get_markdown_content_no_parsed_content_returns_404(...)  # AC-7.29.2
    async def test_get_markdown_content_document_not_found_returns_404(...)  # AC-7.29.6
    async def test_get_markdown_content_kb_not_found_returns_403(...)  # AC-7.29.6

class TestGetMarkdownContentProcessing:
    async def test_get_markdown_content_pending_returns_400(...)  # AC-7.29.3
    async def test_get_markdown_content_processing_returns_400(...)  # AC-7.29.3

class TestGetMarkdownContentUnauthorized:
    async def test_get_markdown_content_no_kb_access_returns_403(...)  # AC-7.29.5
    async def test_get_markdown_content_unauthenticated_returns_401(...)  # AC-7.29.5
```

## Senior Developer Review
**Status:** APPROVED (per story documentation)
**Reviewed:** 2025-12-11
**Reviewer Notes:**
- Tests comprehensive for all AC requirements
- Edge cases covered (404, 400, 403, 401)
- Permission checks properly validated

## Priority Legend
- **P0 (Critical):** Core functionality, must pass for story acceptance
- **P1 (High):** Important edge cases and error handling
- **P2 (Medium):** Nice-to-have coverage, edge cases

## Notes
- Integration tests require Docker (testcontainers) for execution
- Tests are scaffolded and verified against acceptance criteria
- All 10 tests cover the 6 acceptance criteria
- Story status: DONE
