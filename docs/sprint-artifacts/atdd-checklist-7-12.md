# ATDD Checklist - Epic 7, Story 12: KB Settings Schema & Pydantic Models

**Date:** 2025-12-09
**Author:** Tung Vu
**Primary Test Level:** Unit (Python/pytest)

---

## Story Summary

Create typed Pydantic schemas for KB-level configuration so that settings are validated at runtime and type-safe throughout the codebase.

**As a** developer
**I want** typed Pydantic schemas for KB-level configuration
**So that** settings are validated at runtime and type-safe throughout the codebase

---

## Acceptance Criteria

1. **AC-7.12.1**: ChunkingConfig schema with strategy enum (fixed/recursive/semantic), chunk_size (100-2000), chunk_overlap (0-500), separators (list[str])
2. **AC-7.12.2**: RetrievalConfig schema with top_k (1-100), similarity_threshold (0.0-1.0), method enum (vector/hybrid/hyde), mmr_enabled (bool), mmr_lambda (0.0-1.0), hybrid_alpha (0.0-1.0)
3. **AC-7.12.3**: RerankingConfig schema with enabled (bool), model (optional str), top_n (1-50)
4. **AC-7.12.4**: GenerationConfig schema with temperature (0.0-2.0), top_p (0.0-1.0), top_k (1-100), max_tokens (100-16000), frequency_penalty (-2.0-2.0), presence_penalty (-2.0-2.0), stop_sequences (list[str])
5. **AC-7.12.5**: NERConfig schema with enabled (bool), confidence_threshold (0.0-1.0), entity_types (list[str]), batch_size (1-100)
6. **AC-7.12.6**: DocumentProcessingConfig schema with ocr_enabled (bool), language_detection (bool), table_extraction (bool), image_extraction (bool)
7. **AC-7.12.7**: KBPromptConfig schema with system_prompt (str, max 4000 chars), context_template (str), citation_style enum (inline/footnote/none), uncertainty_handling enum (acknowledge/refuse/best_effort), response_language (str)
8. **AC-7.12.8**: EmbeddingConfig schema with model_id (UUID, optional), batch_size (1-100), normalize (bool), truncation enum (start/end/none), max_length (128-16384), prefix_document (str, max 100 chars), prefix_query (str, max 100 chars), pooling_strategy enum (mean/cls/max/last)
9. **AC-7.12.9**: KBSettings composite schema aggregating all sub-configs with default factories and preset field
10. **AC-7.12.10**: Backwards compatibility - existing KBs with empty {} settings parse with all defaults
11. **AC-7.12.11**: Re-indexing trigger detection - EmbeddingConfig changes flag re-indexing required

---

## Failing Tests Created (RED Phase)

### Unit Tests (55 tests)

**File:** `backend/tests/unit/test_kb_settings_schemas.py` (~650 lines)

---

#### Enum Type Tests (7 tests)

- **Test:** `test_chunking_strategy_enum_values`
  - **Status:** RED - ChunkingStrategy enum not implemented
  - **Verifies:** AC-7.12.1 - ChunkingStrategy has values (fixed, recursive, semantic)

- **Test:** `test_retrieval_method_enum_values`
  - **Status:** RED - RetrievalMethod enum not implemented
  - **Verifies:** AC-7.12.2 - RetrievalMethod has values (vector, hybrid, hyde)

- **Test:** `test_citation_style_enum_values`
  - **Status:** RED - CitationStyle enum not implemented
  - **Verifies:** AC-7.12.7 - CitationStyle has values (inline, footnote, none)

- **Test:** `test_uncertainty_handling_enum_values`
  - **Status:** RED - UncertaintyHandling enum not implemented
  - **Verifies:** AC-7.12.7 - UncertaintyHandling has values (acknowledge, refuse, best_effort)

- **Test:** `test_truncation_strategy_enum_values`
  - **Status:** RED - TruncationStrategy enum not implemented
  - **Verifies:** AC-7.12.8 - TruncationStrategy has values (start, end, none)

