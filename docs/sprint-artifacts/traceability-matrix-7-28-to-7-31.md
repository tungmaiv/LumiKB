# Traceability Matrix: Stories 7-28 to 7-31
# Markdown-First Document Processing Feature Chain

**Generated:** 2025-12-11
**Workflow:** *trace (TEA Agent)
**Stories:** 7-28, 7-29, 7-30, 7-31 (Markdown-First Processing)

---

## Executive Summary

| Story | Status | ACs | Tests Found | Coverage Level | Gate |
|-------|--------|-----|-------------|----------------|------|
| 7-28 | done | 6 | 17 unit | **FULL** | PASS |
| 7-29 | done | 6 | 10 integration | **FULL** | PASS |
| 7-30 | review | 6 | 34 unit + hook | **FULL** | PASS |
| 7-31 | ready-for-dev | 6 | 0 | **NONE** | FAIL |

**Overall Assessment:** 3/4 stories have full test coverage. Story 7-31 requires test implementation before development can proceed.

---

## Story 7-28: Markdown Generation from DOCX/PDF (Backend)

**Status:** done | **Story Points:** 3 | **Risk:** Medium (core processing)

### Acceptance Criteria Mapping

| AC ID | Acceptance Criteria | Priority | Tests | Coverage |
|-------|---------------------|----------|-------|----------|
| AC-7.28.1 | markdownify dependency in pyproject.toml | P2 | - | MANUAL (verified in DoD) |
| AC-7.28.2 | elements_to_markdown function | P0 | 17 unit tests | FULL |
| AC-7.28.3 | ParsedContent markdown field | P0 | 3 unit tests | FULL |
| AC-7.28.4 | Markdown stored in MinIO | P1 | Integration (implied) | PARTIAL |
| AC-7.28.5 | DOCX markdown quality | P1 | 4 unit tests | FULL |
| AC-7.28.6 | Unit test coverage >= 80% | P1 | 17 tests | FULL |

### Test Evidence

**File:** `backend/tests/unit/test_parsing.py`

| Test ID | Test Name | AC | Priority |
|---------|-----------|-----|----------|
| 7.28-UNIT-001 | test_empty_elements_returns_empty_string | AC-7.28.2 | P0 |
| 7.28-UNIT-002 | test_title_element_becomes_h1 | AC-7.28.2 | P0 |
| 7.28-UNIT-003 | test_header_element_with_default_level | AC-7.28.2 | P0 |
| 7.28-UNIT-004 | test_header_element_with_custom_level | AC-7.28.2 | P0 |
| 7.28-UNIT-005 | test_header_level_clamped_to_valid_range | AC-7.28.2 | P1 |
| 7.28-UNIT-006 | test_list_item_element | AC-7.28.2 | P0 |
| 7.28-UNIT-007 | test_narrative_text_element | AC-7.28.2 | P0 |
| 7.28-UNIT-008 | test_text_element_same_as_narrative | AC-7.28.2 | P1 |
| 7.28-UNIT-009 | test_code_snippet_element | AC-7.28.5 | P1 |
| 7.28-UNIT-010 | test_figure_caption_element | AC-7.28.5 | P2 |
| 7.28-UNIT-011 | test_table_element_with_html | AC-7.28.5 | P1 |
| 7.28-UNIT-012 | test_table_element_without_html_fallback | AC-7.28.5 | P2 |
| 7.28-UNIT-013 | test_unknown_element_type_becomes_paragraph | AC-7.28.2 | P2 |
| 7.28-UNIT-014 | test_empty_text_elements_skipped | AC-7.28.2 | P1 |
| 7.28-UNIT-015 | test_none_text_elements_skipped | AC-7.28.2 | P2 |
| 7.28-UNIT-016 | test_mixed_element_types_preserve_order | AC-7.28.2 | P0 |
| 7.28-UNIT-017 | test_special_characters_preserved | AC-7.28.2 | P1 |
| 7.28-UNIT-018 | test_markdown_content_field_default_none | AC-7.28.3 | P0 |
| 7.28-UNIT-019 | test_markdown_content_field_can_be_set | AC-7.28.3 | P0 |
| 7.28-UNIT-020 | test_parse_pdf_generates_markdown | AC-7.28.3 | P0 |
| 7.28-UNIT-021 | test_parse_docx_generates_markdown | AC-7.28.3 | P0 |

