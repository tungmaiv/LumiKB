# Story 5.14: Search Audit Logging

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5.14
**Status:** done
**Created:** 2025-12-04
**Story Points:** 2
**Priority:** Medium
**Type:** Feature - Compliance & Audit
**Originally:** Story 3.11 in Epic 3, moved to Epic 5 for thematic fit

---

## Story Statement

**As a** compliance officer,
**I want** all search queries logged to the audit system,
**So that** we can audit information access and demonstrate compliance with data governance policies.

---

## Context

This story implements comprehensive audit logging for all search operations in LumiKB. Search queries represent a key access point for knowledge base content, and logging them is essential for:

1. **Compliance Auditing**: Track who accessed what information and when
2. **Security Monitoring**: Detect unusual search patterns or potential data exfiltration
3. **Analytics**: Understand search usage patterns for system optimization
4. **Accountability**: Provide evidence of information access for regulatory requirements

**Story Relationship:**
- Provides search audit data that Story 5.2 (Audit Log Viewer) displays
- Complements Story 4.10 (Generation Audit Logging) for complete audit coverage
- Together with Stories 5.2 and 5.3, completes the full audit workflow:
  1. Log search queries (5.14) ← **This story**
  2. Log generation requests (4.10) ← **Already implemented**
  3. View all audit logs (5.2) ← **Already implemented**
  4. Export audit logs (5.3) ← **Already implemented**

**Existing Infrastructure:**
- `AuditService` from Story 1.7 provides the audit logging foundation
- `audit_events` table exists with proper schema for event storage
- Fire-and-forget async pattern already established in Generation Audit Logging (Story 4.10)
- Admin audit viewer (Story 5.2) ready to display search events

**Source Documents:**
- [docs/sprint-artifacts/tech-spec-epic-5.md](tech-spec-epic-5.md) - AC-5.14.1 through AC-5.14.5
- [docs/epics.md](../epics.md) - Story 5.14 definition (lines 2361-2408)
- [backend/app/services/audit_service.py](../../backend/app/services/audit_service.py) - Existing AuditService
- [backend/app/services/search_service.py](../../backend/app/services/search_service.py) - Search operations to instrument

---

## Acceptance Criteria

### AC1: All Search API Calls Logged (AC-5.14.1)

**Given** a user performs a search operation via any search endpoint
**When** the search request is processed
**Then**:
- An audit event is created with `event_type="search"`
- Event is logged regardless of search success or failure
- All search endpoints are instrumented:
  - `POST /api/v1/search` (main semantic search)
  - `POST /api/v1/search/cross-kb` (cross-KB search)
  - `GET /api/v1/search/quick` (quick search/command palette)

**Verification:**
```bash
# Perform search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "test query", "kb_id": "uuid"}'

# Verify audit event created
SELECT * FROM audit_events
WHERE event_type = 'search'
ORDER BY created_at DESC LIMIT 1;
```

---

### AC2: Audit Logs Capture Required Fields (AC-5.14.2)

**Given** a search is logged
**When** the audit event is stored
**Then** the event captures:
- `user_id`: UUID of the user who performed the search
- `query_text`: Search query (PII sanitized - see sanitization rules below)
- `kb_id`: Knowledge base ID searched (or array for cross-KB)
- `result_count`: Number of results returned
- `duration_ms`: Search response time in milliseconds
- `search_type`: Type of search performed (semantic, cross_kb, quick)
- `status`: "success" or "failed"

**PII Sanitization Rules:**
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- SSN patterns → `[SSN]`
- Credit card patterns → `[CC]`
- Query preserved for audit purposes but sensitive patterns masked

**Verification:**
```python
# Expected audit event structure
{
    "event_type": "search",
    "user_id": "user-uuid",
    "resource_type": "knowledge_base",
    "resource_id": "kb-uuid",
    "action": "search",
    "metadata": {
        "query_text": "how do I contact [EMAIL]",
        "kb_ids": ["kb-uuid-1", "kb-uuid-2"],
        "result_count": 15,
        "duration_ms": 145,
        "search_type": "semantic",
        "status": "success"
    }
}
```

---

### AC3: Fire-and-Forget Async Logging (AC-5.14.3)

**Given** the search endpoint processes a request
**When** audit logging occurs
**Then**:
- Logging is performed asynchronously (no await blocking the response)
- Search latency is not impacted by audit logging
- Audit write failures do not cause search request failures
- Search response is returned before audit write confirms

