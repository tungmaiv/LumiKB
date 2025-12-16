# Story 7.12: KB Settings Schema & Pydantic Models

## Status: done

## Story
As a developer, I want typed Pydantic schemas for KB-level configuration so that settings are validated at runtime and type-safe throughout the codebase.

## Acceptance Criteria

- [x] **AC-7.12.1:** ChunkingConfig schema with strategy enum (fixed/recursive/semantic), chunk_size (100-2000), chunk_overlap (0-500), separators (list[str])
- [x] **AC-7.12.2:** RetrievalConfig schema with top_k (1-100), similarity_threshold (0.0-1.0), method enum (vector/hybrid/hyde), mmr_enabled (bool), mmr_lambda (0.0-1.0), hybrid_alpha (0.0-1.0)
- [x] **AC-7.12.3:** RerankingConfig schema with enabled (bool), model (optional str), top_n (1-50)
- [x] **AC-7.12.4:** GenerationConfig schema with temperature (0.0-2.0), top_p (0.0-1.0), top_k (1-100), max_tokens (100-16000), frequency_penalty (-2.0-2.0), presence_penalty (-2.0-2.0), stop_sequences (list[str])
- [x] **AC-7.12.5:** NERConfig schema with enabled (bool), confidence_threshold (0.0-1.0), entity_types (list[str]), batch_size (1-100)
- [x] **AC-7.12.6:** DocumentProcessingConfig schema with ocr_enabled (bool), language_detection (bool), table_extraction (bool), image_extraction (bool)
- [x] **AC-7.12.7:** KBPromptConfig schema with system_prompt (str, max 4000 chars), context_template (str), citation_style enum (inline/footnote/none), uncertainty_handling enum (acknowledge/refuse/best_effort), response_language (str)
- [x] **AC-7.12.8:** EmbeddingConfig schema with model_id (UUID, optional), batch_size (1-100), normalize (bool), truncation enum (start/end/none), max_length (128-16384), prefix_document (str, max 100 chars), prefix_query (str, max 100 chars), pooling_strategy enum (mean/cls/max/last)
- [x] **AC-7.12.9:** KBSettings composite schema aggregating all sub-configs (including EmbeddingConfig) with default factories and preset field for quick configuration
- [x] **AC-7.12.10:** Backwards compatibility - existing KBs with empty {} settings parse with all defaults applied without errors
- [x] **AC-7.12.11:** Re-indexing trigger detection - EmbeddingConfig changes (model_id, normalize, prefix_document, prefix_query, pooling_strategy) flag re-indexing required and return warning to user

## Tasks

### Task 1: Create Enum Types (AC: #1, #2, #7, #8)
- [x] 1.1 Create `backend/app/schemas/kb_settings.py` file
- [x] 1.2 Implement ChunkingStrategy enum (fixed, recursive, semantic)
- [x] 1.3 Implement RetrievalMethod enum (vector, hybrid, hyde)
- [x] 1.4 Implement CitationStyle enum (inline, footnote, none)
- [x] 1.5 Implement UncertaintyHandling enum (acknowledge, refuse, best_effort)
- [x] 1.6 Implement TruncationStrategy enum (start, end, none)
- [x] 1.7 Implement PoolingStrategy enum (mean, cls, max, last)