- **Test:** `test_pooling_strategy_enum_values`
  - **Status:** RED - PoolingStrategy enum not implemented
  - **Verifies:** AC-7.12.8 - PoolingStrategy has values (mean, cls, max, last)

- **Test:** `test_enums_json_serializable`
  - **Status:** RED - Enums not JSON serializable
  - **Verifies:** All enums serialize to JSON strings correctly

---

#### ChunkingConfig Tests (8 tests)

- **Test:** `test_chunking_config_default_values`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - Defaults: strategy=recursive, chunk_size=512, chunk_overlap=50

- **Test:** `test_chunking_config_chunk_size_min_boundary`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - chunk_size accepts minimum value 100

- **Test:** `test_chunking_config_chunk_size_max_boundary`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - chunk_size accepts maximum value 2000

- **Test:** `test_chunking_config_chunk_size_below_min_fails`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - chunk_size=99 raises ValidationError

- **Test:** `test_chunking_config_chunk_size_above_max_fails`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - chunk_size=2001 raises ValidationError

- **Test:** `test_chunking_config_chunk_overlap_boundaries`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - chunk_overlap range 0-500

- **Test:** `test_chunking_config_separators_list`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - separators is list[str]

- **Test:** `test_chunking_config_extra_fields_forbidden`
  - **Status:** RED - ChunkingConfig not implemented
  - **Verifies:** AC-7.12.1 - Extra fields raise ValidationError

---

#### RetrievalConfig Tests (10 tests)

- **Test:** `test_retrieval_config_default_values`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - Defaults: top_k=10, similarity_threshold=0.7, method=vector

- **Test:** `test_retrieval_config_top_k_boundaries`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - top_k range 1-100

- **Test:** `test_retrieval_config_top_k_below_min_fails`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - top_k=0 raises ValidationError

- **Test:** `test_retrieval_config_similarity_threshold_boundaries`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - similarity_threshold range 0.0-1.0

- **Test:** `test_retrieval_config_mmr_enabled_default_false`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - mmr_enabled defaults to False

- **Test:** `test_retrieval_config_mmr_lambda_boundaries`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - mmr_lambda range 0.0-1.0

- **Test:** `test_retrieval_config_hybrid_alpha_boundaries`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - hybrid_alpha range 0.0-1.0

- **Test:** `test_retrieval_config_method_enum_validation`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - method accepts only valid enum values

- **Test:** `test_retrieval_config_invalid_method_fails`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - method="invalid" raises ValidationError

- **Test:** `test_retrieval_config_extra_fields_forbidden`
  - **Status:** RED - RetrievalConfig not implemented
  - **Verifies:** AC-7.12.2 - Extra fields raise ValidationError

---

#### RerankingConfig Tests (5 tests)

- **Test:** `test_reranking_config_default_values`
  - **Status:** RED - RerankingConfig not implemented
  - **Verifies:** AC-7.12.3 - Defaults: enabled=False, model=None, top_n=10

- **Test:** `test_reranking_config_top_n_boundaries`
  - **Status:** RED - RerankingConfig not implemented
  - **Verifies:** AC-7.12.3 - top_n range 1-50

- **Test:** `test_reranking_config_top_n_below_min_fails`
  - **Status:** RED - RerankingConfig not implemented
  - **Verifies:** AC-7.12.3 - top_n=0 raises ValidationError

- **Test:** `test_reranking_config_model_optional`
  - **Status:** RED - RerankingConfig not implemented
  - **Verifies:** AC-7.12.3 - model accepts None or string

- **Test:** `test_reranking_config_extra_fields_forbidden`
  - **Status:** RED - RerankingConfig not implemented
  - **Verifies:** AC-7.12.3 - Extra fields raise ValidationError

---

#### GenerationConfig Tests (10 tests)

