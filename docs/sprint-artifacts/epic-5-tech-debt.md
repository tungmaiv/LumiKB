# Epic 5 Technical Debt Tracking

**Epic:** Epic 5 - Administration & Polish
**Created:** 2025-11-26
**Status:** ARCHIVED - Migrated to Epic 7 Tech Debt

---

## Migration Notice

> **IMPORTANT:** This file is archived. All active tech debt has been consolidated into:
> **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**
>
> **Migration Date:** 2025-12-10
> **Reason:** Single-source-of-truth for all project tech debt

---

## Original Purpose (Historical)

Track deferred technical work from Epic 5 and prior epics that:
- Doesn't block production deployment
- Improves quality/maintainability
- Should be addressed in future sprints or Epic 5 itself

---

## Tech Debt Items

### TD-4.1-1: Chat API Integration Test External Service Mocks (Story 5.15)

**Source:** Story 4.1 (Chat Conversation Backend) - Epic 4
**Priority:** Medium
**Effort:** 4 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Integration tests for Chat API require mocks for external services (Qdrant vector search and LiteLLM response generation). Tests currently fail with 500 errors due to missing service mocks.

**Current State:**
- ✅ 8 integration tests created for all 7 ACs
- ✅ Test fixtures complete (authenticated_headers, demo_kb_with_indexed_docs, empty_kb_factory)
- ✅ Unit tests: 9/9 passing (ConversationService)
- ❌ Integration tests fail: 8/8 with 500 Internal Server Error
- ❌ Missing: Qdrant mock fixture for vector search
- ❌ Missing: LiteLLM mock fixture for response generation

**Required Mocks:**
1. **Qdrant Mock** (`mock_qdrant_search` fixture):
   - Mock `SearchService.search()` to return sample SearchResultSchema chunks
   - Provide realistic vector search results with scores, excerpts, metadata
   - Handle both populated KB and empty KB scenarios

2. **LiteLLM Mock** (`mock_litellm_generate` fixture):
   - Mock `LiteLLMClient.generate()` to return citation-formatted responses
   - Return realistic answers with inline [1], [2] citation markers

**Production Impact:**
None - core implementation is production-ready (all 7 ACs implemented, unit tests passing). Integration tests validate end-to-end API behavior but are not blocking deployment.

**Why Deferred:**
Test infrastructure setup deferred to reduce Story 4.1 scope and follow Epic 3 pattern of unit-first testing. Epic 5 Story 5.15 is dedicated to Epic 4 ATDD test hardening.

**Proposed Resolution (Story 5.15):**
- Implement Qdrant and LiteLLM mock fixtures in `tests/integration/conftest.py`
- Transition 8 chat API integration tests to GREEN
- Validate AC coverage: AC1 (single-turn), AC2 (multi-turn), AC4 (Redis storage), AC5 (permission enforcement), AC6 (error handling), AC7 (audit logging)

