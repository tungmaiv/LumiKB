# Epic 7 Technical Debt - Consolidated Tracker

**Epic:** Epic 7 - Infrastructure, DevOps & KB Configuration
**Created:** 2025-12-10
**Last Updated:** 2025-12-10
**Status:** Active - Consolidated from Epics 4, 5, 6, 7

---

## Purpose

This is the **consolidated technical debt tracker** for the LumiKB project. All tech debt from previous epics has been migrated here for single-source-of-truth tracking.

**Migration Summary:**
- Epic 4 tech debt: Migrated 2025-12-10
- Epic 5 tech debt: Migrated 2025-12-10
- Individual tech debt files: Consolidated 2025-12-10
- **Review & Cleanup:** 2025-12-10 (deduplicated, verified status, added missing items)

---

## Tech Debt Summary

| Priority | Count | Total Effort |
|----------|-------|--------------|
| HIGH | 1 | ~4-6h |
| MEDIUM | 9 | ~40-56h |
| LOW | 6 | ~26-38h |
| **TOTAL** | **16** | **~70-100h** |

---

## HIGH Priority Items

### TD-7.17-1: Document Worker KB Chunking Config Integration

**Source:** Story 7-17 (Service Integration) - AC-7.17.4
**Priority:** HIGH
**Effort:** 4-6 hours
**Status:** Open - Next Sprint
**Added:** 2025-12-10

**Description:**
Document worker does not use KB-level chunking configuration from `KBConfigResolver`. Workers still use global/default chunking settings instead of respecting per-KB configuration.

**Current State:**
- ✅ `KBConfigResolver` implemented (3-layer: Request → KB → System)
- ✅ SearchService uses KB retrieval config (AC-7.17.1)
- ✅ GenerationService uses KB generation config (AC-7.17.2, 7.17.3)
- ✅ Request overrides work (AC-7.17.5)
- ✅ Audit logging includes effective_config (AC-7.17.6)
- ❌ Task 3 (document worker integration) NOT implemented
- ❌ `document_tasks.py` uses hardcoded chunking values

**Impact:**
KB-level chunking settings (chunk_size, chunk_overlap, strategy) are ignored during document processing. All documents processed with system defaults regardless of KB configuration.

**Required Work:**
1. Inject `KBConfigResolver` into `document_tasks.py`
2. Fetch KB config before chunking: `config = resolver.resolve(kb_id)`
3. Pass `config.chunking` to parsing/chunking workers
4. Modify `parsing.py` to accept chunking config parameters
5. Update `embedding.py` if chunking affects embedding batch size
6. Add unit tests: `test_document_worker_kb_config.py`
7. Add integration tests for KB-specific chunking

**Reference:**
- [backend/app/workers/document_tasks.py](../../backend/app/workers/document_tasks.py)
- [backend/app/services/kb_config_resolver.py](../../backend/app/services/kb_config_resolver.py)
- [docs/sprint-artifacts/7-17-service-integration.md](./7-17-service-integration.md) - Task 3

---

## MEDIUM Priority Items

### TD-4.2-1: SSE Streaming Reconnection Logic

**Source:** Story 4.2 (Chat Streaming UI)
**Priority:** Medium
**Effort:** 3 hours
**Status:** Open - Based on Pilot Feedback

**Description:**
SSE (Server-Sent Events) streaming for chat lacks automatic reconnection on connection drop.

**Missing Functionality:**
- Automatic retry on connection loss (exponential backoff)
- User notification of connection issues
- Graceful degradation to polling (fallback)

**Current State:**
- ✅ SSE streaming works for happy path
- ✅ Time-to-first-token <2s (performance target met)
- ❌ No retry logic on network interruption
- ❌ User sees "loading..." indefinitely on failure

**Proposed Resolution:**
Add SSE reconnection middleware with exponential backoff based on pilot feedback.

---

### TD-4.5-1: Confidence Scoring Algorithm Validation

**Source:** Story 4.5 (Draft Generation Streaming)
**Priority:** Medium (was HIGH - downgraded, requires pilot data)
**Effort:** 4 hours
**Status:** Pending Pilot Feedback

**Description:**
Confidence scoring formula needs empirical validation against pilot user feedback.

**Current Formula:**
```python
confidence = (
    avg_retrieval_score * 0.5 +
    source_coverage * 0.3 +
    semantic_coherence * 0.2
)
```

**Questions Requiring Pilot Data:**
- Are 80/50% thresholds appropriate for high/low classification?
- Does formula correlate with perceived draft quality?
- Should formula weight retrieval_score higher?
- Do users trust amber (medium) confidence sections?

**Proposed Resolution:**
- Collect pilot feedback on confidence accuracy
- Analyze false positives/negatives
- Adjust formula weights and thresholds based on data