### Task 2: Create Sub-Config Schemas (AC: #1-8)
- [x] 2.1 Implement ChunkingConfig with strategy, chunk_size (100-2000), chunk_overlap (0-500), separators (list[str])
- [x] 2.2 Implement RetrievalConfig with top_k (1-100), similarity_threshold (0.0-1.0), method, mmr_enabled, mmr_lambda (0.0-1.0), hybrid_alpha (0.0-1.0)
- [x] 2.3 Implement RerankingConfig with enabled, model (optional), top_n (1-50)
- [x] 2.4 Implement GenerationConfig with temperature (0.0-2.0), top_p (0.0-1.0), top_k (1-100), max_tokens (100-16000), frequency_penalty (-2.0-2.0), presence_penalty (-2.0-2.0), stop_sequences
- [x] 2.5 Implement NERConfig with enabled, confidence_threshold (0.0-1.0), entity_types, batch_size (1-100)
- [x] 2.6 Implement DocumentProcessingConfig with ocr_enabled, language_detection, table_extraction, image_extraction
- [x] 2.7 Implement KBPromptConfig with system_prompt (max 4000), context_template, citation_style, uncertainty_handling, response_language
- [x] 2.8 Implement EmbeddingConfig with model_id (UUID optional), batch_size (1-100), normalize, truncation, max_length (128-16384), prefix_document (max 100), prefix_query (max 100), pooling_strategy

### Task 3: Create Composite KBSettings Schema (AC: #9-10)
- [x] 3.1 Create KBSettings aggregating all sub-configs with Optional fields and default_factory
- [x] 3.2 Add preset field (optional str) for quick configuration
- [x] 3.3 Configure model_config for JSON serialization
- [x] 3.4 Test backwards compatibility - empty {} parses without errors
- [x] 3.5 Verify all defaults are sensible for production use

### Task 4: Implement Re-indexing Detection Logic (AC: #11)
- [x] 4.1 Add `requires_reindex(previous: Optional[EmbeddingConfig])` method to EmbeddingConfig
- [x] 4.2 Implement comparison for: model_id, normalize, prefix_document, prefix_query, pooling_strategy
- [x] 4.3 Add `get_reindex_warning()` method returning user-friendly warning message
- [x] 4.4 Add `detect_reindex_fields(previous: Optional[EmbeddingConfig])` returning list of changed fields

### Task 5: Unit Tests - Enum Types (AC: #1, #2, #7, #8)
- [x] 5.1 Create `backend/tests/unit/test_kb_settings_schemas.py`
- [x] 5.2 Test all enum types have correct values
- [x] 5.3 Test enum JSON serialization/deserialization

### Task 6: Unit Tests - Sub-Config Validation (AC: #1-8)
- [x] 6.1 Test ChunkingConfig valid ranges (chunk_size 100-2000, chunk_overlap 0-500)
- [x] 6.2 Test ChunkingConfig invalid values raise ValidationError
- [x] 6.3 Test ChunkingConfig separators as list[str]
- [x] 6.4 Test RetrievalConfig valid ranges (top_k 1-100, similarity 0.0-1.0, mmr_lambda 0.0-1.0, hybrid_alpha 0.0-1.0)
- [x] 6.5 Test RetrievalConfig invalid values raise ValidationError
- [x] 6.6 Test RerankingConfig validation (top_n 1-50)
- [x] 6.7 Test GenerationConfig valid ranges (temperature 0.0-2.0, top_p 0.0-1.0, top_k 1-100, max_tokens 100-16000, frequency_penalty -2.0-2.0, presence_penalty -2.0-2.0)
- [x] 6.8 Test GenerationConfig invalid values raise ValidationError
- [x] 6.9 Test NERConfig validation (confidence_threshold 0.0-1.0, batch_size 1-100)
- [x] 6.10 Test DocumentProcessingConfig all booleans default correctly
- [x] 6.11 Test KBPromptConfig system_prompt max 4000 chars enforced
- [x] 6.12 Test KBPromptConfig prefix fields max 100 chars enforced
- [x] 6.13 Test EmbeddingConfig valid ranges (batch_size 1-100, max_length 128-16384)
- [x] 6.14 Test EmbeddingConfig model_id accepts UUID or None

### Task 7: Unit Tests - KBSettings Composite (AC: #9-10)
- [x] 7.1 Test KBSettings instantiation with all defaults
- [x] 7.2 Test KBSettings instantiation with partial overrides
- [x] 7.3 Test KBSettings preset field accepts string
- [x] 7.4 Test backwards compatibility: KBSettings.model_validate({}) succeeds
- [x] 7.5 Test KBSettings JSON round-trip (model_dump → model_validate)

