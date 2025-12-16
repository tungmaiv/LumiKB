# Technical Debt: Backend Unit Test Failures

**Created:** 2025-12-04
**Source:** Story 5-15 (Epic 4 ATDD Transition to GREEN)
**Priority:** Medium
**Estimated Effort:** 1-2 days
**Status:** RESOLVED in Story 7-6

---

## Migration Notice

> **RESOLVED:** This tech debt was addressed in Epic 7 Story 7-6 (Backend Unit Test Fixes).
> See consolidated tracker: **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**

---

## Summary

26 pre-existing backend unit test failures were identified during Story 5-15. These failures are NOT related to Epic 4 functionality and exist due to service constructor signature changes and mock configuration drift.

## Failing Tests (26 total)

### test_draft_service.py (12 failures)

**Root Cause:** `DraftService.__init__()` got an unexpected keyword argument `'draft_repository'`

| Test | Error |
|------|-------|
| `test_create_draft_sets_default_status` | TypeError: unexpected keyword argument |
| `test_create_draft_calculates_word_count` | TypeError: unexpected keyword argument |
| `test_create_draft_preserves_explicit_word_count` | TypeError: unexpected keyword argument |
| `test_transition_streaming_to_complete` | TypeError: unexpected keyword argument |
| `test_transition_complete_to_editing` | TypeError: unexpected keyword argument |
| `test_transition_editing_to_exported` | TypeError: unexpected keyword argument |
| `test_validate_citation_markers_match` | TypeError: unexpected keyword argument |
| `test_validate_detects_orphaned_citations` | TypeError: unexpected keyword argument |
| `test_validate_detects_missing_citation_data` | TypeError: unexpected keyword argument |
| `test_get_drafts_by_kb_filters_correctly` | TypeError: unexpected keyword argument |
| `test_get_draft_by_id_returns_single_draft` | TypeError: unexpected keyword argument |
| `test_delete_draft_calls_repository` | TypeError: unexpected keyword argument |

**Fix Required:** Update test mocks to match current `DraftService` constructor signature (likely uses dependency injection container now).

### test_search_service.py (8 failures)

**Root Cause:** Mock configuration doesn't match current service implementation

| Test | Error Type |
|------|------------|
| `test_search_collections_returns_chunks` | Mock assertion failure |
| `test_search_collections_sorts_by_relevance` | Mock assertion failure |
| `test_search_collections_raises_connection_error_on_qdrant_failure` | Mock configuration |
| `test_search_with_answer_synthesis_success` | Mock configuration |
| `test_search_synthesis_failure_graceful_degradation` | Mock configuration |
| `test_quick_search_returns_top_5_results` | Mock configuration |
| `test_quick_search_truncates_excerpt` | Mock configuration |
| `test_similar_search_excludes_original` | Mock configuration |

**Fix Required:** Update mocks to match current `SearchService` dependencies and method signatures.

### test_generation_service.py (5 failures)

**Root Cause:** Service dependencies changed since tests were written

| Test | Error Type |
|------|------------|
| `test_insufficient_sources_error` | Service initialization |
| `test_stream_yields_status_events` | Service initialization |
| `test_stream_yields_token_events` | Service initialization |
| `test_citation_detection_and_emission` | Service initialization |
| `test_done_event_with_metadata` | Service initialization |

**Fix Required:** Update `GenerationService` test initialization and mocks.

### test_explanation_service.py (1 failure)

| Test | Error Type |
|------|------------|
| `test_find_related_documents_excludes_original` | Mock configuration |

**Fix Required:** Update mock for `ExplanationService`.

## Recommended Fix Approach

1. **Audit Service Constructors:** Review current constructor signatures for:
   - `DraftService`
   - `SearchService`
   - `GenerationService`
   - `ExplanationService`

2. **Update Test Fixtures:** Create/update pytest fixtures that properly initialize services with mocked dependencies.

3. **Use Dependency Injection Patterns:** If services now use DI containers, update tests to mock at the container level.

4. **Consider Test Refactoring:** Some tests may need complete rewrites if service interfaces have significantly changed.

## Impact Assessment

- **Production Impact:** None - these are test-only issues
- **CI/CD Impact:** Unit tests currently skip or fail silently
- **Development Impact:** Reduced confidence in unit test coverage

## Acceptance Criteria for Resolution

- [ ] All 26 unit tests passing
- [ ] No new test failures introduced
- [ ] Mock patterns documented for future reference
- [ ] Test fixtures updated in `tests/unit/conftest.py`

## Related Files

- `backend/tests/unit/test_draft_service.py`
- `backend/tests/unit/test_search_service.py`
- `backend/tests/unit/test_generation_service.py`
- `backend/tests/unit/test_explanation_service.py`
- `backend/app/services/draft_service.py`
- `backend/app/services/search_service.py`
- `backend/app/services/generation_service.py`
- `backend/app/services/explanation_service.py`

## Notes

These failures were NOT introduced by Epic 4 or Story 5-15. They represent accumulated technical debt from service refactoring that occurred without corresponding test updates.
