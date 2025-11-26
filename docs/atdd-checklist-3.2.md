# ATDD Checklist: Story 3.2 - LLM Answer Synthesis with Citations

**Date:** 2025-11-25
**Story ID:** 3.2
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.2 - LLM Answer Synthesis with Citations

**Description:**
Implement LLM-powered answer synthesis from retrieved chunks with inline `[n]` citation markers. This is the **MAGIC MOMENT** of LumiKB - citations provide trust and verifiability, differentiating from generic RAG chatbots.

**Risk Level:** CRITICAL (BLOCK)
- **R-001**: LLM citation quality (Score: 9 - BLOCK) - If LLM doesn't follow `[n]` format, entire Epic 3 fails
- **R-002**: Citation mapping errors (Score: 6 - MITIGATE) - Wrong chunk = false confidence
- **R-007**: LLM hallucination (Score: 6 - MITIGATE) - Answer includes info NOT in chunks

**THIS IS THE MOST CRITICAL STORY IN EPIC 3.**

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.2.1 | LLM uses inline `[n]` markers | Integration | `test_llm_synthesis.py::test_llm_answer_contains_citation_markers` | ❌ RED |
| AC-3.2.2 | Citation numbering and mapping | Unit | `test_citation_service.py::test_extract_citations_with_valid_markers` | ❌ RED |
| AC-3.2.2 | Orphaned marker validation | Unit | `test_citation_service.py::test_extract_citations_orphaned_marker_raises_error` | ❌ RED |
| AC-3.2.2 | Out-of-bounds marker validation | Unit | `test_citation_service.py::test_extract_citations_out_of_bounds_raises_error` | ❌ RED |
| AC-3.2.2 | Duplicate markers allowed | Unit | `test_citation_service.py::test_extract_citations_duplicate_markers_allowed` | ❌ RED |
| AC-3.2.2 | No markers edge case | Unit | `test_citation_service.py::test_extract_citations_no_markers_returns_empty` | ❌ RED |
| AC-3.2.3 | Citation metadata completeness | Unit | `test_citation_service.py::test_citation_metadata_includes_all_required_fields` | ❌ RED |
| AC-3.2.3 | Excerpt truncation (200 chars) | Unit | `test_citation_service.py::test_citation_excerpt_truncated_to_200_chars` | ❌ RED |
| AC-3.2.3 | Integration metadata check | Integration | `test_llm_synthesis.py::test_citations_include_all_required_metadata` | ❌ RED |
| AC-3.2.4 | Confidence score (high coverage) | Unit | `test_citation_service.py::test_calculate_confidence_score_high_coverage` | ❌ RED |
| AC-3.2.4 | Confidence score (low coverage) | Unit | `test_citation_service.py::test_calculate_confidence_score_low_coverage` | ❌ RED |
| AC-3.2.4 | Confidence in API response | Integration | `test_llm_synthesis.py::test_llm_answer_includes_confidence_score` | ❌ RED |
| AC-3.2.5 | Hallucination prevention | Integration | `test_llm_synthesis.py::test_llm_answer_grounded_in_retrieved_chunks` | ❌ RED |

**Total Tests**: 13 tests (8 unit + 5 integration)

---

## Test Files Created

### Unit Tests

**File**: `backend/tests/unit/test_citation_service.py`

**Tests (8 unit tests):**
1. ✅ `test_extract_citations_with_valid_markers` - Core citation extraction logic
2. ✅ `test_extract_citations_orphaned_marker_raises_error` - Validates R-002 mitigation
3. ✅ `test_extract_citations_out_of_bounds_raises_error` - Edge case validation
4. ✅ `test_extract_citations_duplicate_markers_allowed` - Deduplication logic
5. ✅ `test_extract_citations_no_markers_returns_empty` - Empty-case handling
6. ✅ `test_citation_metadata_includes_all_required_fields` - AC-3.2.3 validation
7. ✅ `test_citation_excerpt_truncated_to_200_chars` - Truncation logic
8. ✅ `test_calculate_confidence_score_high_coverage` - Confidence algorithm (high)
9. ✅ `test_calculate_confidence_score_low_coverage` - Confidence algorithm (low)