### Task 8: Unit Tests - Re-indexing Detection (AC: #11)
- [x] 8.1 Test requires_reindex returns False when no previous config
- [x] 8.2 Test requires_reindex returns False when no re-index fields changed
- [x] 8.3 Test requires_reindex returns True when model_id changes
- [x] 8.4 Test requires_reindex returns True when normalize changes
- [x] 8.5 Test requires_reindex returns True when prefix_document changes
- [x] 8.6 Test requires_reindex returns True when prefix_query changes
- [x] 8.7 Test requires_reindex returns True when pooling_strategy changes
- [x] 8.8 Test detect_reindex_fields returns correct field list
- [x] 8.9 Test get_reindex_warning returns user-friendly message

### Task 9: Export and Integration (AC: #9)
- [x] 9.1 Export all schemas from `backend/app/schemas/__init__.py`
- [x] 9.2 Verify import compatibility with existing KB schemas
- [x] 9.3 Run ruff linting and fix any issues
- [x] 9.4 Run all unit tests and verify pass

## Dev Notes

### Architecture Patterns and Constraints

**Pydantic v2 Schema Pattern:**
Use Field validators with `ge`, `le`, `gt`, `lt` for range constraints. Use `max_length` for string limits. Follow existing schema patterns in `backend/app/schemas/`.

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from enum import Enum

