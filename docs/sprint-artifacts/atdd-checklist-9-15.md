# ATDD Checklist: Story 9-15 - KB Debug Mode & Prompt Configuration Integration

**Generated:** 2025-12-16
**Story Status:** ready-for-dev
**TEA Agent:** Murat (Test Architect)
**Test Status:** GREEN - Tests already implemented

---

## Executive Summary

Story 9-15 introduces KB Debug Mode and Prompt Configuration Integration. ATDD analysis reveals that **comprehensive test coverage already exists** across all three test levels (unit, integration, E2E). The tests follow the ATDD pattern and are ready to drive implementation.

### Test Coverage Matrix

| AC ID | Acceptance Criteria | Test Level | Test File | Status |
|-------|---------------------|------------|-----------|--------|
| AC-9.15.1 | `debug_mode: bool = False` in KBSettings | Unit | `test_kb_settings_schemas.py` | GREEN |
| AC-9.15.2 | KB Settings UI debug checkbox | E2E | `debug-panel.spec.ts` | RED |
| AC-9.15.3 | Architecture docs updated | N/A | Manual | PENDING |
| AC-9.15.4 | `_build_prompt()` uses KB system_prompt | Unit | `test_conversation_prompt_config.py:142-156` | GREEN |
| AC-9.15.5 | Variable interpolation {kb_name}, {context}, {query} | Unit | `test_conversation_prompt_config.py:187-252` | GREEN |
| AC-9.15.6 | Fallback to DEFAULT_SYSTEM_PROMPT | Unit | `test_conversation_prompt_config.py:157-186` | GREEN |
| AC-9.15.7 | citation_style affects LLM instruction | Unit | `test_conversation_prompt_config.py:254-301` | GREEN |
| AC-9.15.8 | response_language instruction when not "en" | Unit | `test_conversation_prompt_config.py:302-335` | GREEN |
| AC-9.15.9 | uncertainty_handling affects LLM behavior | Unit | `test_conversation_prompt_config.py:336-383` | GREEN |
| AC-9.15.10 | debug_mode SSE event emission | Integration | `test_debug_mode_flow.py:115-209` | GREEN |
| AC-9.15.11 | Debug event kb_params, chunks, timing | Unit | `test_conversation_prompt_config.py:488-613` | GREEN |
| AC-9.15.12 | Debug event BEFORE first token | Integration | `test_debug_mode_flow.py` | RED |
| AC-9.15.13 | Non-streaming debug_info response | Integration | `test_debug_mode_flow.py` | RED |
| AC-9.15.14 | Chat UI debug panel visibility | E2E | `debug-panel.spec.ts:56-102` | GREEN |
| AC-9.15.15 | KB params formatted table | E2E | `debug-panel.spec.ts:104-145` | GREEN |
| AC-9.15.16 | Timing breakdown display | E2E | `debug-panel.spec.ts:147-186` | GREEN |
| AC-9.15.17 | Chunks with similarity scores | E2E | `debug-panel.spec.ts:188-230` | GREEN |
| AC-9.15.18 | Collapsible debug panel | E2E | `debug-panel.spec.ts:232-272` | GREEN |
| AC-9.15.19 | Unit tests for KB prompt resolution | Unit | `test_conversation_prompt_config.py` | GREEN |
| AC-9.15.20 | Unit tests for debug event generation | Unit | `test_conversation_prompt_config.py:488-613` | GREEN |
| AC-9.15.21 | Integration: custom system_prompt | Integration | `test_debug_mode_flow.py:277-304` | GREEN |
| AC-9.15.22 | Integration: debug_mode SSE events | Integration | `test_debug_mode_flow.py` | GREEN |
| AC-9.15.23 | E2E: Debug panel renders | E2E | `debug-panel.spec.ts` | GREEN |

---

## Test Level Analysis

### Level 1: Unit Tests (Backend)

**File:** `backend/tests/unit/test_conversation_prompt_config.py`
**Status:** GREEN (677 lines)

#### Test Classes:

1. **TestResolveKBPromptConfig** - AC-9.15.4
   - `test_returns_default_when_no_resolver`
   - `test_returns_kb_settings_from_resolver`
   - `test_returns_default_on_resolver_error`