**Pattern**: Pure function testing, no external dependencies

### Integration Tests

**File**: `backend/tests/integration/test_llm_synthesis.py`

**Tests (5 integration tests):**
1. ✅ `test_llm_answer_contains_citation_markers` - **R-001 BLOCK RISK** - LLM format compliance
2. ✅ `test_llm_answer_citations_map_to_chunks` - Citation mapping validation
3. ✅ `test_llm_answer_grounded_in_retrieved_chunks` - **R-007 MITIGATE** - Hallucination check
4. ✅ `test_llm_answer_includes_confidence_score` - API response validation
5. ✅ `test_citations_include_all_required_metadata` - End-to-end metadata check
6. ✅ `test_synthesis_without_results_returns_empty_answer` - Empty results handling

**Pattern**: End-to-end API testing with LLM integration

---

## Supporting Infrastructure

### Test Fixtures

**Created in test files:**
- `mock_chunks` - Mock search chunks with metadata (unit tests)
- `kb_with_indexed_security_docs` - KB with OAuth/MFA docs (integration)
- `mock_llm_response_with_citations` - Deterministic LLM response for testing

### Mock Requirements

**LiteLLM Synthesis Mock** (CRITICAL):
```python
@pytest.fixture
def mock_llm_synthesis(monkeypatch):
    """Mock LiteLLM synthesis to return deterministic responses with citations."""
    async def mock_synthesis(chunks, query, model="gpt-4"):
        # Return deterministic answer with [1], [2] markers
        return {
            "answer": "OAuth 2.0 [1] and MFA [2] are recommended for API security.",
            "usage": {"prompt_tokens": 500, "completion_tokens": 30}
        }

    monkeypatch.setattr(
        "app.services.synthesis_service.synthesize_answer",
        mock_synthesis
    )
```

**Why mock?**
- Deterministic testing (LLMs are non-deterministic)
- Cost savings (avoid real API calls in tests)
- Speed (mocked responses are instant)

**Alternative**: Use LiteLLM with `temperature=0` and few-shot examples for semi-deterministic results

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 13 tests written and failing
- [x] Fixtures scaffolded
- [x] Mock requirements documented

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Create Citation Data Model

- [ ] Create `backend/app/models/citation.py`
- [ ] Define `Citation` dataclass with fields:
  - `number: int`
  - `chunk_id: int`
  - `document_id: int`
  - `document_name: str`
  - `page_number: int | None`
  - `section_header: str`
  - `excerpt: str` (max 200 chars)
  - `char_start: int`
  - `char_end: int`
- [ ] Run test: `test_citation_metadata_includes_all_required_fields`
- [ ] ✅ Test passes (data model defined)

#### Task 2: Create CitationService (Core Logic)

- [ ] Create `backend/app/services/citation_service.py`
- [ ] Implement `class CitationService`
- [ ] Implement `extract_citations(answer: str, chunks: list) -> tuple[str, list[Citation]]`:
  - Parse answer for `[n]` markers using regex: `\[(\d+)\]`
  - Validate all markers ≤ len(chunks)
  - Raise `CitationMappingError` for orphaned/OOB markers
  - Map each marker to corresponding chunk (1-indexed)
  - Extract metadata from chunk
  - Truncate excerpt to 200 chars
  - Deduplicate citations (same marker cited twice)
  - Return clean text (markers removed) + citations list
- [ ] Run tests: All unit tests in `test_citation_service.py`
- [ ] ✅ Tests pass (citation extraction works)

#### Task 3: Implement Confidence Score Calculation