class ChunkingStrategy(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"

class RetrievalMethod(str, Enum):
    VECTOR = "vector"
    HYBRID = "hybrid"
    HYDE = "hyde"

class CitationStyle(str, Enum):
    INLINE = "inline"
    FOOTNOTE = "footnote"
    NONE = "none"

class UncertaintyHandling(str, Enum):
    ACKNOWLEDGE = "acknowledge"
    REFUSE = "refuse"
    BEST_EFFORT = "best_effort"

class TruncationStrategy(str, Enum):
    START = "start"
    END = "end"
    NONE = "none"

class PoolingStrategy(str, Enum):
    MEAN = "mean"
    CLS = "cls"
    MAX = "max"
    LAST = "last"

class ChunkingConfig(BaseModel):
    strategy: ChunkingStrategy = Field(default=ChunkingStrategy.RECURSIVE)
    chunk_size: int = Field(default=512, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    separators: list[str] = Field(default_factory=lambda: ["\n\n", "\n", " ", ""])

    model_config = {"extra": "forbid"}

class EmbeddingConfig(BaseModel):
    model_id: Optional[UUID] = Field(default=None)
    batch_size: int = Field(default=32, ge=1, le=100)
    normalize: bool = Field(default=True)
    truncation: TruncationStrategy = Field(default=TruncationStrategy.END)
    max_length: int = Field(default=512, ge=128, le=16384)
    prefix_document: str = Field(default="", max_length=100)
    prefix_query: str = Field(default="", max_length=100)
    pooling_strategy: PoolingStrategy = Field(default=PoolingStrategy.MEAN)

    model_config = {"extra": "forbid"}

    # Re-indexing fields that invalidate existing vectors
    REINDEX_FIELDS = {"model_id", "normalize", "prefix_document", "prefix_query", "pooling_strategy"}

    def requires_reindex(self, previous: Optional["EmbeddingConfig"]) -> bool:
        if previous is None:
            return False
        for field in self.REINDEX_FIELDS:
            if getattr(self, field) != getattr(previous, field):
                return True
        return False

    def detect_reindex_fields(self, previous: Optional["EmbeddingConfig"]) -> list[str]:
        if previous is None:
            return []
        return [f for f in self.REINDEX_FIELDS if getattr(self, f) != getattr(previous, f)]

    def get_reindex_warning(self, changed_fields: list[str]) -> str:
        if not changed_fields:
            return ""
        return f"Changing {', '.join(changed_fields)} requires re-indexing all documents in this KB."
```

**Three-Layer Precedence (for Story 7.13):**
Request params → KB settings → System defaults. KBSettings stores only overrides (sparse storage).

**JSONB Storage Pattern:**
The KB model will store settings as JSONB. Empty `{}` means "use all system defaults". Only non-default values are persisted.

**Preset Field:**
The `preset` field in KBSettings enables quick configuration via Story 7.16. It stores the preset name used (e.g., "legal", "technical", "creative") for audit/reference.

### Project Structure Notes

- Schema file: `backend/app/schemas/kb_settings.py`
- Unit tests: `backend/tests/unit/test_kb_settings_schemas.py`
- Follow existing schema organization in `backend/app/schemas/`
- Export from `__init__.py` following established pattern

[Source: docs/sprint-artifacts/correct-course-kb-level-config.md - Story 7.12 Requirements]
[Source: docs/epics/epic-7-infrastructure.md - Epic 7 Story 7.12 AC definitions]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md - Technical specifications]

### Learnings from Previous Story

**From Story 7-11 (Navigation Restructure & RBAC Default Groups):**

- **Enum Pattern:** Use `str, Enum` base class for string enums (see PermissionLevel in permission_service.py)
- **Service Pattern:** Keep validation logic in schemas, business logic in services
- **Test Coverage:** Previous story achieved 75 tests - maintain similar thoroughness
- **Code Review:** Story 7-11 received APPROVED status with clean patterns

**Files Created in 7-11 for Reference:**
- `backend/app/services/permission_service.py` - PermissionLevel enum pattern
- `frontend/src/components/layout/main-nav.tsx` - Navigation structure
- `frontend/src/components/auth/operator-guard.tsx` - Route protection pattern

[Source: docs/sprint-artifacts/7-11-navigation-restructure-rbac-default-groups.md]

### Testing Guidelines

Follow testing patterns from `docs/testing-guideline.md`:
- Use pytest fixtures for common setup
- Test boundary values (exact limits)
- Test invalid inputs raise ValidationError
- Test JSON serialization round-trips

[Source: docs/testing-guideline.md]

### References

- [docs/sprint-artifacts/correct-course-kb-level-config.md](docs/sprint-artifacts/correct-course-kb-level-config.md) - Primary source for Story 7.12 detailed requirements
- [docs/epics/epic-7-infrastructure.md](docs/epics/epic-7-infrastructure.md) - Epic breakdown with all ACs
- [docs/sprint-artifacts/tech-spec-epic-7.md](docs/sprint-artifacts/tech-spec-epic-7.md) - Technical architecture
- [docs/sprint-artifacts/7-11-navigation-restructure-rbac-default-groups.md](docs/sprint-artifacts/7-11-navigation-restructure-rbac-default-groups.md) - Previous story for continuity
- [docs/testing-guideline.md](docs/testing-guideline.md) - Testing standards and patterns
- [backend/app/schemas/](backend/app/schemas/) - Existing schema patterns

## Dev Agent Record

### Context Reference
- Story Key: 7-12-kb-settings-schema
- Epic: 7 - Infrastructure & DevOps
- Story Points: 5
- Prerequisites: Story 7.10 (KB Model Configuration) - DONE

### Agent Model Used
Claude Opus 4.5

### Debug Log References
- All 138 unit tests pass (0.13s execution)
- Ruff linting passes with no issues

### Completion Notes List
- Implementation follows Pydantic v2 patterns with Field validators
- All enums use `str, Enum` base class for JSON serialization compatibility
- `ClassVar` used for REINDEX_FIELDS to avoid Pydantic serialization
- `model_config = {"extra": "forbid"}` enforces strict validation
- Backwards compatibility verified with empty `{}` input
- Re-indexing detection implemented with comprehensive warning messages

### File List
- `[NEW] backend/app/schemas/kb_settings.py` - 267 lines, all schemas and enums
- `[NEW] backend/tests/unit/test_kb_settings_schemas.py` - 1065 lines, 138 tests
- `[MODIFIED] backend/app/schemas/__init__.py` - Added exports for all KB settings schemas

---

## Code Review

### Review Metadata
- **Reviewer:** Senior Developer (Code Review Workflow)
- **Review Date:** 2025-12-09
- **Review Outcome:** APPROVED

### Systematic AC Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC-7.12.1 | PASS | `kb_settings.py:72-83` - ChunkingConfig with strategy enum, chunk_size (ge=100, le=2000), chunk_overlap (ge=0, le=500), separators (list[str]) |
| AC-7.12.2 | PASS | `kb_settings.py:85-96` - RetrievalConfig with all required fields and validation ranges |
| AC-7.12.3 | PASS | `kb_settings.py:98-106` - RerankingConfig with enabled, model (optional), top_n (ge=1, le=50) |
| AC-7.12.4 | PASS | `kb_settings.py:108-120` - GenerationConfig with all temperature/penalty ranges as specified |
| AC-7.12.5 | PASS | `kb_settings.py:122-131` - NERConfig with all required fields |
| AC-7.12.6 | PASS | `kb_settings.py:133-142` - DocumentProcessingConfig with 4 boolean fields |
| AC-7.12.7 | PASS | `kb_settings.py:144-156` - KBPromptConfig with system_prompt (max_length=4000), citation_style, uncertainty_handling enums |
| AC-7.12.8 | PASS | `kb_settings.py:158-179` - EmbeddingConfig with all fields including prefix_document/prefix_query (max_length=100) |
| AC-7.12.9 | PASS | `kb_settings.py:239-267` - KBSettings composite with default_factory for all sub-configs and preset field |
| AC-7.12.10 | PASS | `test_kb_settings_schemas.py:651-657` - `KBSettings.model_validate({})` test verifies backwards compatibility |
| AC-7.12.11 | PASS | `kb_settings.py:172-231` - REINDEX_FIELDS ClassVar, requires_reindex(), detect_reindex_fields(), get_reindex_warning() methods |

### Test Coverage Summary
- **Total Tests:** 138
- **Pass Rate:** 100%
- **Test Categories:**
  - Enum Tests: 6 test classes covering all enum types
  - Sub-Config Validation Tests: 8 test classes (one per config schema)
  - Composite KBSettings Tests: 1 test class with 10 tests
  - Re-indexing Detection Tests: 2 test classes with 17 tests
  - Edge Case Tests: 6 additional test classes covering validation failures and edge cases

### Code Quality Assessment

**Strengths:**
1. **Clean Architecture:** Well-organized file with clear section comments separating enums, sub-configs, and composite schema
2. **Type Safety:** Proper use of `ClassVar[set[str]]` for REINDEX_FIELDS to prevent Pydantic serialization issues
3. **Documentation:** Each class has docstrings referencing the relevant AC
4. **Validation:** Comprehensive Field validators using `ge`, `le`, `max_length` constraints
5. **Sensible Defaults:** Production-ready default values (chunk_size=512, temperature=0.7, etc.)
6. **Test Thoroughness:** 138 tests covering boundary values, invalid inputs, JSON round-trips, and edge cases

**Minor Observations (Not Blocking):**
- The `get_reindex_warning()` message is more detailed than the spec's minimal example, which is actually better for UX

### Security Review
- No security concerns identified
- No external API calls or file system access
- Pure schema validation with no business logic side effects

### Performance Considerations
- All validation is synchronous Pydantic v2 which is highly optimized
- ClassVar usage avoids per-instance overhead for REINDEX_FIELDS

### Recommendations
None - implementation is clean and complete.

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-09 | Story drafted from epic requirements | SM Agent |
| 2025-12-09 | Story improved - ACs aligned with source docs, expanded tasks, added testing-guideline reference | SM Agent (Auto-improve) |
| 2025-12-09 | Implementation complete - all 11 ACs satisfied | Dev Agent |
| 2025-12-09 | Code review APPROVED - 138 tests passing, linting clean | Code Review Workflow |