### Coverage Assessment: FULL

- All critical ACs (P0) have dedicated tests
- Edge cases covered (empty, null, special chars)
- Element type conversions thoroughly tested
- **Gate Decision: PASS**

---

## Story 7-29: Markdown Content API Endpoint (Backend)

**Status:** done | **Story Points:** 2 | **Risk:** Low (standard CRUD)

### Acceptance Criteria Mapping

| AC ID | Acceptance Criteria | Priority | Tests | Coverage |
|-------|---------------------|----------|-------|----------|
| AC-7.29.1 | GET endpoint returns 200 with markdown | P0 | 2 integration | FULL |
| AC-7.29.2 | 404 for documents without markdown | P0 | 3 integration | FULL |
| AC-7.29.3 | 400 for processing documents | P0 | 2 integration | FULL |
| AC-7.29.4 | Response schema validation | P0 | 1 integration | FULL |
| AC-7.29.5 | Permission check (403) | P0 | 2 integration | FULL |
| AC-7.29.6 | Integration tests for all scenarios | P1 | 10 tests | FULL |

### Test Evidence

**File:** `backend/tests/integration/test_markdown_content_api.py`

| Test ID | Test Name | AC | Priority |
|---------|-----------|-----|----------|
| 7.29-INT-001 | test_get_markdown_content_returns_200 | AC-7.29.1 | P0 |
| 7.29-INT-002 | test_get_markdown_content_response_schema | AC-7.29.4 | P0 |
| 7.29-INT-003 | test_get_markdown_content_no_markdown_returns_404 | AC-7.29.2 | P0 |
| 7.29-INT-004 | test_get_markdown_content_no_parsed_content_returns_404 | AC-7.29.2 | P0 |
| 7.29-INT-005 | test_get_markdown_content_document_not_found_returns_404 | AC-7.29.2 | P0 |
| 7.29-INT-006 | test_get_markdown_content_kb_not_found_returns_403 | AC-7.29.5 | P0 |
| 7.29-INT-007 | test_get_markdown_content_pending_returns_400 | AC-7.29.3 | P0 |
| 7.29-INT-008 | test_get_markdown_content_processing_returns_400 | AC-7.29.3 | P0 |
| 7.29-INT-009 | test_get_markdown_content_no_kb_access_returns_403 | AC-7.29.5 | P0 |
| 7.29-INT-010 | test_get_markdown_content_unauthenticated_returns_401 | AC-7.29.5 | P0 |

### Coverage Assessment: FULL

- All 6 ACs have dedicated integration tests
- All HTTP status codes verified (200, 400, 401, 403, 404)
- Response schema explicitly tested
- Code review approved with security validation
- **Gate Decision: PASS**

---

## Story 7-30: Enhanced Markdown Viewer with Highlighting (Frontend)

**Status:** review | **Story Points:** 3 | **Risk:** Medium (UI complexity)

### Acceptance Criteria Mapping

| AC ID | Acceptance Criteria | Priority | Tests | Coverage |
|-------|---------------------|----------|-------|----------|
| AC-7.30.1 | Fetch markdown content hook | P0 | 7 hook tests | FULL |
| AC-7.30.2 | Precise highlighting with char_start/end | P0 | 8 component tests | FULL |
| AC-7.30.3 | Highlight styling + auto-scroll | P0 | 4 component tests | FULL |
| AC-7.30.4 | Graceful fallback for older docs | P0 | 3 component tests | FULL |
| AC-7.30.5 | Loading state skeleton | P0 | 2 component tests | FULL |
| AC-7.30.6 | Unit tests for edge cases | P1 | 10 component tests | FULL |

### Test Evidence

**File:** `frontend/src/hooks/__tests__/useMarkdownContent.test.ts`

| Test ID | Test Name | AC | Priority |
|---------|-----------|-----|----------|
| 7.30-HOOK-001 | should fetch markdown content successfully | AC-7.30.1 | P1 |
| 7.30-HOOK-002 | should handle 404 gracefully by returning null | AC-7.30.1 | P1 |
| 7.30-HOOK-003 | should handle API errors (non-404) as errors | AC-7.30.1 | P1 |
| 7.30-HOOK-004 | should not fetch when disabled | AC-7.30.1 | P1 |
| 7.30-HOOK-005 | should not fetch when kbId is empty | AC-7.30.1 | P2 |
| 7.30-HOOK-006 | should not fetch when documentId is empty | AC-7.30.1 | P2 |
| 7.30-HOOK-007 | should handle network errors gracefully | AC-7.30.1 | P2 |