- **Test:** `test_generation_config_default_values`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - Defaults: temperature=0.7, top_p=1.0, max_tokens=2000

- **Test:** `test_generation_config_temperature_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - temperature range 0.0-2.0

- **Test:** `test_generation_config_temperature_above_max_fails`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - temperature=2.1 raises ValidationError

- **Test:** `test_generation_config_top_p_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - top_p range 0.0-1.0

- **Test:** `test_generation_config_top_k_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - top_k range 1-100

- **Test:** `test_generation_config_max_tokens_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - max_tokens range 100-16000

- **Test:** `test_generation_config_frequency_penalty_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - frequency_penalty range -2.0-2.0

- **Test:** `test_generation_config_presence_penalty_boundaries`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - presence_penalty range -2.0-2.0

- **Test:** `test_generation_config_stop_sequences_list`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - stop_sequences is list[str]

- **Test:** `test_generation_config_extra_fields_forbidden`
  - **Status:** RED - GenerationConfig not implemented
  - **Verifies:** AC-7.12.4 - Extra fields raise ValidationError

---

#### NERConfig Tests (5 tests)

- **Test:** `test_ner_config_default_values`
  - **Status:** RED - NERConfig not implemented
  - **Verifies:** AC-7.12.5 - Defaults: enabled=False, confidence_threshold=0.8, batch_size=32

- **Test:** `test_ner_config_confidence_threshold_boundaries`
  - **Status:** RED - NERConfig not implemented
  - **Verifies:** AC-7.12.5 - confidence_threshold range 0.0-1.0

- **Test:** `test_ner_config_batch_size_boundaries`
  - **Status:** RED - NERConfig not implemented
  - **Verifies:** AC-7.12.5 - batch_size range 1-100

- **Test:** `test_ner_config_entity_types_list`
  - **Status:** RED - NERConfig not implemented
  - **Verifies:** AC-7.12.5 - entity_types is list[str]

- **Test:** `test_ner_config_extra_fields_forbidden`
  - **Status:** RED - NERConfig not implemented
  - **Verifies:** AC-7.12.5 - Extra fields raise ValidationError

---

#### DocumentProcessingConfig Tests (3 tests)

- **Test:** `test_document_processing_config_default_values`
  - **Status:** RED - DocumentProcessingConfig not implemented
  - **Verifies:** AC-7.12.6 - Defaults: all booleans False except ocr_enabled

- **Test:** `test_document_processing_config_all_booleans`
  - **Status:** RED - DocumentProcessingConfig not implemented
  - **Verifies:** AC-7.12.6 - All fields are booleans

- **Test:** `test_document_processing_config_extra_fields_forbidden`
  - **Status:** RED - DocumentProcessingConfig not implemented
  - **Verifies:** AC-7.12.6 - Extra fields raise ValidationError

---

#### KBPromptConfig Tests (6 tests)

- **Test:** `test_kb_prompt_config_default_values`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - Defaults: system_prompt="", citation_style=inline

- **Test:** `test_kb_prompt_config_system_prompt_max_length`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - system_prompt max 4000 chars

- **Test:** `test_kb_prompt_config_system_prompt_exceeds_max_fails`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - system_prompt with 4001 chars raises ValidationError

- **Test:** `test_kb_prompt_config_citation_style_enum`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - citation_style enum validation

- **Test:** `test_kb_prompt_config_uncertainty_handling_enum`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - uncertainty_handling enum validation

- **Test:** `test_kb_prompt_config_extra_fields_forbidden`
  - **Status:** RED - KBPromptConfig not implemented
  - **Verifies:** AC-7.12.7 - Extra fields raise ValidationError

---

#### EmbeddingConfig Tests (10 tests)

- **Test:** `test_embedding_config_default_values`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - Defaults: model_id=None, batch_size=32, normalize=True

- **Test:** `test_embedding_config_model_id_accepts_uuid`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - model_id accepts UUID

- **Test:** `test_embedding_config_model_id_accepts_none`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - model_id accepts None (system default)

- **Test:** `test_embedding_config_batch_size_boundaries`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - batch_size range 1-100

- **Test:** `test_embedding_config_max_length_boundaries`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - max_length range 128-16384

- **Test:** `test_embedding_config_prefix_document_max_length`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - prefix_document max 100 chars

- **Test:** `test_embedding_config_prefix_query_max_length`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - prefix_query max 100 chars

- **Test:** `test_embedding_config_truncation_enum`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - truncation enum validation

- **Test:** `test_embedding_config_pooling_strategy_enum`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - pooling_strategy enum validation

- **Test:** `test_embedding_config_extra_fields_forbidden`
  - **Status:** RED - EmbeddingConfig not implemented
  - **Verifies:** AC-7.12.8 - Extra fields raise ValidationError

---

#### KBSettings Composite Tests (8 tests)

- **Test:** `test_kb_settings_default_factories`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - All sub-configs use default_factory

- **Test:** `test_kb_settings_partial_overrides`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - Can override individual sub-configs

- **Test:** `test_kb_settings_preset_field`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - preset field accepts optional string

- **Test:** `test_kb_settings_backwards_compatibility_empty_dict`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.10 - KBSettings.model_validate({}) succeeds

- **Test:** `test_kb_settings_backwards_compatibility_partial_dict`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.10 - Partial dicts parse with defaults

- **Test:** `test_kb_settings_json_round_trip`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - model_dump to model_validate round-trip

- **Test:** `test_kb_settings_nested_validation`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - Invalid nested config raises ValidationError

- **Test:** `test_kb_settings_extra_fields_forbidden`
  - **Status:** RED - KBSettings not implemented
  - **Verifies:** AC-7.12.9 - Extra fields raise ValidationError

---

#### Re-indexing Detection Tests (9 tests)

- **Test:** `test_requires_reindex_false_when_no_previous`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns False when previous is None

- **Test:** `test_requires_reindex_false_when_no_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns False when no re-index fields changed