**Performance Requirement:**
- Search latency impact: < 5ms (measured as p99 overhead)
- Target: No measurable latency increase from audit logging

**Verification:**
```python
# Measure search latency with and without audit logging
# Should show negligible difference (<5ms p99)
```

---

### AC4: Failed Searches Logged (AC-5.14.4)

**Given** a search request fails
**When** the failure is handled
**Then**:
- Audit event is created with `status="failed"`
- `error_message` field captures the failure reason
- Failure type is categorized:
  - `error_type`: "validation_error", "kb_not_found", "access_denied", "internal_error"
- Failed searches are queryable in audit log viewer

**Verification:**
```bash
# Trigger a failed search (invalid KB)
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "test", "kb_id": "non-existent-uuid"}'

# Verify failed audit event
SELECT * FROM audit_events
WHERE event_type = 'search'
AND metadata->>'status' = 'failed'
ORDER BY created_at DESC LIMIT 1;
```

---

### AC5: Search Logs Queryable in Audit Viewer (AC-5.14.5)

**Given** search audit logs exist
**When** an admin queries them via Story 5.2 audit viewer
**Then**:
- Search events appear in audit log table
- Events can be filtered by `event_type="search"`
- Events can be filtered by user, date range, and KB
- Search-specific metadata is displayed (query, result count, duration)

**Verification:**
```bash
# Query audit logs via API
curl -X POST http://localhost:8000/api/v1/admin/audit/logs \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "event_type": "search",
    "start_date": "2025-12-01",
    "end_date": "2025-12-05"
  }'
```

---

## Technical Design

### Solution Overview

1. **Create `SearchAuditService`** - Dedicated service for search audit logging with PII sanitization
2. **Instrument Search Endpoints** - Add audit logging calls to all search API endpoints
3. **Implement PII Sanitizer** - Regex-based sanitizer for query text
4. **Use Background Task** - FastAPI BackgroundTasks for fire-and-forget logging

### Architecture

```
Search Request Flow:
┌─────────┐    ┌───────────┐    ┌──────────────┐    ┌────────────┐
│  User   │───►│  Search   │───►│   Search     │───►│   Search   │
│         │    │  Endpoint │    │   Service    │    │   Results  │
└─────────┘    └───────────┘    └──────────────┘    └────────────┘
                    │                                      │
                    │ (async, fire-and-forget)            │
                    ▼                                      │
           ┌───────────────┐                              │
           │ SearchAudit   │                              │
           │   Service     │                              │
           └───────────────┘                              │
                    │                                      │
                    ▼                                      │
           ┌───────────────┐    ┌─────────────┐           │
           │ PII Sanitizer │───►│   Audit     │           │
           │               │    │   Service   │           │
           └───────────────┘    └─────────────┘           │
                                      │                   │
                                      ▼                   │
                               ┌──────────────┐           │
                               │ audit_events │◄──────────┘
                               │    table     │  (result_count,
                               └──────────────┘   duration_ms)
```

### Service Implementation

```python
# backend/app/services/search_audit_service.py

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from structlog import get_logger

from app.services.audit_service import AuditService

logger = get_logger(__name__)


class PIISanitizer:
    """Sanitize PII patterns from search queries."""

    PATTERNS = {
        "email": (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
        "phone": (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        "ssn": (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        "credit_card": (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CC]'),
    }

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Sanitize all PII patterns from text."""
        result = text
        for pattern, replacement in cls.PATTERNS.values():
            result = re.sub(pattern, replacement, result)
        return result


class SearchAuditService:
    """Service for logging search operations to audit trail."""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    async def log_search(
        self,
        user_id: UUID,
        query_text: str,
        kb_ids: list[UUID],
        result_count: int,
        duration_ms: int,
        search_type: str,  # "semantic", "cross_kb", "quick"
        status: str = "success",
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Log a search operation to audit trail (fire-and-forget)."""
        try:
            sanitized_query = PIISanitizer.sanitize(query_text)

            metadata = {
                "query_text": sanitized_query,
                "kb_ids": [str(kb_id) for kb_id in kb_ids],
                "result_count": result_count,
                "duration_ms": duration_ms,
                "search_type": search_type,
                "status": status,
            }

            if error_message:
                metadata["error_message"] = error_message
            if error_type:
                metadata["error_type"] = error_type

            await self.audit_service.log_event(
                event_type="search",
                user_id=user_id,
                resource_type="knowledge_base",
                resource_id=str(kb_ids[0]) if kb_ids else None,
                action="search",
                metadata=metadata,
            )

            logger.debug(
                "search_audit_logged",
                user_id=str(user_id),
                search_type=search_type,
                result_count=result_count,
                duration_ms=duration_ms,
            )

        except Exception as e:
            # Fire-and-forget: log error but don't raise
            logger.error(
                "search_audit_failed",
                error=str(e),
                user_id=str(user_id),
            )
```