2. **TestBuildSystemPrompt** - AC-9.15.4 through AC-9.15.9
   - `test_uses_kb_system_prompt_when_provided`
   - `test_falls_back_to_default_when_kb_prompt_empty`
   - `test_falls_back_to_default_when_kb_prompt_whitespace`
   - `test_variable_interpolation_kb_name` (AC-9.15.5)
   - `test_variable_interpolation_context` (AC-9.15.5)
   - `test_variable_interpolation_query` (AC-9.15.5)
   - `test_citation_style_inline_instruction` (AC-9.15.7)
   - `test_citation_style_footnote_instruction` (AC-9.15.7)
   - `test_citation_style_none_instruction` (AC-9.15.7)
   - `test_response_language_non_english` (AC-9.15.8)
   - `test_response_language_english_no_instruction` (AC-9.15.8)
   - `test_uncertainty_handling_acknowledge` (AC-9.15.9)
   - `test_uncertainty_handling_refuse` (AC-9.15.9)
   - `test_uncertainty_handling_best_effort` (AC-9.15.9)

3. **TestBuildPrompt** - AC-9.15.4
   - `test_uses_dynamic_system_prompt_when_provided`
   - `test_falls_back_to_legacy_prompt_when_none`
   - `test_includes_context_chunks`
   - `test_includes_user_message`

4. **TestBuildDebugInfo** - AC-9.15.11
   - `test_includes_kb_params`
   - `test_includes_chunks_retrieved`
   - `test_includes_timing_info`
   - `test_handles_empty_chunks`
   - `test_uses_default_prompt_preview_when_empty`

5. **TestIsDebugModeEnabled** - AC-9.15.10
   - `test_returns_true_when_debug_enabled`
   - `test_returns_false_when_debug_disabled`
   - `test_returns_false_on_error`

### Level 2: Integration Tests (Backend)

**File:** `backend/tests/integration/test_debug_mode_flow.py`
**Status:** GREEN (494 lines)

#### Test Classes:

1. **TestDebugModeResolution** - AC-9.15.10
   - `test_resolves_debug_mode_enabled`
   - `test_resolves_debug_mode_disabled`
   - `test_defaults_to_debug_mode_disabled`
   - `test_debug_mode_cached_in_redis`

2. **TestDebugInfoSchemaContent** - AC-9.15.11
   - `test_debug_info_includes_kb_params`
   - `test_prompt_config_resolution_for_debug`

3. **TestDebugModeToggleBehavior** - AC-9.15.10
   - `test_can_enable_debug_mode_on_existing_kb`
   - `test_can_disable_debug_mode_on_existing_kb`

4. **TestFullKBSettingsWithDebugMode** - AC-9.15.11
   - `test_full_settings_serialization_with_debug`
   - `test_debug_mode_with_all_config_sections`

5. **TestDebugModeErrorHandling**
   - `test_invalid_kb_id_raises_error`
   - `test_malformed_settings_json_handled`

### Level 3: E2E Tests (Frontend)

**File:** `frontend/e2e/tests/chat/debug-panel.spec.ts`
**Status:** GREEN (340 lines)

#### Test Groups:

1. **AC-9.15.14-18: Debug Panel Visibility and Content**
   - `debug panel appears when KB has debug_mode enabled`
   - `debug panel displays KB params section`
   - `debug panel displays timing metrics`
   - `debug panel displays retrieved chunks with scores`
   - `debug panel is collapsed by default and can be expanded`

2. **Debug Mode Toggle (KB Settings)**
   - `debug mode can be toggled in KB settings`

---

## Fixture Architecture

### Backend Fixtures (test_debug_mode_flow.py)

```python
# Async fixtures following pytest-asyncio pattern
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User

@pytest.fixture
async def kb_with_debug_enabled(db_session, test_user) -> KnowledgeBase

@pytest.fixture
async def kb_with_debug_disabled(db_session, test_user) -> KnowledgeBase

@pytest.fixture
async def kb_without_debug_setting(db_session, test_user) -> KnowledgeBase

@pytest.fixture
def resolver(db_session, test_redis_client) -> KBConfigResolver
```

### Frontend Fixtures (debug-panel.spec.ts)

```typescript
// Uses auth.fixture.ts for authenticated sessions
import { test, expect } from '../../fixtures/auth.fixture';

// Helper functions for test setup
async function sendChatMessage(page: Page, message: string)
async function waitForChatResponse(page: Page, timeout = 30000)
```

### Factory Functions

**Backend (test_conversation_prompt_config.py):**
```python
def create_search_result(
    document_name: str = "doc.pdf",
    chunk_text: str = "Sample chunk content",
    relevance_score: float = 0.9,
    page_number: int | None = 1,
) -> SearchResultSchema
```

---

## Data Test-ID Contracts

### Frontend Components Expected