---

### TD-4.6-1: Draft Editing Validation Warnings (AC6)

**Source:** Story 4.6 (Draft Editing)
**Priority:** Medium
**Effort:** 4 hours
**Status:** Open - UX Enhancement

**Description:**
Validation warnings for broken citations not implemented.

**Missing Functionality:**
1. Detect orphaned citations (markers without citation data)
2. Detect unused citations (citations without markers)
3. Detect invalid marker numbers (e.g., [999] when only 3 citations exist)
4. Warning badge in status bar showing count
5. Auto-fix options (remove orphaned, renumber)

**Current State:**
- ✅ Core draft editing works (AC1-AC5 complete)
- ✅ Citation preservation (HTML-based, XSS-protected)
- ❌ AC6 validation warnings not implemented

---

### TD-4.8-1: Feedback Button DraftEditor Integration

**Source:** Story 4.8 (Generation Feedback & Recovery)
**Priority:** Medium
**Effort:** 4 hours
**Status:** Open - Components ready, integration pending

**Description:**
AC1 "This doesn't look right" button integration with DraftEditor deferred. All UI components exist and are tested, but not wired into DraftEditor.

**Current State:**
- ✅ FeedbackModal component (5 feedback types, tested)
- ✅ RecoveryModal component (alternative suggestions, tested)
- ✅ ErrorRecoveryDialog component (error recovery UI, tested)
- ✅ useFeedback hook (POST /api/v1/drafts/{id}/feedback, tested)
- ✅ Backend endpoint functional (3 alternatives per feedback type)
- ❌ DraftEditor button not added
- ❌ Regeneration flow not wired up

**Required Integration:**
1. Add "This doesn't look right" button to DraftEditor toolbar
2. Wire button click → FeedbackModal open
3. Wire FeedbackModal submit → useFeedback.handleSubmit
4. Wire alternative selection → regeneration flow
5. Show ErrorRecoveryDialog on generation failures

---

### TD-4.8-2: Feedback Analytics Dashboard

**Source:** Story 4.8 (Generation Feedback & Recovery)
**Priority:** Medium
**Effort:** 6 hours
**Status:** Future Enhancement

**Description:**
Analytics dashboard to visualize feedback patterns, common issues, and regeneration success rates.

**Proposed Features:**
- Feedback type distribution chart
- Common issues by KB
- Regeneration success rate over time
- User feedback trends

---

### TD-5.2-1: Audit Log Retention & Archiving

**Source:** Story 5-2 (Audit Log Viewer)
**Priority:** Medium
**Effort:** 8-16 hours
**Status:** Future - Compliance Sprint

**Description:**
Audit logs grow indefinitely with no retention policy or archiving mechanism.

**Proposed Enhancement:**
1. System configuration for retention days (AUDIT_RETENTION_DAYS)
2. Celery Beat cleanup task
3. Archive to file/S3 before delete
4. Admin UI controls for retention settings
5. Compliance modes (Standard, Compliance Hold, Minimal/GDPR erasure)

---

### TD-6.1-1: Bulk Document Operations

**Source:** Epic 6 (Document Lifecycle Management)
**Priority:** Medium
**Effort:** 4-8 hours
**Status:** Future Enhancement

**Description:**
Only bulk purge implemented. Missing bulk archive, delete, clear failed.

**Current State:**
- ✅ Bulk purge: `POST /kb/{kb_id}/documents/bulk-purge` - Implemented
- ❌ Bulk archive: Not implemented
- ❌ Bulk delete: Not implemented
- ❌ Bulk clear failed: Not implemented
- ❌ Select all / batch selection UI: Not implemented

**Proposed Endpoints:**
- `POST /documents/bulk-archive`
- `POST /documents/bulk-delete`
- `POST /documents/bulk-clear`

---

### TD-4.7-4: Export Audit Logging (AC6)

**Source:** Story 4.7 (Document Export)
**Priority:** Medium
**Effort:** 2 hours
**Status:** Open - Audit infrastructure exists

**Description:**
AC6 (Export Audit Logging) implementation code exists but was commented out. Now that Story 5.14 implemented audit infrastructure, this can be enabled.

**Required Work:**
1. Uncomment audit logging code in export endpoint
2. Add integration test: `test_export_audit_logging`
3. Validate audit event fields and privacy constraints

---

### TD-4.7-5: PDF Export Citation Formatting Quality

**Source:** Story 4.7 (Document Export)
**Priority:** Medium
**Effort:** 4 hours
**Status:** Based on Pilot Feedback

**Description:**
PDF export uses basic text-based citation rendering. Footnotes may not render cleanly for complex documents.