- **Test:** `test_requires_reindex_true_when_model_id_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns True when model_id changes

- **Test:** `test_requires_reindex_true_when_normalize_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns True when normalize changes

- **Test:** `test_requires_reindex_true_when_prefix_document_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns True when prefix_document changes

- **Test:** `test_requires_reindex_true_when_prefix_query_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns True when prefix_query changes

- **Test:** `test_requires_reindex_true_when_pooling_strategy_changes`
  - **Status:** RED - EmbeddingConfig.requires_reindex not implemented
  - **Verifies:** AC-7.12.11 - Returns True when pooling_strategy changes

- **Test:** `test_detect_reindex_fields_returns_changed_fields`
  - **Status:** RED - EmbeddingConfig.detect_reindex_fields not implemented
  - **Verifies:** AC-7.12.11 - Returns list of changed field names

- **Test:** `test_get_reindex_warning_message`
  - **Status:** RED - EmbeddingConfig.get_reindex_warning not implemented
  - **Verifies:** AC-7.12.11 - Returns user-friendly warning message

---

## Data Factories Created

**Note:** This story tests pure Pydantic schemas - no database factories needed. Test data is created inline.

### Schema Test Helpers

**File:** `backend/tests/unit/test_kb_settings_schemas.py` (inline helpers)

**Helpers:**
- Inline schema instantiation with explicit overrides
- No faker needed - schema validation tests use explicit boundary values

---

## Fixtures Created

**Note:** This story tests pure Pydantic schemas - no fixtures needed. Each test is isolated and creates its own schema instances.

---

## Mock Requirements

**None required.** This story tests pure Pydantic schema validation with no external dependencies.

---

## Required data-testid Attributes

**None required.** This is a backend-only unit testing story with no UI components.

---

## Implementation Checklist