- [ ] In `CitationService`, implement `calculate_confidence(answer: str, chunks: list, citation_count: int) -> int`:
  - **Algorithm** (simple heuristic):
    - Base score: `(citation_count / len(chunks)) * 100`
    - Penalty: If answer is much longer than chunks, reduce score
    - Penalty: If chunks have low relevance_score, reduce confidence
    - Clamp to 0-100 range
  - **Advanced** (optional):
    - Semantic similarity between answer and concatenated chunks (cosine similarity)
    - Fact verification using NLI model
- [ ] Run tests: `test_calculate_confidence_score_*`
- [ ] ✅ Tests pass (confidence calculation works)

#### Task 4: Create SynthesisService (LLM Integration)

- [ ] Create `backend/app/services/synthesis_service.py`
- [ ] Implement `synthesize_answer(chunks: list, query: str) -> dict`:
  - Build LLM system prompt with CRITICAL instructions:
    ```
    You are a knowledge base assistant. Answer the user's question using ONLY the provided context chunks.

    CRITICAL CITATION RULES:
    1. Use inline [n] markers to cite sources (e.g., "OAuth 2.0 [1] is...")
    2. Number citations sequentially: [1], [2], [3], etc.
    3. Cite the chunk number where information appears
    4. Do NOT include information outside the provided chunks
    5. If chunks don't contain relevant info, say "I don't have information on that"

    CONTEXT CHUNKS:
    [1] {chunk_1_text}
    [2] {chunk_2_text}
    ...

    USER QUESTION: {query}
    ```
  - Call `litellm.completion(model="gpt-4", messages=[...])`
  - Parse LLM response
  - Use `CitationService.extract_citations()` to extract markers
  - Calculate confidence score
  - Return `{ answer, citations, confidence_score }`
- [ ] Run test: `test_llm_answer_contains_citation_markers`
- [ ] ✅ Test passes (LLM follows citation format)

#### Task 5: Integrate Synthesis into Search Endpoint

- [ ] Update `/api/v1/search` endpoint in `backend/app/api/v1/search.py`
- [ ] Add request parameter: `synthesize: bool = False` (optional)
- [ ] If `synthesize=True`:
  - After Qdrant search, pass top N chunks to `SynthesisService`
  - Include `answer`, `citations`, `confidence_score` in response
- [ ] If `synthesize=False`:
  - Return only `results` (chunks) as before
- [ ] Run test: `test_llm_answer_includes_confidence_score`
- [ ] ✅ Test passes (end-to-end synthesis works)

#### Task 6: Hallucination Prevention Validation

- [ ] Review LLM system prompt (Task 4) for grounding instructions
- [ ] Add few-shot examples to prompt showing correct citation usage
- [ ] Test with manual queries to verify LLM doesn't hallucinate
- [ ] Run test: `test_llm_answer_grounded_in_retrieved_chunks`
- [ ] ✅ Test passes (confidence score reflects chunk coverage)

**CRITICAL**: If this test fails (confidence < 40% frequently), revisit prompt engineering:
- Add more explicit grounding instructions
- Use `temperature=0` for determinism
- Consider prompt template with slot-filling pattern

#### Task 7: Handle Edge Cases