**Potential Issues:**
- Page breaks may split footnotes awkwardly
- Multi-column layouts not supported
- Custom fonts/styling limited

**Proposed Resolution:**
- Gather pilot feedback on PDF quality
- If needed, upgrade to professional PDF library (e.g., WeasyPrint with CSS)

---

## LOW Priority Items

### TD-4.9-2: Custom Template Database Storage

**Source:** Story 4.9 (Generation Templates)
**Priority:** Low
**Effort:** 8 hours
**Status:** Future Enhancement - MVP 2

**Description:**
Only 4 built-in templates. No user-defined custom templates.

**Missing Functionality:**
- Admin UI to create/edit templates
- Template storage (database table)
- Template versioning
- Template sharing across organization

**Note:** This is distinct from KB Settings Presets (TD-7.16-1). Templates are for document generation (RFP, Checklist, etc.), presets are for KB configuration (Legal, Technical, etc.).

---

### TD-7.16-1: Dynamic KB Presets with Database Storage

**Source:** Story 7-16 (KB Settings Presets)
**Priority:** Low
**Effort:** 8-16 hours
**Status:** Future Enhancement

**Description:**
KB presets hard-coded in `backend/app/core/kb_presets.py`. No admin-created custom presets or user-saved configurations.

**Current State:**
- ✅ 5 system presets: Legal, Technical, Creative, Code, General
- ✅ Hard-coded with `KBSettings` Pydantic models
- ✅ Helper functions: `get_preset()`, `list_presets()`, `detect_preset()`
- ❌ No database storage
- ❌ No admin UI for preset management

**Proposed Enhancement:**
- Database table for presets (kb_presets)
- Admin CRUD API for custom presets
- Mark system presets as read-only
- Import/Export presets (JSON)

---

### TD-4.10-1: Audit Log Query Performance

**Source:** Story 4.10 (Generation Audit Logging)
**Priority:** Low
**Effort:** 2 hours
**Status:** At Scale

**Description:**
Audit log query endpoint may need optimization for large datasets (>100K events).

**Proposed Resolution:**
- Add database indexes on audit.events (user_id, timestamp, event_type)
- Implement cursor-based pagination (currently uses offset)

---

### TD-4.7-6: Export Rate Limiting

**Source:** Story 4.7 (Document Export)
**Priority:** Low
**Effort:** 2 hours
**Status:** At Scale

**Description:**
No rate limiting on export endpoint. User could spam export requests.

**Missing Protection:**
- Per-user rate limit (e.g., 10 exports/minute)
- Abuse detection/alerting
- Export queue management for large documents

---

### TD-7.8-1: Chunk-to-Document Position Sync

**Source:** Story 7-8 (UI Scroll Isolation Fix)
**Priority:** Low (P3)
**Effort:** 4 hours
**Status:** UX Polish

**Description:**
Chunk viewer chunk position doesn't always sync with document viewer position due to extraction module offset differences.

---

### TD-7.8-2: Chunk Search Semantic Enhancement

**Source:** Story 7-8 (UI Scroll Isolation Fix)
**Priority:** Low (P4)
**Effort:** 2 hours
**Status:** Feature Enhancement

**Description:**
Chunk search uses text search. Could benefit from semantic search for better relevance.

---

## RESOLVED Items (Reference)

### Resolved in Story 5.10
| ID | Description |
|----|-------------|
| TD-3.7-1 | Command Palette Test Coverage (shouldFilter fix) |

### Resolved in Story 5.15
| ID | Description |
|----|-------------|
| TD-4.0-1 | ATDD Test Suite Transition to GREEN |
| TD-4.1-1 | Chat API Integration Test Mocks (Qdrant + LiteLLM) |
| TD-4.2-2 | Chat Streaming Integration Test Dependency |
| TD-4.5-2 | Draft Generation Integration Tests |
| TD-4.7-1 | Frontend Component Test Import Fixes |
| TD-4.7-2 | Backend Integration Test Execution |
| TD-4.7-3 | Export E2E Test Validation |
| TD-4.9-1 | Template Selection E2E Tests |
| TD-4.9-2 | Test File TypeScript Cleanup |
| TD-4.8-3 | Feedback/Recovery Test Coverage (32/32 frontend, 8 integration) |

### Resolved in Epic 7
| ID | Description | Story |
|----|-------------|-------|
| TD-5.15-1 | Backend Unit Test Constructor Mismatches | Story 7-6 |
| TD-5.26-1 | Async Qdrant Client Migration | Story 7-7 |

### Document Processing Defects (RESOLVED 2025-12-06)
| Defect | Description |
|--------|-------------|
| P0 | PostgreSQL Connection Pool Exhaustion - FIXED |
| P1 | Duplicate Documents on Single Upload - FIXED |
| P2 | Documents Stuck in Processing - FIXED |