### Endpoint Integration

```python
# In backend/app/api/v1/search.py - Add audit logging

from time import time
from fastapi import BackgroundTasks

from app.services.search_audit_service import SearchAuditService


@router.post("/search")
async def semantic_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
    search_audit_service: SearchAuditService = Depends(get_search_audit_service),
):
    start_time = time()

    try:
        results = await search_service.semantic_search(
            query=request.query,
            kb_id=request.kb_id,
            user=current_user,
        )

        duration_ms = int((time() - start_time) * 1000)

        # Fire-and-forget audit logging
        background_tasks.add_task(
            search_audit_service.log_search,
            user_id=current_user.id,
            query_text=request.query,
            kb_ids=[request.kb_id],
            result_count=len(results.results),
            duration_ms=duration_ms,
            search_type="semantic",
            status="success",
        )

        return results

    except KBNotFoundError as e:
        duration_ms = int((time() - start_time) * 1000)
        background_tasks.add_task(
            search_audit_service.log_search,
            user_id=current_user.id,
            query_text=request.query,
            kb_ids=[request.kb_id],
            result_count=0,
            duration_ms=duration_ms,
            search_type="semantic",
            status="failed",
            error_message=str(e),
            error_type="kb_not_found",
        )
        raise
```

### Dependencies

```python
# backend/app/api/dependencies.py - Add search audit dependency

from app.services.search_audit_service import SearchAuditService
from app.services.audit_service import AuditService


async def get_search_audit_service(
    audit_service: AuditService = Depends(get_audit_service),
) -> SearchAuditService:
    return SearchAuditService(audit_service)
```

---

## Tasks / Subtasks

### Task 1: Create SearchAuditService with PII Sanitizer (AC: #2, #3)