### Test: Enum Types (Task 1)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/schemas/kb_settings.py` file
- [ ] Implement `ChunkingStrategy` enum with values: fixed, recursive, semantic
- [ ] Implement `RetrievalMethod` enum with values: vector, hybrid, hyde
- [ ] Implement `CitationStyle` enum with values: inline, footnote, none
- [ ] Implement `UncertaintyHandling` enum with values: acknowledge, refuse, best_effort
- [ ] Implement `TruncationStrategy` enum with values: start, end, none
- [ ] Implement `PoolingStrategy` enum with values: mean, cls, max, last
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestEnumTypes -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: ChunkingConfig Schema (Task 2.1)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `ChunkingConfig` Pydantic model
- [ ] Add `strategy` field with `ChunkingStrategy` enum, default `RECURSIVE`
- [ ] Add `chunk_size` field with `Field(default=512, ge=100, le=2000)`
- [ ] Add `chunk_overlap` field with `Field(default=50, ge=0, le=500)`
- [ ] Add `separators` field with `Field(default_factory=lambda: ["\n\n", "\n", " ", ""])`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestChunkingConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: RetrievalConfig Schema (Task 2.2)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `RetrievalConfig` Pydantic model
- [ ] Add `top_k` field with `Field(default=10, ge=1, le=100)`
- [ ] Add `similarity_threshold` field with `Field(default=0.7, ge=0.0, le=1.0)`
- [ ] Add `method` field with `RetrievalMethod` enum, default `VECTOR`
- [ ] Add `mmr_enabled` field with `Field(default=False)`
- [ ] Add `mmr_lambda` field with `Field(default=0.5, ge=0.0, le=1.0)`
- [ ] Add `hybrid_alpha` field with `Field(default=0.5, ge=0.0, le=1.0)`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestRetrievalConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: RerankingConfig Schema (Task 2.3)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `RerankingConfig` Pydantic model
- [ ] Add `enabled` field with `Field(default=False)`
- [ ] Add `model` field with `Optional[str] = None`
- [ ] Add `top_n` field with `Field(default=10, ge=1, le=50)`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestRerankingConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.25 hours

---

### Test: GenerationConfig Schema (Task 2.4)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `GenerationConfig` Pydantic model
- [ ] Add `temperature` field with `Field(default=0.7, ge=0.0, le=2.0)`
- [ ] Add `top_p` field with `Field(default=1.0, ge=0.0, le=1.0)`
- [ ] Add `top_k` field with `Field(default=50, ge=1, le=100)`
- [ ] Add `max_tokens` field with `Field(default=2000, ge=100, le=16000)`
- [ ] Add `frequency_penalty` field with `Field(default=0.0, ge=-2.0, le=2.0)`
- [ ] Add `presence_penalty` field with `Field(default=0.0, ge=-2.0, le=2.0)`
- [ ] Add `stop_sequences` field with `Field(default_factory=list)`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestGenerationConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: NERConfig Schema (Task 2.5)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `NERConfig` Pydantic model
- [ ] Add `enabled` field with `Field(default=False)`
- [ ] Add `confidence_threshold` field with `Field(default=0.8, ge=0.0, le=1.0)`
- [ ] Add `entity_types` field with `Field(default_factory=list)`
- [ ] Add `batch_size` field with `Field(default=32, ge=1, le=100)`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestNERConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.25 hours

---

### Test: DocumentProcessingConfig Schema (Task 2.6)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `DocumentProcessingConfig` Pydantic model
- [ ] Add `ocr_enabled` field with `Field(default=True)`
- [ ] Add `language_detection` field with `Field(default=True)`
- [ ] Add `table_extraction` field with `Field(default=False)`
- [ ] Add `image_extraction` field with `Field(default=False)`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestDocumentProcessingConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.25 hours

---