---

## Known Limitations (Accepted)

| Issue | Notes |
|-------|-------|
| **Scroll Isolation** | react-resizable-panels propagates scroll; workaround applied with `overscroll-behavior: contain` |
| **Chunk Viewer Scroll Sync** | Split-pane linked scrolling deferred; 9 solutions attempted, none successful |

---

## Tracking Table

| ID | Priority | Status | Target | Effort |
|----|----------|--------|--------|--------|
| TD-7.17-1 | **HIGH** | Open | **Next Sprint** | 4-6h |
| TD-4.2-1 | MEDIUM | Open | Pilot Feedback | 3h |
| TD-4.5-1 | MEDIUM | Pending | Post-Pilot | 4h |
| TD-4.6-1 | MEDIUM | Open | UX Enhancement | 4h |
| TD-4.7-4 | MEDIUM | Open | Ready | 2h |
| TD-4.7-5 | MEDIUM | Open | Pilot Feedback | 4h |
| TD-4.8-1 | MEDIUM | Open | Ready | 4h |
| TD-4.8-2 | MEDIUM | Open | Future | 6h |
| TD-5.2-1 | MEDIUM | Open | Compliance | 8-16h |
| TD-6.1-1 | MEDIUM | Open | Feature | 4-8h |
| TD-4.9-2 | LOW | Open | MVP 2 | 8h |
| TD-7.16-1 | LOW | Open | Future | 8-16h |
| TD-4.10-1 | LOW | Open | At Scale | 2h |
| TD-4.7-6 | LOW | Open | At Scale | 2h |
| TD-7.8-1 | LOW | Open | Polish | 4h |
| TD-7.8-2 | LOW | Open | Feature | 2h |

---

## Tech Debt Sprint (Pre-Epic 8) - Stories 7-18 through 7-23

**Purpose:** Resolve accumulated tech debt before starting GraphRAG epic
**Duration:** 2025-12-10 to 2025-12-12 (3 days)
**Total Effort:** ~23h

### Sprint Backlog

| Story ID | Description | Effort | Story File |
|----------|-------------|--------|------------|
| **7-18** | Document Worker KB Config (HIGH) | 4-6h | [7-18-document-worker-kb-config.md](./7-18-document-worker-kb-config.md) |
| 7-19 | Export Audit Logging | 2h | [7-19-export-audit-logging.md](./7-19-export-audit-logging.md) |
| 7-20 | Feedback Button Integration | 4h | [7-20-feedback-button-integration.md](./7-20-feedback-button-integration.md) |
| 7-21 | Draft Validation Warnings | 4h | [7-21-draft-validation-warnings.md](./7-21-draft-validation-warnings.md) |
| 7-22 | SSE Reconnection (pilot feedback) | 3h | [7-22-sse-reconnection.md](./7-22-sse-reconnection.md) |
| 7-23 | Feedback Analytics (future) | 6h | [7-23-feedback-analytics.md](./7-23-feedback-analytics.md) |

### Execution Order

1. **Story 7-18** (HIGH priority) - blocks KB chunking feature
2. **Story 7-19** - quick win, infrastructure exists
3. **Story 7-20** - components ready, just wire up
4. **Story 7-21** - UX enhancement
5. Story 7-22 / Story 7-23 - if time permits

---

## Recommended Next Actions

1. **Story 7-18** (HIGH): Integrate `KBConfigResolver` with document workers - blocking KB chunking config feature
2. **Story 7-19** (MEDIUM): Enable export audit logging - audit infrastructure now exists
3. **Story 7-20** (MEDIUM): Wire feedback button into DraftEditor - components ready

---

## Archived Tech Debt Files

The following files are now archived and reference this consolidated tracker:
- [epic-4-tech-debt.md](./epic-4-tech-debt.md) - Status: ARCHIVED
- [epic-5-tech-debt.md](./epic-5-tech-debt.md) - Status: ARCHIVED
- [tech-debt-backend-unit-tests.md](./tech-debt-backend-unit-tests.md) - RESOLVED in Story 7-6
- [tech-debt-scroll-isolation.md](./tech-debt-scroll-isolation.md) - ACCEPTED as known limitation
- [tech-debt-chunk-viewer.md](./tech-debt-chunk-viewer.md) - Partial resolution, TD-7.8-1/2 remain
- [tech-debt-document-processing.md](./tech-debt-document-processing.md) - RESOLVED 2025-12-06

---

**Document Owner:** Tung Vu
**Last Updated:** 2025-12-10
**Next Review:** After Epic 8 planning or next sprint planning