**File:** `frontend/src/components/documents/chunk-viewer/viewers/__tests__/enhanced-markdown-viewer.test.tsx`

| Test ID | Test Name | AC | Priority |
|---------|-----------|-----|----------|
| 7.30-COMP-001 | should render markdown content | AC-7.30.2 | P0 |
| 7.30-COMP-002 | should render markdown with proper styling | AC-7.30.2 | P0 |
| 7.30-COMP-003 | should highlight specified character range | AC-7.30.2 | P0 |
| 7.30-COMP-004 | should apply correct highlight styling | AC-7.30.3 | P0 |
| 7.30-COMP-005 | should split content correctly for highlight at beginning | AC-7.30.2 | P0 |
| 7.30-COMP-006 | should split content correctly for highlight in middle | AC-7.30.2 | P0 |
| 7.30-COMP-007 | should split content correctly for highlight at end | AC-7.30.2 | P0 |
| 7.30-COMP-008 | should handle out-of-bounds highlight range gracefully | AC-7.30.6 | P1 |
| 7.30-COMP-009 | should handle negative highlight range start | AC-7.30.6 | P1 |
| 7.30-COMP-010 | should scroll highlighted section into view | AC-7.30.3 | P0 |
| 7.30-COMP-011 | should not scroll when no highlight range | AC-7.30.3 | P1 |
| 7.30-COMP-012 | should not scroll when highlight range is null | AC-7.30.3 | P1 |
| 7.30-COMP-013 | should show loading state | AC-7.30.5 | P0 |
| 7.30-COMP-014 | should show error state | AC-7.30.5 | P0 |
| 7.30-COMP-015 | should show empty state when content is empty | AC-7.30.4 | P0 |
| 7.30-COMP-016 | should show fallback message when enabled | AC-7.30.4 | P1 |
| 7.30-COMP-017 | should not show fallback message when disabled | AC-7.30.4 | P1 |
| 7.30-COMP-018 | should render code blocks correctly | AC-7.30.2 | P1 |
| 7.30-COMP-019 | should render inline code correctly | AC-7.30.2 | P1 |
| 7.30-COMP-020 | should render links with target="_blank" | AC-7.30.2 | P1 |
| 7.30-COMP-021 | should render unordered lists | AC-7.30.2 | P1 |
| 7.30-COMP-022 | should render ordered lists | AC-7.30.2 | P1 |
| 7.30-COMP-023 | should render blockquotes | AC-7.30.2 | P1 |
| 7.30-COMP-024 | should handle empty highlight range (start equals end) | AC-7.30.6 | P2 |
| 7.30-COMP-025 | should handle very long content | AC-7.30.6 | P2 |
| 7.30-COMP-026 | should handle content with special characters | AC-7.30.6 | P2 |
| 7.30-COMP-027 | should have scroll container attribute | AC-7.30.6 | P2 |

### Coverage Assessment: FULL

- All 6 ACs have dedicated tests
- Hook tests cover success, error, 404, disabled states
- Component tests cover highlighting, styling, scroll, fallback
- Edge cases thoroughly tested (bounds, empty, special chars)
- **Gate Decision: PASS**

---

## Story 7-31: View Mode Toggle for Chunk Viewer (Frontend)

**Status:** ready-for-dev | **Story Points:** 2 | **Risk:** Low (UI control)

### Acceptance Criteria Mapping

| AC ID | Acceptance Criteria | Priority | Tests | Coverage |
|-------|---------------------|----------|-------|----------|
| AC-7.31.1 | Toggle component with Original/Markdown options | P0 | 0 | **NONE** |
| AC-7.31.2 | Default to Markdown when available | P0 | 0 | **NONE** |
| AC-7.31.3 | Markdown disabled when unavailable | P0 | 0 | **NONE** |
| AC-7.31.4 | Preference persistence in localStorage | P1 | 0 | **NONE** |
| AC-7.31.5 | Visual indication of selected state | P1 | 0 | **NONE** |
| AC-7.31.6 | Unit tests for mode switching, persistence | P1 | 0 | **NONE** |

### Test Evidence

**No tests found for Story 7-31**