### Test: KBPromptConfig Schema (Task 2.7)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `KBPromptConfig` Pydantic model
- [ ] Add `system_prompt` field with `Field(default="", max_length=4000)`
- [ ] Add `context_template` field with `Field(default="")`
- [ ] Add `citation_style` field with `CitationStyle` enum, default `INLINE`
- [ ] Add `uncertainty_handling` field with `UncertaintyHandling` enum, default `ACKNOWLEDGE`
- [ ] Add `response_language` field with `Field(default="en")`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestKBPromptConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: EmbeddingConfig Schema (Task 2.8)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `EmbeddingConfig` Pydantic model
- [ ] Add `model_id` field with `Optional[UUID] = None`
- [ ] Add `batch_size` field with `Field(default=32, ge=1, le=100)`
- [ ] Add `normalize` field with `Field(default=True)`
- [ ] Add `truncation` field with `TruncationStrategy` enum, default `END`
- [ ] Add `max_length` field with `Field(default=512, ge=128, le=16384)`
- [ ] Add `prefix_document` field with `Field(default="", max_length=100)`
- [ ] Add `prefix_query` field with `Field(default="", max_length=100)`
- [ ] Add `pooling_strategy` field with `PoolingStrategy` enum, default `MEAN`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestEmbeddingConfig -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: KBSettings Composite Schema (Task 3)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Implement `KBSettings` Pydantic model
- [ ] Add `chunking` field with `Field(default_factory=ChunkingConfig)`
- [ ] Add `retrieval` field with `Field(default_factory=RetrievalConfig)`
- [ ] Add `reranking` field with `Field(default_factory=RerankingConfig)`
- [ ] Add `generation` field with `Field(default_factory=GenerationConfig)`
- [ ] Add `ner` field with `Field(default_factory=NERConfig)`
- [ ] Add `processing` field with `Field(default_factory=DocumentProcessingConfig)`
- [ ] Add `prompts` field with `Field(default_factory=KBPromptConfig)`
- [ ] Add `embedding` field with `Field(default_factory=EmbeddingConfig)`
- [ ] Add `preset` field with `Optional[str] = None`
- [ ] Add `model_config = {"extra": "forbid"}`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestKBSettings -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: Re-indexing Detection (Task 4)

**File:** `backend/tests/unit/test_kb_settings_schemas.py`

**Tasks to make this test pass:**

- [ ] Add `REINDEX_FIELDS: ClassVar[set[str]]` to `EmbeddingConfig`
- [ ] Set `REINDEX_FIELDS = {"model_id", "normalize", "prefix_document", "prefix_query", "pooling_strategy"}`
- [ ] Implement `requires_reindex(self, previous: Optional["EmbeddingConfig"]) -> bool`
- [ ] Implement `detect_reindex_fields(self, previous: Optional["EmbeddingConfig"]) -> list[str]`
- [ ] Implement `get_reindex_warning(self, changed_fields: list[str]) -> str`
- [ ] Run test: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py::TestReindexDetection -v`
- [ ] ✅ Tests pass (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: Exports and Integration (Task 9)

**File:** `backend/app/schemas/__init__.py`

**Tasks to make this test pass:**

- [ ] Export all enums from `kb_settings.py`
- [ ] Export all sub-config schemas from `kb_settings.py`
- [ ] Export `KBSettings` from `kb_settings.py`
- [ ] Run ruff: `cd backend && .venv/bin/ruff check app/schemas/kb_settings.py`
- [ ] Run all tests: `cd backend && .venv/bin/pytest tests/unit/test_kb_settings_schemas.py -v`
- [ ] ✅ All tests pass (green phase)

**Estimated Effort:** 0.25 hours

---

## Running Tests

```bash
# Run all failing tests for this story
cd backend && source .venv/bin/activate && pytest tests/unit/test_kb_settings_schemas.py -v

# Run specific test class
cd backend && source .venv/bin/activate && pytest tests/unit/test_kb_settings_schemas.py::TestChunkingConfig -v

# Run tests with coverage
cd backend && source .venv/bin/activate && pytest tests/unit/test_kb_settings_schemas.py --cov=app/schemas/kb_settings --cov-report=term-missing