- [x] Create `backend/app/services/search_audit_service.py`
- [x] Implement `PIISanitizer` class with regex patterns for email, phone, SSN, CC
- [x] Implement `SearchAuditService` with `log_search()` method
- [x] Add fire-and-forget error handling (log errors, don't raise)
- [x] Add structlog logging for audit events
- [x] **Estimated Time:** 30 minutes

### Task 2: Add SearchAuditService Dependency (AC: #1)

- [x] Add `get_search_audit_service` function to `backend/app/api/dependencies.py`
- [x] Ensure dependency injection works with existing AuditService
- [x] **Estimated Time:** 10 minutes

### Task 3: Instrument Semantic Search Endpoint (AC: #1, #4)

- [x] Add audit logging to `POST /api/v1/search` endpoint
- [x] Capture timing with `time.time()` for duration_ms
- [x] Add BackgroundTasks for fire-and-forget execution
- [x] Handle both success and failure cases
- [x] **Estimated Time:** 20 minutes

### Task 4: Instrument Cross-KB Search Endpoint (AC: #1, #4)

- [x] Add audit logging to `POST /api/v1/search/cross-kb` endpoint
- [x] Log multiple KB IDs in metadata
- [x] Handle success and failure cases
- [x] **Estimated Time:** 15 minutes

### Task 5: Instrument Quick Search Endpoint (AC: #1, #4)

- [x] Add audit logging to `GET /api/v1/search/quick` endpoint
- [x] Capture query from query params
- [x] Handle success and failure cases
- [x] **Estimated Time:** 15 minutes

### Task 6: Write Unit Tests for SearchAuditService (AC: #2, #3)

- [x] Create `backend/tests/unit/test_search_audit_service.py`
- [x] Test PII sanitization patterns (email, phone, SSN, CC)
- [x] Test log_search() with success status
- [x] Test log_search() with failure status
- [x] Test fire-and-forget error handling
- [x] **Estimated Time:** 30 minutes

### Task 7: Write Unit Tests for PII Sanitizer (AC: #2)

- [x] Test email sanitization
- [x] Test phone number sanitization (various formats)
- [x] Test SSN sanitization
- [x] Test credit card sanitization
- [x] Test multiple patterns in single query
- [x] **Estimated Time:** 20 minutes

### Task 8: Write Integration Tests for Search Audit Logging (AC: #1, #4, #5)

- [x] Create `backend/tests/integration/test_search_audit_api.py`
- [x] Test successful search creates audit event
- [x] Test failed search creates audit event with error details
- [x] Test audit events queryable via admin API
- [x] Test latency impact is minimal
- [x] **Estimated Time:** 40 minutes

### Task 9: Verify Audit Viewer Integration (AC: #5)

- [x] Verify search events appear in audit log viewer
- [x] Verify filtering by event_type="search" works
- [x] Verify search-specific metadata displayed
- [x] **Estimated Time:** 15 minutes

### Task 10: Update Documentation

- [x] Add search audit logging to API documentation
- [x] Document PII sanitization patterns
- [x] **Estimated Time:** 10 minutes

---

## Dev Notes

### Files to Create

- `backend/app/services/search_audit_service.py` - New audit service for search
- `backend/tests/unit/test_search_audit_service.py` - Unit tests
- `backend/tests/unit/test_pii_sanitizer.py` - PII sanitizer tests
- `backend/tests/integration/test_search_audit_logging.py` - Integration tests

### Files to Modify

- `backend/app/api/dependencies.py` - Add search audit service dependency
- `backend/app/api/v1/search.py` - Add audit logging to endpoints (if separate file)
- `backend/app/api/v1/knowledge_bases.py` - Add audit logging to search endpoints (if in KB routes)

### Existing Patterns to Follow

**From Story 4.10 (Generation Audit Logging):**
```python
# Pattern for fire-and-forget audit logging
background_tasks.add_task(
    audit_service.log_event,
    event_type="generation",
    user_id=current_user.id,
    ...
)
```

**From AuditService (Story 1.7):**
```python
# Existing audit event structure
await audit_service.log_event(
    event_type="...",
    user_id=UUID,
    resource_type="...",
    resource_id="...",
    action="...",
    metadata={...},
)
```

### Testing Commands

```bash
# Run unit tests
cd /home/tungmv/Projects/LumiKB/backend
.venv/bin/pytest tests/unit/test_search_audit_service.py -v

# Run integration tests
.venv/bin/pytest tests/integration/test_search_audit_logging.py -v

# Run all audit-related tests
.venv/bin/pytest tests/ -k "audit" -v

# Check test coverage
.venv/bin/pytest tests/unit/test_search_audit_service.py --cov=app/services/search_audit_service --cov-report=term-missing
```

### Considerations

1. **Performance Impact**: Fire-and-forget pattern ensures no latency impact on search responses. Background tasks are executed after response is sent.

2. **Error Handling**: Audit logging failures should never cause search failures. All exceptions are caught and logged.

3. **PII Sanitization**: Query text is sanitized before storage to protect sensitive information while maintaining audit value. Patterns are conservative to avoid false positives.

4. **Idempotency**: Each search creates exactly one audit event. No deduplication needed.

5. **Volume Considerations**: High-volume search environments may generate many audit events. Consider:
   - Table partitioning by date (future)
   - Archival policy (future)
   - For MVP: Standard PostgreSQL performance is sufficient

### Coding Standards

Follow project coding standards from [docs/coding-standards.md](../coding-standards.md):
- **KISS/DRY/YAGNI**: Keep SearchAuditService simple, reuse existing AuditService patterns
- **Python Standards**: Use type hints, structlog for logging, Pydantic for schemas
- **Testing Standards**: Unit tests ≥90% coverage, integration tests for all ACs
- **No Dead Code**: Delete unused code, don't comment out

### Learnings from Previous Stories

**From Story 4.10 (Generation Audit Logging):**
- Fire-and-forget pattern using FastAPI BackgroundTasks works well
- Structured metadata allows flexible querying
- Error handling is critical - never let audit fail the main operation

**From Story 5.13 (Celery Beat Fix):**
- Infrastructure changes require careful testing
- Manual verification for Docker-related changes

**From Story 5.2/5.3 (Audit Viewer/Export):**
- Audit events are queryable via `POST /api/v1/admin/audit/logs`
- Events must follow existing schema for viewer compatibility
- PII redaction already handled in viewer (AC-5.2.3)

---

## Definition of Done

- [x] **Search Audit Service (AC1, AC2, AC3):**
  - [x] `SearchAuditService` created with `log_search()` method
  - [x] `PIISanitizer` implemented with email, phone, SSN, CC patterns
  - [x] Fire-and-forget pattern implemented (no await blocking)
  - [x] All search endpoints instrumented

- [x] **Field Capture (AC2):**
  - [x] user_id captured
  - [x] query_text captured (PII sanitized)
  - [x] kb_id(s) captured
  - [x] result_count captured
  - [x] duration_ms captured
  - [x] search_type captured
  - [x] status captured

- [x] **Failure Handling (AC4):**
  - [x] Failed searches logged with status="failed"
  - [x] error_message captured
  - [x] error_type categorized

- [x] **Integration (AC5):**
  - [x] Search events appear in audit viewer
  - [x] Events filterable by event_type="search"
  - [x] Events filterable by user, date, KB

- [x] **Performance:**
  - [x] Search latency impact < 5ms (p99)
  - [x] Audit failures don't cause search failures

- [x] **Testing:**
  - [x] Unit tests for SearchAuditService (≥90% coverage)
  - [x] Unit tests for PIISanitizer (all patterns tested)
  - [x] Integration tests for audit logging
  - [x] All tests pass in CI/CD

- [x] **Code Quality:**
  - [x] ruff check passes (no linting errors)
  - [x] ruff format applied
  - [x] Type hints complete
  - [x] Structlog logging added

---

## FR Traceability

**Functional Requirements Addressed:**

| FR | Requirement | How Satisfied |
|----|-------------|---------------|
| FR48 | Audit logs with filters | Search events logged with filterable metadata |
| FR53 | System logs all queries | All search API calls create audit events |
| FR54 | Query logs include details | user_id, query, kb_id, result_count, duration captured |

**Non-Functional Requirements:**

- **Performance**: Fire-and-forget pattern ensures < 5ms latency impact
- **Security**: PII sanitization protects sensitive query content
- **Compliance**: Complete audit trail for search operations
- **Reliability**: Audit failures don't impact search availability

---

## Story Size Estimate

**Story Points:** 2

**Rationale:**
- Moderate scope: New service + endpoint instrumentation
- Low complexity: Follows established patterns from Story 4.10
- Low risk: Non-breaking change, additive functionality
- Good test coverage required

**Estimated Effort:** 3-4 hours

**Breakdown:**
- Task 1: SearchAuditService (30m)
- Task 2: Dependency injection (10m)
- Task 3-5: Endpoint instrumentation (50m)
- Task 6-8: Testing (90m)
- Task 9: Verification (15m)
- Task 10: Documentation (10m)

---

## Dev Agent Record

### Context Reference
- [docs/sprint-artifacts/5-14-search-audit-logging.context.xml](5-14-search-audit-logging.context.xml)

---

## Change Log

| Date | Author | Change | Reason |
|------|--------|--------|--------|
| 2025-12-04 | SM Agent (Bob) | Story created | Initial draft from tech-spec-epic-5.md |
| 2025-12-04 | SM Agent (Bob) | Added coding-standards.md citation | Validation fix - Major issue resolved |
| 2025-12-04 | SM Agent (Bob) | Status: draft → ready-for-dev | Story context generated, ready for implementation |
| 2025-12-04 | Dev Agent (Amelia) | Status: ready-for-dev → done | Implementation complete with 35 tests passing |

---

**Story Created By:** SM Agent (Bob)

---

## References

- [docs/sprint-artifacts/tech-spec-epic-5.md](tech-spec-epic-5.md) - AC-5.14.1 through AC-5.14.5
- [docs/epics.md](../epics.md) - Story 5.14 definition (lines 2361-2408)
- [docs/coding-standards.md](../coding-standards.md) - Project coding conventions (KISS/DRY/YAGNI, Python standards, testing standards)
- [backend/app/services/audit_service.py](../../backend/app/services/audit_service.py) - Existing AuditService
- [backend/app/services/search_service.py](../../backend/app/services/search_service.py) - Search operations
- [docs/sprint-artifacts/5-13-celery-beat-filesystem-fix.md](5-13-celery-beat-filesystem-fix.md) - Previous story learnings
- [backend/tests/unit/test_audit_logging.py](../../backend/tests/unit/test_audit_logging.py) - Existing audit tests pattern