- [ ] Implement empty results handling in `SynthesisService`
- [ ] If no chunks found, return: `{ answer: "", citations: [], confidence_score: 0 }`
- [ ] Run test: `test_synthesis_without_results_returns_empty_answer`
- [ ] ✅ Test passes (empty case handled)

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 13 tests written and failing
- ✅ Tests define expected behavior for citation system
- ✅ Failures due to missing implementation (CitationService, SynthesisService don't exist)

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (Citation data model) - Foundation
2. Task 2 (CitationService) - Core logic
3. Task 3 (Confidence calculation) - Algorithm
4. Task 4 (SynthesisService) - LLM integration
5. Task 5 (Search endpoint update) - API integration
6. Task 6 (Hallucination validation) - Quality assurance
7. Task 7 (Edge cases) - Robustness

### REFACTOR Phase (After all tests green)

1. Extract prompt template to config file
2. Add logging for citation extraction failures
3. Optimize confidence calculation (cache chunk embeddings)
4. Add telemetry: track LLM token usage, citation accuracy
5. Code review with senior dev
6. Commit: "feat: implement LLM citation synthesis (Story 3.2)"

---

## Running Tests

### Run All Unit Tests

```bash
cd backend
pytest tests/unit/test_citation_service.py -v

# Expected: All 8 tests FAIL (RED phase)
```

### Run All Integration Tests

```bash
pytest tests/integration/test_llm_synthesis.py -v

# Expected: All 5 tests FAIL (RED phase)
```

### Run Specific Critical Test (R-001 BLOCK)

```bash
# This is THE most important test (LLM citation format compliance)
pytest tests/integration/test_llm_synthesis.py::test_llm_answer_contains_citation_markers -vv

# Must pass before Story 3.2 is done
```

### Run After Implementation

```bash
# Run full Story 3.2 test suite
pytest tests/unit/test_citation_service.py tests/integration/test_llm_synthesis.py -v

# Expected: All 13 tests PASS (GREEN phase)
```

---

## LLM System Prompt (Draft)

**CRITICAL COMPONENT** - This prompt is the R-001 mitigation strategy:

```
You are a knowledge base assistant that answers questions using provided context.

CRITICAL CITATION RULES (MUST FOLLOW):
1. Use inline [n] markers to cite sources, e.g., "OAuth 2.0 [1] is recommended."
2. Number citations sequentially: [1], [2], [3], etc.
3. Each [n] corresponds to the chunk number in the context below
4. ONLY use information from the provided chunks
5. If a fact comes from chunk 2, mark it with [2]
6. If chunks don't answer the question, say "I don't have information on that topic"

CONTEXT CHUNKS:
[1] {chunk_text_1}
[2] {chunk_text_2}
[3] {chunk_text_3}

EXAMPLE ANSWER FORMAT:
"OAuth 2.0 [1] provides delegated access without exposing credentials. Combining OAuth with MFA [2] significantly improves security."

USER QUESTION: {query}

YOUR ANSWER (with inline [n] citations):
```

**Few-Shot Example** (add to prompt):
```
EXAMPLE 1:
Question: What is OAuth 2.0?
Context:
[1] OAuth 2.0 is an authorization framework that enables apps to obtain limited access.
[2] MFA adds extra security layers.

Answer: OAuth 2.0 [1] is an authorization framework for delegated access.

EXAMPLE 2:
Question: How do I implement security?
Context:
[1] Use OAuth 2.0 for auth.
[2] Enable MFA for users.

Answer: Implement OAuth 2.0 [1] for authorization and enable MFA [2] for additional security.
```

---

## Required Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
litellm = "^1.0.0"  # LLM API client (already added in Story 3.1)
```

### Environment Variables

```bash
# LiteLLM Configuration
LITELLM_MODEL_SYNTHESIS=gpt-4  # Use GPT-4 for better instruction following
LITELLM_API_KEY=sk-...  # OpenAI API key
LITELLM_TEMPERATURE=0  # Deterministic responses (reduce hallucination)
```

---

## Known Issues / TODOs

### LLM Prompt Engineering

**Challenge**: LLMs don't always follow citation format perfectly (R-001 risk).

**Mitigation Strategies**:
1. **Few-shot examples** - Show 3-5 examples of correct citation usage
2. **JSON mode** (alternative) - Use structured output instead of freeform text
3. **Temperature=0** - Reduce randomness
4. **Post-processing validation** - Reject responses without citations
5. **Manual QA sampling** - Review 50 real queries before launch

**Action**: Iterate on prompt template until test pass rate > 95%

### Confidence Score Algorithm

**Current**: Simple heuristic (citation_count / chunk_count * 100)

**Improvements**:
- Semantic similarity (cosine distance between answer embedding and chunk embeddings)
- Fact verification (NLI model to check if answer is entailed by chunks)
- Citation density (# citations per sentence)

**Action**: Start simple, iterate based on user feedback

### Hallucination Detection

**Current**: Low confidence score triggers warning

**Improvements**:
- Fact-checking model (does answer claim something NOT in chunks?)
- User verification flow (Story 3.10 - manual citation review)
- Automated flagging (if confidence < 50%, require manual review before export)

**Action**: Implement basic confidence threshold, enhance in future sprints

---

## Next Steps for DEV Team

### Immediate Actions

1. **Review this checklist** and R-001 BLOCK risk mitigation plan
2. **Review LLM system prompt** (draft above) - critical for citation quality
3. **Set up LiteLLM mock fixture** for integration tests
4. **Run failing tests** to confirm RED phase: `pytest tests/unit/test_citation_service.py -v`
5. **Start GREEN phase** with Task 1 (Citation data model)

### Definition of Done

- [ ] All 13 tests pass (8 unit + 5 integration)
- [ ] LLM citation format compliance validated (test_llm_answer_contains_citation_markers passes)
- [ ] Manual QA: 50 real queries, citation accuracy > 90%
- [ ] Confidence score calculated and displayed
- [ ] Code reviewed by senior dev (focus on R-001 mitigation)
- [ ] Merged to main branch

---

## Quality Gate Criteria

**CRITICAL (Must Pass):**
- [ ] `test_llm_answer_contains_citation_markers` passes (R-001 BLOCK)
- [ ] `test_extract_citations_with_valid_markers` passes (R-002 MITIGATE)
- [ ] `test_llm_answer_grounded_in_retrieved_chunks` confidence >= 40% (R-007 MITIGATE)

**Important (Should Pass):**
- [ ] All unit tests pass (citation extraction logic)
- [ ] All integration tests pass (end-to-end)

**Optional (Nice to Have):**
- [ ] Manual QA pass rate > 95%
- [ ] Confidence score aligns with human judgment

---

## Knowledge Base References Applied

**Frameworks:**
- `test-levels-framework.md` - Unit vs Integration test selection
- `test-quality.md` - Given-When-Then structure
- `test-priorities-matrix.md` - P0 prioritization (BLOCK risk)

**Risk Management:**
- `test-design-epic-3.md` - R-001, R-002, R-007 risk assessment
- `risk-governance.md` - BLOCK risk mitigation strategy

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.2 - LLM Answer Synthesis with Citations
**Primary Test Levels**: Unit (8 tests) + Integration (5 tests)

**Failing Tests Created**:
- Unit tests: 8 tests in `backend/tests/unit/test_citation_service.py`
- Integration tests: 5 tests in `backend/tests/integration/test_llm_synthesis.py`

**Supporting Infrastructure**:
- Fixtures: 3 fixtures (mock_chunks, kb_with_indexed_security_docs, mock_llm_response)
- Mocks: 1 critical mock (LiteLLM synthesis)
- LLM prompt: Draft system prompt with few-shot examples

**Implementation Checklist**:
- Total tasks: 7 tasks
- Estimated effort: 16-20 hours (CRITICAL story)

**BLOCK Risk Mitigation**:
- R-001 (Score 9): LLM prompt + validation tests + few-shot examples
- R-002 (Score 6): Citation mapping unit tests (orphaned/OOB validation)
- R-007 (Score 6): Confidence score + grounding instructions

**Next Steps for DEV Team**:
1. Review LLM system prompt (CRITICAL for R-001)
2. Run failing tests: `pytest tests/unit/test_citation_service.py -v`
3. Implement Task 1 (Citation data model)
4. Follow RED → GREEN → REFACTOR cycle
5. **THIS STORY CANNOT FAIL** - It's the Epic 3 magic moment

**Output File**: `docs/atdd-checklist-3.2.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
**Priority**: P0 - CRITICAL BLOCK RISK