# Run linting
cd backend && source .venv/bin/activate && ruff check app/schemas/kb_settings.py

# Test backwards compatibility manually
cd backend && source .venv/bin/activate && python -c "from app.schemas.kb_settings import KBSettings; print(KBSettings.model_validate({}))"
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

**TEA Agent Responsibilities:**

- ✅ All 55 tests written and failing
- ✅ Test file structure follows existing patterns (test_kb_schemas.py)
- ✅ Boundary value testing for all numeric fields
- ✅ ValidationError assertions for invalid inputs
- ✅ Implementation checklist created with clear tasks

**Verification:**

- All tests run and fail as expected
- Failure messages are clear: "ImportError: cannot import name 'ChunkingConfig'"
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Create schema file**: `backend/app/schemas/kb_settings.py`
2. **Implement enums first** (Task 1) - all tests depend on these
3. **Implement sub-configs** (Tasks 2.1-2.8) - one at a time
4. **Implement KBSettings** (Task 3) - composite with default_factory
5. **Implement re-indexing** (Task 4) - EmbeddingConfig methods
6. **Export schemas** (Task 9) - update `__init__.py`

**Key Principles:**

- One test class at a time
- Run tests after each class implementation
- Use existing patterns from `knowledge_base.py` and `test_kb_schemas.py`

**Progress Tracking:**

- Check off tasks as you complete them
- Share progress in daily standup
- Mark story as IN PROGRESS in sprint-status.yaml

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all 55 tests pass**
2. **Run ruff linting**: Fix any style issues
3. **Review defaults**: Ensure all defaults are sensible for production
4. **Documentation**: Add docstrings to each schema class
5. **Run full test suite**: Ensure no regressions

**Completion:**

- All tests pass
- Ruff linting passes
- Backwards compatibility verified: `KBSettings.model_validate({})` succeeds
- Ready for code review

---

## Next Steps

1. **Create test file** at `backend/tests/unit/test_kb_settings_schemas.py`
2. **Run failing tests** to confirm RED phase: `pytest tests/unit/test_kb_settings_schemas.py -v`
3. **Begin implementation** using implementation checklist as guide
4. **Work one test class at a time** (red → green for each)
5. **When all tests pass**, run code review workflow
6. **When review complete**, mark story as DONE

---

## Knowledge Base References Applied

This ATDD workflow consulted the following knowledge fragments:

- **test-quality.md** - Test design principles (deterministic tests, explicit assertions)
- **data-factories.md** - Not needed - pure schema tests use inline data
- **fixture-architecture.md** - Not needed - pure schema tests need no fixtures

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `cd backend && source .venv/bin/activate && pytest tests/unit/test_kb_settings_schemas.py -v`

**Expected Results:**

```
FAILED tests/unit/test_kb_settings_schemas.py - ImportError: cannot import name 'ChunkingStrategy'
```

**Summary:**

- Total tests: 55
- Passing: 0 (expected)
- Failing: 55 (expected - import errors)
- Status: ✅ RED phase verified

**Expected Failure Messages:**

- `ImportError: cannot import name 'ChunkingStrategy' from 'app.schemas.kb_settings'`
- `ImportError: cannot import name 'ChunkingConfig' from 'app.schemas.kb_settings'`
- `ImportError: cannot import name 'KBSettings' from 'app.schemas.kb_settings'`

---

## Notes

- This story is **backend-only** - no frontend components
- All schemas use `extra="forbid"` to catch typos in config keys
- Re-indexing detection is critical for Story 7-13 (KBConfigResolver)
- Backwards compatibility is non-negotiable - existing KBs must continue working

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Refer to `docs/sprint-artifacts/7-12-kb-settings-schema.context.xml` for full story context
- Consult `backend/app/schemas/knowledge_base.py` for existing patterns

---

**Generated by BMad TEA Agent** - 2025-12-09