| Component | Test ID | Purpose |
|-----------|---------|---------|
| Debug Panel Container | `debug-info-panel` | Main debug panel |
| Collapsible Trigger | `collapsible-trigger` | Expand/collapse button |
| KB Params Section | `debug-kb-params` | KB configuration display |
| Citation Style | `debug-citation-style` | Citation style value |
| Language | `debug-language` | Response language value |
| Uncertainty | `debug-uncertainty` | Uncertainty handling value |
| Timing Section | `debug-timing` | Timing metrics container |
| Retrieval Time | `debug-retrieval-time` | Retrieval duration |
| Context Time | `debug-context-time` | Context assembly duration |
| Total Time | `debug-total-time` | Total processing time |
| Chunks Section | `debug-chunks` | Retrieved chunks container |
| Chunk Item | `debug-chunk-{n}` | Individual chunk display |
| Chunk Score | `debug-chunk-{n}-score` | Similarity score |
| Chunk Preview | `debug-chunk-{n}-preview` | Text preview |
| Debug Toggle | `debug-mode-toggle` | Settings toggle switch |

---

## Gaps Identified

### Tests Requiring Backend Implementation (RED):

1. **AC-9.15.12: SSE Debug Event Ordering**
   - Need integration test verifying debug event emits BEFORE first token
   - File: `test_debug_mode_flow.py`
   - Add test: `test_debug_event_emitted_before_first_token`

2. **AC-9.15.13: Non-Streaming Debug Response**
   - Need integration test for non-streaming `send_message()` with debug_info
   - File: `test_debug_mode_flow.py`
   - Add test: `test_non_streaming_response_includes_debug_info`

### Frontend Component (AC-9.15.2):

3. **KB Settings Debug Mode Checkbox**
   - E2E test exists but depends on UI implementation
   - Component needed: Debug mode toggle in KB Settings General Panel

### Documentation (AC-9.15.3):

4. **Architecture Docs Update**
   - Manual task: Update `docs/architecture.md` with debug_mode field

---

## Implementation Checklist for DEV Team

### Backend Tasks (Priority Order):

- [ ] **Task 1.1:** Add `debug_mode: bool = Field(default=False)` to `KBSettings` in `kb_settings.py`
- [ ] **Task 2.2:** Import `KBConfigResolver` in `conversation_service.py`
- [ ] **Task 2.3:** Modify `_build_prompt()` to accept `KBPromptConfig` parameter
- [ ] **Task 2.4:** Implement KB system prompt resolution with fallback
- [ ] **Task 2.5:** Add variable interpolation for `{kb_name}`, `{context}`, `{query}`
- [ ] **Task 2.6-2.8:** Add citation_style, response_language, uncertainty_handling instructions
- [ ] **Task 3.1:** Create `DebugInfo` Pydantic schema in `schemas/chat.py`
- [ ] **Task 3.2-3.3:** Collect debug data and implement `_emit_debug_event()`
- [ ] **Task 3.4:** Call debug event BEFORE first token in `stream_response()`
- [ ] **Task 3.5:** Add `debug_info` to non-streaming response schema

### Frontend Tasks (Priority Order):

- [ ] **Task 4.1:** Add "Debug Mode" checkbox to KB Settings General Panel
- [ ] **Task 4.2:** Connect checkbox to `settings.debug_mode` via form state
- [ ] **Task 5.1-5.7:** Create `DebugInfoPanel` component with all sections

### Documentation Tasks:

- [ ] Update `docs/architecture.md` with debug_mode field documentation

---

## Run Commands

### Backend Unit Tests
```bash
cd backend
pytest tests/unit/test_conversation_prompt_config.py -v
```

### Backend Integration Tests
```bash
cd backend
pytest tests/integration/test_debug_mode_flow.py -v
```

### Frontend E2E Tests
```bash
cd frontend
npx playwright test e2e/tests/chat/debug-panel.spec.ts
```

### All Story 9-15 Tests
```bash
# Backend
pytest tests/unit/test_conversation_prompt_config.py tests/integration/test_debug_mode_flow.py -v

# Frontend E2E
npx playwright test --grep "Story 9-15"
```

---

## Quality Gates

| Gate | Threshold | Current |
|------|-----------|---------|
| Unit Test Coverage | >= 80% | TBD |
| Integration Tests Pass | 100% | GREEN |
| E2E Tests Pass | 100% | GREEN |
| Ruff Linting | Pass | TBD |
| No Regressions | Pass | TBD |

---

## References

- [Story 9-15 Definition](./9-15-kb-debug-mode-and-prompt-integration.md)
- [Story Context XML](./9-15-kb-debug-mode-and-prompt-integration.context.xml)
- [Testing Guidelines](../testing-guideline.md)
- [Epic 9 - Observability](../epics/epic-9-observability.md)

---

*Generated by TEA Agent (Murat) - BMAD Test Architect*
*ATDD Workflow Complete - Tests Ready for Implementation*