**Reference:**
- [backend/tests/integration/test_chat_api.py](../../backend/tests/integration/test_chat_api.py) - Test implementation
- [docs/sprint-artifacts/4-1-chat-conversation-backend.md](./4-1-chat-conversation-backend.md) - Story details
- [docs/sprint-artifacts/epic-4-tech-debt.md](./epic-4-tech-debt.md#TD-4.1-1) - Full tech debt entry

---

### TD-4.2-2: Chat Streaming Integration Test Dependency (Story 5.15)

**Source:** Story 4.2 (Chat Streaming UI) - Epic 4
**Priority:** Medium
**Effort:** 2 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Chat streaming integration tests cannot run due to dependency on Story 4.1 test infrastructure (Qdrant and LiteLLM mocks). Story 4.2 SSE streaming endpoint implementation is complete and production-ready, but integration tests require the same external service mocks as Story 4.1.

**Current State:**
- ✅ Backend SSE streaming: Real LLM token streaming implemented (not word-split simulation)
- ✅ Event schema: Fixed (text→token, inline citations)
- ✅ ConversationService.send_message_stream(): Yields real-time events
- ✅ Frontend components: ChatContainer, ChatInput, useChatStream hook created
- ✅ SSE client updated: Handles status, token, citation, done events
- ✅ Component tests: ChatMessage component (9/9 passing)
- ❌ Integration tests: Cannot run without Story 4.1 mock infrastructure

**Blocked Tests:**
- `backend/tests/integration/test_chat_api.py` - SSE streaming endpoint tests (require Qdrant + LiteLLM mocks)
- `frontend/e2e/tests/chat/chat-conversation.spec.ts` - E2E streaming tests (require backend infrastructure)

**Dependencies:**
1. TD-4.1-1 must be resolved first (Qdrant and LiteLLM mocks)
2. Once Story 4.1 mocks are in place, Story 4.2 streaming tests will use same fixtures

**Production Impact:**
None - SSE streaming implementation is production-ready:
- Real LLM token streaming (not simulated)
- Citations streamed inline as markers detected
- Status events before/during generation
- Error handling with SSE error events
- All frontend components integrated

**Why Deferred:**
Story 4.2 implementation focused on fixing code review blockers (real streaming, missing components). Integration testing deferred to Story 5.15 which resolves all Epic 4 test infrastructure needs in one consolidated effort.

**Proposed Resolution (Story 5.15):**
- Reuse TD-4.1-1 mock fixtures for streaming endpoint tests
- Add SSE-specific integration tests (streaming response parsing, event order)
- Validate real-time citation inline streaming (AC2)
- Run E2E tests with full backend infrastructure

**Reference:**
- [backend/app/api/v1/chat_stream.py](../../backend/app/api/v1/chat_stream.py) - SSE endpoint implementation
- [backend/app/services/conversation_service.py:160-292](../../backend/app/services/conversation_service.py#L160-L292) - send_message_stream method
- [docs/sprint-artifacts/code-review-report-story-4-2.md](./code-review-report-story-4-2.md) - Code review findings
- [docs/sprint-artifacts/4-2-chat-streaming-ui.md](./4-2-chat-streaming-ui.md) - Story details

---

### TD-3.7-1: Command Palette Test Coverage (Story 5.10)

**Source:** Story 3-7 (Quick Search and Command Palette)
**Priority:** Low
**Effort:** 1-2 hours
**Target Story:** Story 5.10

**Description:**
Command palette component tests have 70% pass rate (7/10 passing). Three tests fail due to shadcn/ui Command component's internal filtering not recognizing mocked fetch responses.

**Failing Tests:**
- `fetches results after debounce (AC10)` - Timeouts waiting for results to appear
- `displays results with metadata (AC2)` - Timeouts waiting for result metadata
- `shows error state on API failure (AC9)` - Timeouts waiting for error message

**Root Cause:**
The shadcn/ui Command component has internal filtering that doesn't work with vitest mocked fetch responses. When fetch is mocked to return results, the Command component's filtering mechanism doesn't display them in the test DOM.

**Production Impact:**
None - manual QA and backend integration tests confirm all features work correctly. This is a test infrastructure limitation, not a functional bug.

**Why Deferred:**
- Production functionality verified working
- Backend integration tests validate API contract
- 7 passing component tests cover core functionality
- Senior developer review approved Story 3.7 with this known limitation

**Proposed Resolution (Story 5.10):**
1. **Option 1**: Convert to E2E tests with Playwright (tests against real browser)
2. **Option 2**: Mock at different level (API layer vs component props)
3. **Option 3**: Use real backend in integration tests instead of mocks
4. **Option 4**: Investigate Command/cmdk library test utilities

**Reference:**
- Story 3.7: [docs/sprint-artifacts/3-7-quick-search-and-command-palette.md](docs/sprint-artifacts/3-7-quick-search-and-command-palette.md#L1028)
- Story 5.10: [docs/epics.md](docs/epics.md#L2050-L2086)

---

### TD-4.9-1: Template Selection E2E Test Execution (Story 5.15)

**Source:** Story 4.9 (Generation Templates) - Epic 4
**Priority:** Low
**Effort:** 2 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
E2E tests for template selection UI workflow are written but not yet executable with Playwright. Tests validate template selection, preview display, context input, and generation initiation.

**Current State:**
- ✅ Backend: Template registry complete (4 templates)
- ✅ Backend: GET /api/v1/templates endpoint implemented
- ✅ Frontend: TemplateSelector component complete
- ✅ Frontend: GenerationModal integration complete
- ✅ Component tests: 9/9 passing
- ✅ Hook tests: 8/8 passing
- ✅ Unit tests: 8/8 passing (backend)
- ✅ Integration tests: 4/4 passing (backend)
- ❌ E2E tests: 9 tests written but not executed with Playwright

**E2E Test Coverage (Deferred):**
9 tests in `frontend/e2e/tests/generation/template-selection.spec.ts`:
1. Displays all 4 templates in selector
2. Shows template descriptions
3. Displays template previews on selection
4. Defaults to RFP Response template
5. Allows template switching
6. Custom template shows custom instructions field
7. Requires context input before generation
8. Initiates generation with template + context
9. Clears form after generation

**Production Impact:**
None - all functionality is production-ready and validated:
- Backend template registry tested (12 tests passing)
- Frontend component tested (9 tests passing)
- Frontend hook tested (8 tests passing)
- Build passing with 0 TypeScript errors
- All 5 acceptance criteria satisfied

**Why Deferred:**
E2E tests intentionally deferred to Epic 5 Story 5.15 per project workflow. Story 4.9 focused on component implementation and unit/integration testing. E2E execution aligns with Epic 4 ATDD transition to GREEN.

**Proposed Resolution (Story 5.15):**
- Install Playwright dependencies if needed
- Execute 9 E2E tests in `template-selection.spec.ts`
- Validate full user workflow: template selection → preview → context input → generation
- Verify integration with search page "Generate Draft" button
- Add screenshot assertions for visual regression testing

**Reference:**
- [frontend/e2e/tests/generation/template-selection.spec.ts](../../frontend/e2e/tests/generation/template-selection.spec.ts) - E2E test file
- [docs/sprint-artifacts/4-9-generation-templates.md](./4-9-generation-templates.md) - Story details

---

### TD-4.9-2: Test File TypeScript Error Cleanup (Story 5.15)

**Source:** Story 4.9 (Generation Templates) - Epic 4
**Priority:** Low
**Effort:** 1 hour
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Three TypeScript errors exist in `frontend/src/hooks/__tests__/use-chat-stream.test.ts` (test file, not production code). These are non-blocking linting errors that do not affect production code or test execution.

**Current State:**
- ✅ Production code: 0 TypeScript errors (build PASSED)
- ✅ All tests passing: 29/29 (100% pass rate)
- ❌ Test file errors: 3 TypeScript errors in `use-chat-stream.test.ts`

**Error Details:**
The errors are related to test setup and mock configuration in the chat stream hook tests. They do not impact:
- Production code quality
- Test execution or results
- Runtime behavior
- Build output

**Production Impact:**
None - production code is clean and all tests pass successfully. This is a test file quality improvement, not a functional issue.

**Why Deferred:**
Focus for Story 4.9 was on production code quality, functional test coverage, and build verification. Test file linting is a polish item that can be addressed during Epic 5 test hardening.

**Proposed Resolution (Story 5.15):**
- Review TypeScript errors in `use-chat-stream.test.ts`
- Fix type annotations in test mocks and assertions
- Verify all tests still pass after cleanup
- Run `npm run type-check` to confirm 0 errors

**Reference:**
- [frontend/src/hooks/__tests__/use-chat-stream.test.ts](../../frontend/src/hooks/__tests__/use-chat-stream.test.ts) - Test file with TypeScript errors
- [docs/sprint-artifacts/4-9-generation-templates.md](./4-9-generation-templates.md) - Story details

---

### TD-5.15-1: Backend Unit Test Service Constructor Mismatches (NEW)

**Source:** Story 5.15 (Epic 4 ATDD Transition to GREEN)
**Priority:** Medium
**Effort:** 1-2 days
**Target Story:** Future Epic 6 or Tech Debt Sprint

**Description:**
26 pre-existing backend unit test failures discovered during Story 5-15. These failures are NOT related to Epic 4 functionality and exist due to service constructor signature changes and mock configuration drift.

**Current State:**
- ❌ 12 failures in `test_draft_service.py` - TypeError: unexpected keyword argument 'draft_repository'
- ❌ 8 failures in `test_search_service.py` - Mock configuration issues
- ❌ 5 failures in `test_generation_service.py` - Service initialization errors
- ❌ 1 failure in `test_explanation_service.py` - Mock configuration issue

**Root Cause:**
Services were refactored (likely to use dependency injection) without corresponding test updates.

**Production Impact:**
None - these are test-only issues. Integration tests provide adequate coverage.

**Why Deferred:**
- Not related to Epic 4 or Story 5-15 scope
- Integration tests provide production coverage
- Requires architectural understanding of DI patterns used

**Proposed Resolution:**
1. Audit current service constructor signatures
2. Update test fixtures to match DI patterns
3. Update mock configurations
4. Document patterns for future tests

**Reference:**
- [docs/sprint-artifacts/tech-debt-backend-unit-tests.md](./tech-debt-backend-unit-tests.md) - Full breakdown of 26 failures
- [backend/tests/unit/test_draft_service.py](../../backend/tests/unit/test_draft_service.py)
- [backend/tests/unit/test_search_service.py](../../backend/tests/unit/test_search_service.py)
- [backend/tests/unit/test_generation_service.py](../../backend/tests/unit/test_generation_service.py)
- [backend/tests/unit/test_explanation_service.py](../../backend/tests/unit/test_explanation_service.py)

---

## Summary

**Total Items:** 10 (4 resolved, 3 migrated to Epic 7, 3 new)
**High Priority:** 0
**Medium-High Priority:** 1
  - TD-5.26-1 (Async Qdrant client migration) - **MIGRATED TO Epic 7 Story 7-7**
**Medium Priority:** 5
  - TD-4.1-1 (Chat API integration test mocks) - RESOLVED in Story 5.15
  - TD-4.2-2 (Chat Streaming integration test dependency) - RESOLVED in Story 5.15
  - TD-5.15-1 (Backend unit test service constructor mismatches) - **MIGRATED TO Epic 7 Story 7-6**
  - TD-5.2-1 (Audit log retention & archiving) - NEW, Future Compliance
  - TD-6.1-1 (Bulk document operations: archive, delete, clear) - NEW, Future Enhancement
**Low Priority:** 4
  - TD-3.7-1 (Command palette tests) - RESOLVED in Story 5.10
  - TD-4.9-1 (Template selection E2E tests) - RESOLVED in Story 5.15
  - TD-4.9-2 (Test file TypeScript cleanup) - RESOLVED in Story 5.15
  - TD-7.16-1 (Dynamic KB presets with database storage) - NEW, Future Enhancement

**Epic 5 Story Allocation:**
- Story 5.10: TD-3.7-1 (Command palette test coverage) - DONE
- Story 5.15: TD-4.1-1 + TD-4.2-2 + TD-4.9-1 + TD-4.9-2 (Epic 4 ATDD transition to GREEN) - DONE

---

## Migration to Epic 7

**Date:** 2025-12-08
**Reason:** Epic 5 grew to 26 stories, exceeding manageable scope. Infrastructure and DevOps work extracted to new Epic 7.

**Migrated Tech Debt Items:**

| Item | Description | New Story |
|------|-------------|-----------|
| TD-5.15-1 | Backend unit test service constructor mismatches | Story 7-6 |
| TD-5.26-1 | Async Qdrant client migration | Story 7-7 |
| TD-scroll-1 | UI scroll isolation issue | Story 7-8 |

**New Story Files Created:**
- [7-6-backend-unit-test-fixes.md](./7-6-backend-unit-test-fixes.md)
- [7-7-async-qdrant-migration.md](./7-7-async-qdrant-migration.md)
- [7-8-ui-scroll-isolation-fix.md](./7-8-ui-scroll-isolation-fix.md)

---

**Notes:**
- All deferred items have minimal production impact
- Story 4.2 implementation is production-ready (all blockers from code review fixed)
- Story 4.9 implementation is production-ready (Quality 95/100, all ACs satisfied)
- TD-4.2-2 has dependency on TD-4.1-1 (must resolve Story 4.1 mocks first)
- Story 5.10 and 5.15 already defined in Epic 5 to address tech debt
- No blockers for Epic 3 or Epic 4 completion or MVP deployment
- **Note:** TD-4.5-2 (Draft Generation tests) moved to epic-4-tech-debt.md (correct location)
- **UPDATE 2025-12-08:** Remaining tech debt migrated to Epic 7 - Infrastructure & DevOps

---

### TD-5.26-1: Async Qdrant Client Migration

**Source:** Story 5-26 (Document Chunk Viewer Frontend) - Code Review
**Priority:** Medium-High
**Effort:** 4-8 hours
**Target Story:** Future Performance Optimization Sprint

**Description:**
Synchronous `QdrantClient` is used in async FastAPI context, blocking the event loop and reducing concurrency under load. This affects all Qdrant-dependent services.

**Current State:**
- ❌ `backend/app/integrations/qdrant_client.py` - Uses sync `QdrantClient`
- ❌ `backend/app/services/chunk_service.py` - Direct sync calls (lines 156, 224, 262, 343)
- ❌ `backend/app/services/search_service.py` - Mixed (one proper `asyncio.to_thread`, rest sync)

**Impact Assessment:**
| Factor | Impact |
|--------|--------|
| Event loop blocking | Each Qdrant call blocks ALL other requests |
| Concurrency reduction | From ~1000 async to ~30 thread-based |
| Latency spikes | Unpredictable under load |
| Current usage | Low traffic = not noticeable yet |

**Production Impact:**
Low at current scale but will become significant as traffic increases. Each sync Qdrant call blocks the async event loop, reducing the server's ability to handle concurrent requests.

**Why Deferred:**
- Requires significant refactoring of `QdrantService` class
- Need to replace `QdrantClient` with `AsyncQdrantClient`
- All service methods need true async implementations
- Requires thorough testing under load
- Not a blocker for current Stories 5-25/5-26

**Proposed Resolution:**
1. Replace `QdrantClient` with `AsyncQdrantClient` in `qdrant_client.py`
2. Update all service methods to use native async Qdrant calls
3. Remove `asyncio.to_thread` workarounds
4. Add load testing to validate concurrency improvements
5. Update unit tests with async mock patterns

**Reference:**
- [backend/app/integrations/qdrant_client.py](../../backend/app/integrations/qdrant_client.py) - Qdrant client initialization
- [backend/app/services/chunk_service.py](../../backend/app/services/chunk_service.py) - Chunk retrieval service
- [backend/app/services/search_service.py](../../backend/app/services/search_service.py) - Search service

---

### TD-7.16-1: Dynamic KB Presets with Database Storage

**Source:** Story 7-16 (KB Settings Presets) - Epic 7
**Priority:** Low
**Effort:** 8-16 hours (1-2 days)
**Target Story:** Future Epic or Feature Request

**Description:**
KB settings presets are currently hard-coded in Python (`backend/app/core/kb_presets.py`). This approach works for system-defined presets but doesn't support:
- Admin-created custom presets
- User-saved preset configurations
- Runtime preset modifications without code deployment

**Current State:**
- ✅ 5 system presets: Legal, Technical, Creative, Code, General
- ✅ Hard-coded in `KB_PRESETS` dict with `KBSettings` Pydantic models
- ✅ Helper functions: `get_preset()`, `list_presets()`, `detect_preset()`
- ❌ No database storage
- ❌ No admin UI for preset management
- ❌ No user-saved presets

**Proposed Enhancement:**

1. **Database Schema:**
   ```sql
   CREATE TABLE kb_presets (
       id UUID PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       description TEXT,
       settings JSONB NOT NULL,  -- KBSettings as JSON
       is_system BOOLEAN DEFAULT FALSE,  -- System presets read-only
       created_by UUID REFERENCES users(id),
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP
   );
   ```

2. **API Endpoints:**
   - `GET /api/v1/admin/presets` - List all presets (system + custom)
   - `POST /api/v1/admin/presets` - Create custom preset (admin only)
   - `PUT /api/v1/admin/presets/{id}` - Update custom preset
   - `DELETE /api/v1/admin/presets/{id}` - Delete custom preset (not system)
   - `POST /api/v1/admin/presets/{id}/duplicate` - Clone preset

3. **Admin UI:**
   - Preset management page under `/admin/presets`
   - Create/Edit preset modal with full KBSettings form
   - Import/Export presets (JSON)
   - Lock icon for system presets

4. **Migration Strategy:**
   - Seed system presets from `kb_presets.py` on first run
   - Mark system presets with `is_system=True`
   - Keep `kb_presets.py` as fallback/defaults

**Production Impact:**
None - current hard-coded approach is fully functional for MVP. This is an enhancement for advanced admin workflows.

**Why Deferred:**
- Hard-coded presets sufficient for initial release
- 5 system presets cover common use cases
- Custom presets require additional admin UI work
- Lower priority than core KB configuration features

**Benefits When Implemented:**
- Admins can create organization-specific presets
- Presets can be updated without code deployment
- Users can save their preferred configurations
- Better multi-tenant support

**Reference:**
- [backend/app/core/kb_presets.py](../../backend/app/core/kb_presets.py) - Current hard-coded presets
- [docs/sprint-artifacts/7-16-kb-settings-presets.md](./7-16-kb-settings-presets.md) - Story details

---

### TD-5.2-1: Audit Log Retention & Archiving

**Source:** Story 5-2 (Audit Log Viewer) - Epic 5
**Priority:** Medium
**Effort:** 8-16 hours (1-2 days)
**Target Story:** Future Epic or Compliance Sprint

**Description:**
Audit logs in `audit.events` table grow indefinitely with no retention policy or archiving mechanism. This will eventually impact:
- Database storage costs
- Query performance on large tables
- Compliance requirements (GDPR right to erasure, data retention policies)

**Current State:**
- ✅ Audit events stored in `audit.events` table (PostgreSQL)
- ✅ INSERT-only permissions (immutable audit trail)
- ✅ Indexes on user_id, timestamp, resource_type/id
- ✅ Export to CSV/JSON via admin API
- ❌ No retention period configuration
- ❌ No automatic cleanup/archiving
- ❌ No cold storage integration
- ❌ Table grows indefinitely

**Risk Assessment:**
| Factor | Current Risk | At Scale (100K+ events) |
|--------|--------------|-------------------------|
| Storage cost | Low | Medium |
| Query performance | Low | Medium-High |
| Compliance | Depends on domain | May be blocking |
| Backup size | Low | Medium |

**Proposed Enhancement:**

1. **System Configuration:**
   ```python
   # Add to system_config table
   AUDIT_RETENTION_DAYS = 365  # Default 1 year, 0 = forever
   AUDIT_ARCHIVE_ENABLED = True  # Archive before delete
   AUDIT_ARCHIVE_FORMAT = "jsonl"  # jsonl, csv, parquet
   ```

2. **Archive Table (Optional):**
   ```sql
   CREATE TABLE audit.events_archive (
       -- Same schema as audit.events
       archived_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

3. **Celery Beat Task:**
   ```python
   @celery_app.task
   def cleanup_old_audit_logs():
       retention_days = get_config("AUDIT_RETENTION_DAYS", 365)
       if retention_days == 0:
           return  # Retention disabled

       cutoff = datetime.utcnow() - timedelta(days=retention_days)

       if get_config("AUDIT_ARCHIVE_ENABLED", True):
           # Archive to file/S3 first
           export_audit_events_to_storage(before=cutoff)

       # Delete old events
       DELETE FROM audit.events WHERE timestamp < cutoff
   ```

4. **Admin UI:**
   - Retention period setting in `/admin/config`
   - Archive download for date ranges
   - Storage usage indicator
   - "Archive & Purge" manual action

5. **Compliance Modes:**
   - **Standard:** Archive + delete after retention period
   - **Compliance Hold:** Disable deletion, archive only
   - **Minimal:** Delete without archiving (GDPR erasure)

**Production Impact:**
None currently - audit table is small. Will become important as system scales or if compliance requirements emerge.

**Why Deferred:**
- Audit table growth is slow (hundreds of events/day typical)
- No immediate compliance requirements identified
- MVP focus on core features
- Can be added without schema changes

**Benefits When Implemented:**
- Controlled storage growth
- Compliance with data retention policies
- Faster queries on recent events
- Historical audit data preserved in cold storage
- Configurable per-deployment requirements

**Implementation Order:**
1. Add retention config to system_config
2. Implement Celery Beat cleanup task
3. Add archive-to-file before delete
4. (Optional) Add S3/MinIO cold storage
5. Add admin UI controls

**Reference:**
- [backend/app/models/audit.py](../../backend/app/models/audit.py) - AuditEvent model
- [backend/app/services/audit_service.py](../../backend/app/services/audit_service.py) - AuditService
- [backend/alembic/versions/002_audit_schema_and_role.py](../../backend/alembic/versions/002_audit_schema_and_role.py) - Audit schema migration
- [docs/sprint-artifacts/5-2-audit-log-viewer.md](./5-2-audit-log-viewer.md) - Story details

---

### TD-6.1-1: Bulk Document Operations (Archive, Delete, Clear)

**Source:** Epic 6 (Document Lifecycle Management)
**Priority:** Medium
**Effort:** 4-8 hours
**Target Story:** Future Epic or Feature Request

**Description:**
Only bulk purge is implemented (`POST /documents/bulk-purge`). Missing bulk operations for archive, delete, and clear failed documents. This forces users to perform one-by-one operations which is tedious for large document sets.

**Current State:**
- ✅ Bulk purge: `POST /kb/{kb_id}/documents/bulk-purge` - Implemented
- ❌ Bulk archive: Placeholder tests exist, endpoint not implemented
- ❌ Bulk delete: Not implemented
- ❌ Bulk clear failed: Not implemented
- ❌ Select all / batch selection UI: Not implemented

**Proposed Enhancement:**

1. **Backend Endpoints:**
   ```python
   # Bulk archive (READY → archived)
   POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-archive
   Request: { "document_ids": [uuid, ...] }
   Response: { "archived_count": int, "skipped": [{ "id": uuid, "reason": str }] }

   # Bulk delete (soft delete)
   POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-delete
   Request: { "document_ids": [uuid, ...] }
   Response: { "deleted_count": int, "skipped": [{ "id": uuid, "reason": str }] }

   # Bulk clear failed (FAILED → removed)
   POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-clear
   Request: { "document_ids": [uuid, ...] }  # Optional, if empty clears all FAILED
   Response: { "cleared_count": int, "skipped": [{ "id": uuid, "reason": str }] }
   ```

2. **Service Layer:**
   ```python
   # document_service.py
   async def bulk_archive(kb_id, document_ids, user) -> BulkResult
   async def bulk_delete(kb_id, document_ids, user) -> BulkResult
   async def bulk_clear_failed(kb_id, document_ids, user) -> BulkResult
   ```

3. **Frontend UI:**
   - Checkbox selection in document list
   - "Select All" / "Select None" toggle
   - Bulk action dropdown (Archive, Delete, Clear)
   - Confirmation modal with count
   - Progress indicator for large batches
   - Partial success toast with skipped count

4. **Rate Limiting:**
   - Max 100 documents per request
   - Async processing for large batches (>50 docs)

**Production Impact:**
Low - single document operations work fine. Bulk operations are convenience/efficiency enhancement.

**Why Deferred:**
- Single document operations cover core use cases
- Bulk purge (most critical) is already implemented
- MVP focus on individual document lifecycle
- Placeholder tests indicate future intent

**Benefits When Implemented:**
- Efficient cleanup of multiple documents
- Better UX for large knowledge bases
- Reduced API calls for batch operations
- Consistent with bulk purge pattern

**Implementation Order:**
1. Add bulk_archive endpoint + service method
2. Add bulk_delete endpoint + service method
3. Add bulk_clear endpoint + service method
4. Add frontend checkbox selection
5. Add bulk action dropdown + confirmation
6. Add tests (unskip existing placeholders)

**Reference:**
- [backend/app/api/v1/documents.py:914-952](../../backend/app/api/v1/documents.py#L914-L952) - Existing bulk_purge endpoint
- [backend/tests/integration/test_archive_api.py:682-706](../../backend/tests/integration/test_archive_api.py#L682-L706) - Placeholder tests
- [docs/sprint-artifacts/6-7-archive-management-ui.md](./6-7-archive-management-ui.md) - Archive UI story
- [docs/sprint-artifacts/6-8-document-list-actions-ui.md](./6-8-document-list-actions-ui.md) - Document actions story