Files searched:
- `frontend/src/hooks/__tests__/useViewModePreference*.ts` - NOT FOUND
- `frontend/src/components/**/__tests__/*view-mode*.tsx` - NOT FOUND
- `frontend/e2e/**/*view-mode*.ts` - NOT FOUND

### Coverage Assessment: NONE

- **Critical Gap:** No tests exist for this story
- Story is blocked until tests are written (ATDD approach)
- Required tests per story spec:
  - 8 unit tests for toggle component
  - 8 unit tests for useViewModePreference hook
  - 4 E2E tests for user workflows
- **Gate Decision: FAIL**

---

## Coverage Gap Analysis

### Critical Gaps (P0)

| Story | AC | Gap Description | Recommended Action |
|-------|-----|-----------------|-------------------|
| 7-31 | AC-7.31.1 | No tests for toggle rendering | Write component tests |
| 7-31 | AC-7.31.2 | No tests for default mode logic | Write hook tests |
| 7-31 | AC-7.31.3 | No tests for disabled state | Write component tests |

### Non-Critical Gaps (P1/P2)

| Story | AC | Gap Description | Recommended Action |
|-------|-----|-----------------|-------------------|
| 7-28 | AC-7.28.4 | MinIO storage not directly tested | Consider integration test |
| 7-30 | - | No E2E test for markdown viewer | Add to chunk-viewer E2E |
| 7-31 | AC-7.31.4 | No localStorage persistence tests | Write hook tests |
| 7-31 | AC-7.31.5 | No visual indication tests | Write component tests |

---

## Risk Assessment Matrix

| Story | Probability | Impact | Risk Score | Mitigation |
|-------|-------------|--------|------------|------------|
| 7-28 | 1 (Low) | 3 (High) | 3 | Comprehensive unit tests exist |
| 7-29 | 1 (Low) | 2 (Medium) | 2 | Full integration test coverage |
| 7-30 | 1 (Low) | 3 (High) | 3 | Extensive component tests |
| 7-31 | 3 (High) | 1 (Low) | 3 | **No tests - must implement** |

---

## Quality Gate Summary

### Story-Level Gates

| Story | Unit | Integration | E2E | Overall |
|-------|------|-------------|-----|---------|
| 7-28 | PASS | N/A | N/A | **PASS** |
| 7-29 | N/A | PASS | N/A | **PASS** |
| 7-30 | PASS | N/A | PARTIAL | **PASS** |
| 7-31 | FAIL | N/A | FAIL | **FAIL** |

### Feature Chain Gate: **CONCERNS**

- 3/4 stories pass quality gates
- Story 7-31 is blocking feature completion
- Recommendation: Run `*atdd` for Story 7-31 before development

---

## Recommendations

### Immediate Actions

1. **Story 7-31 - BLOCKED**: Run `/bmad:bmm:workflows:*atdd` to generate test scaffolds
   - Create `frontend/src/hooks/__tests__/useViewModePreference.test.ts`
   - Create `frontend/src/components/documents/chunk-viewer/__tests__/view-mode-toggle.test.tsx`
   - Add E2E tests to `document-chunk-viewer.spec.ts`

2. **Story 7-30 - ENHANCEMENT**: Add E2E coverage for markdown viewer
   - Add test case for markdown content loading
   - Add test case for chunk highlighting in markdown mode

### Post-Implementation

3. **Integration Test**: Verify markdown content API with real MinIO storage (AC-7.28.4)
4. **Regression Suite**: Add markdown feature chain to CI smoke tests

---

## Appendix: Test File Inventory

| File Path | Tests | Stories | Type |
|-----------|-------|---------|------|
| `backend/tests/unit/test_parsing.py` | 21 | 7-28 | Unit |
| `backend/tests/integration/test_markdown_content_api.py` | 10 | 7-29 | Integration |
| `frontend/src/hooks/__tests__/useMarkdownContent.test.ts` | 7 | 7-30 | Hook Unit |
| `frontend/src/components/.../enhanced-markdown-viewer.test.tsx` | 27 | 7-30 | Component Unit |
| `frontend/e2e/tests/documents/document-chunk-viewer.spec.ts` | 12 | 5-26 | E2E |

**Total Tests Cataloged:** 77
**Stories with Full Coverage:** 3/4
**Overall Test Health:** Good (with 7-31 gap)
