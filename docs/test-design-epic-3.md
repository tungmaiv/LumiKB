# Test Design: Epic 3 - Semantic Search & Citations

**Date:** 2025-11-25
**Author:** Tung Vu
**Status:** Draft

---

## Executive Summary

**Scope:** Full test design for Epic 3

**Risk Summary:**

- Total risks identified: 7
- High-priority risks (≥6): 3 (R-001, R-002, R-003, R-007)
- Critical categories: TECH (2), DATA (2), PERF (1)

**Coverage Summary:**

- P0 scenarios: 30 (60 hours)
- P1 scenarios: 29 (29 hours)
- P2/P3 scenarios: 34 (15.25 hours)
- **Total effort**: 104.25 hours (~13 days)

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description                                                  | Probability | Impact | Score | Mitigation                                                                                              | Owner     | Timeline   |
| ------- | -------- | ------------------------------------------------------------ | ----------- | ------ | ----- | ------------------------------------------------------------------------------------------------------- | --------- | ---------- |
| R-001   | TECH     | LLM doesn't consistently use [n] markers                     | 3           | 3      | **9** | (1) Strong system prompt (2) Few-shot examples (3) CitationService validation (4) Manual QA sampling   | Tech Lead | Before 3.2 |
| R-002   | DATA     | Citation marker [n] maps to wrong chunk                      | 2           | 3      | **6** | (1) Comprehensive unit tests (2) Validate marker ≤ chunk_count (3) Structured logging                  | QA Lead   | Before 3.2 |
| R-003   | PERF     | Cross-KB search exceeds 3s p95 with 10+ KBs                  | 2           | 3      | **6** | (1) Parallel async queries (2) Limit to top-3 KBs by usage (3) Redis caching (4) Load testing          | Backend   | Before 3.6 |
| R-007   | DATA     | LLM answer includes info NOT in source chunks (hallucination) | 2           | 3      | **6** | (1) Citation validation (2) Confidence scoring <50% = warning (3) User verification flow (Story 3.10)  | Tech Lead | Before 3.4 |

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description                                    | Probability | Impact | Score | Mitigation                                                 | Owner   |
| ------- | -------- | ---------------------------------------------- | ----------- | ------ | ----- | ---------------------------------------------------------- | ------- |
| R-005   | TECH     | SSE stream disconnects (network issues)        | 2           | 2      | **4** | (1) Reconnect logic (2) 60s state retention (3) Fallback to non-streaming | Backend |
| R-006   | SEC      | Cross-KB search bypasses permission checks     | 1           | 3      | **3** | (1) Unit test for unauthorized access (2) Integration test cross-tenant isolation | Security |
| R-004   | OPS      | Qdrant unavailable (vector DB downtime)        | 1           | 3      | **3** | (1) Graceful degradation (2) Cached results (3) Health check monitoring | DevOps  |

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks core journey + High risk (≥6) + No workaround

| Requirement                            | Test Level  | Risk Link         | Test Count | Owner | Notes                              |
| -------------------------------------- | ----------- | ----------------- | ---------- | ----- | ---------------------------------- |
| Citation extraction with valid markers | Unit        | R-001, R-002      | 8          | DEV   | BLOCK risk - regex + mapping logic |
| LLM citation format validation         | Integration | R-001, R-007      | 5          | QA    | Few-shot prompt testing            |
| Cross-KB permission enforcement        | Integration | R-006             | 4          | QA    | Security-critical                  |
| Citation-chunk mapping correctness     | Unit        | R-002             | 6          | DEV   | Edge cases: orphaned markers, OOB  |
| SSE streaming stability                | Integration | R-005             | 3          | QA    | Token/citation/done events         |
| Search audit logging                   | Integration | -                 | 2          | QA    | Compliance (FR54)                  |
| Citation UI rendering (E2E)            | E2E         | R-001             | 2          | QA    | Verify [1], [2] badges + click     |

**Total P0**: 30 tests, **60 hours**

**Test Examples:**

```python
# tests/unit/test_citation_service.py
async def test_extract_citations_with_valid_markers():
    """R-001, R-002: CitationService correctly extracts [1], [2] from answer."""
    chunks = [mock_chunk_1, mock_chunk_2]
    answer = "OAuth 2.0 [1] with MFA [2] ensures security."

    text, citations = service.extract_citations(answer, chunks)

    assert len(citations) == 2
    assert citations[0].number == 1
    assert citations[0].document_name == mock_chunk_1.document_name
    assert citations[0].excerpt == mock_chunk_1.chunk_text[:200]
    assert citations[1].number == 2

async def test_extract_citations_orphaned_marker():
    """R-002: Raises error if [3] exists but only 2 chunks provided."""
    chunks = [mock_chunk_1, mock_chunk_2]
    answer = "OAuth [1] and biometric [3] auth."  # [3] invalid

    with pytest.raises(CitationMappingError) as exc:
        service.extract_citations(answer, chunks)
    assert "Citation [3] exceeds chunk count" in str(exc.value)
```

```python
# tests/integration/test_search_citations.py
async def test_llm_citation_format_compliance(client, test_db):
    """R-001, R-007: LLM follows citation format with [n] markers."""
    # Setup: Index test document with rich metadata
    await seed_document(kb_id, "Test Doc.pdf", chunks=[...])

    # Execute: Search with citation instructions
    response = await client.post("/api/v1/search", json={
        "query": "authentication approach",
        "kb_ids": [kb_id]
    })

    assert response.status_code == 200
    data = response.json()

    # Validate: Answer has citations
    assert len(data["citations"]) > 0

    # Validate: Every [n] in answer has corresponding citation
    markers = re.findall(r'\[(\d+)\]', data["answer"])
    assert set(markers) == {str(c.number) for c in data["citations"]}

    # Validate: Citations have required fields
    for citation in data["citations"]:
        assert citation["document_name"]
        assert citation["excerpt"]
        assert len(citation["excerpt"]) <= 200  # Truncation
```

```typescript
// tests/e2e/search-citations.spec.ts
test('user can search and verify citations @p0 @smoke', async ({ page }) => {
  await page.goto('/dashboard');

  // Enter search query
  await page.fill('[data-testid="search-bar"]', 'authentication approach');
  await page.press('[data-testid="search-bar"]', 'Enter');

  // Wait for streaming to complete
  await page.waitForSelector('[data-testid="search-answer"]');
  await page.waitForSelector('[data-testid="search-done"]');

  // Verify citation markers exist
  const markers = page.locator('[data-testid^="citation-marker-"]');
  await expect(markers).toHaveCount(2); // Expecting [1], [2]

  // Verify CitationPanel populated
  await expect(page.locator('[data-testid="citation-card-1"]')).toBeVisible();
  await expect(page.locator('[data-testid="citation-card-2"]')).toBeVisible();

  // Click first citation marker
  await markers.first().click();

  // Verify citation panel highlights
  const card = page.locator('[data-testid="citation-card-1"]');
  await expect(card).toHaveClass(/highlighted/);

  // Verify citation metadata
  await expect(card.locator('[data-testid="doc-name"]')).toBeVisible();
  await expect(card.locator('[data-testid="excerpt"]')).toBeVisible();
});
```

---

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-5) + Common workflows

| Requirement                            | Test Level  | Risk Link | Test Count | Owner | Notes                         |
| -------------------------------------- | ----------- | --------- | ---------- | ----- | ----------------------------- |
| Semantic search returns relevant results | Integration | R-003     | 4          | QA    | Qdrant vector search          |
| Cross-KB search merging & ranking      | Integration | R-003     | 5          | QA    | Parallel queries, re-rank     |
| Confidence score calculation           | Unit        | R-007     | 4          | DEV   | Mitigates hallucination risk  |
| Citation preview & source navigation   | Component   | -         | 6          | DEV   | Important UX flow             |
| Command palette (⌘K) interaction       | Component   | -         | 4          | DEV   | Frequent usage pattern        |
| Confidence indicator display           | Component   | -         | 3          | DEV   | Trust signal (color-coded)    |
| Search performance < 3s p95            | Integration | R-003     | 3          | QA    | NFR requirement, load testing |

**Total P1**: 29 tests, **29 hours**

**Test Examples:**

```python
# tests/integration/test_cross_kb_search.py
async def test_cross_kb_search_merges_results(client, test_db):
    """R-003: Cross-KB search queries multiple collections and merges results."""
    # Setup: Create 2 KBs with indexed docs
    kb1_id = await create_kb(user_id, "Sales KB")
    kb2_id = await create_kb(user_id, "Tech KB")
    await seed_document(kb1_id, "Proposal.pdf", chunks=[...])
    await seed_document(kb2_id, "Architecture.md", chunks=[...])

    # Execute: Cross-KB search (kb_ids=None)
    start = time.time()
    response = await client.post("/api/v1/search", json={
        "query": "security best practices",
        "kb_ids": None  # Search ALL permitted KBs
    })
    elapsed = time.time() - start

    assert response.status_code == 200
    data = response.json()

    # Validate: Results from both KBs
    results = data["results"]
    kb_ids = {r["kb_id"] for r in results}
    assert len(kb_ids) == 2  # Both KBs represented

    # Validate: Results ranked by relevance (descending)
    scores = [r["relevance_score"] for r in results]
    assert scores == sorted(scores, reverse=True)

    # Validate: Performance < 3s p95
    assert elapsed < 3.0
```

```typescript
// src/components/citations/__tests__/citation-card.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { CitationCard } from '../citation-card';

test('citation preview shows doc metadata and excerpt', async () => {
  const citation = {
    number: 1,
    documentName: 'Acme Proposal.pdf',
    pageNumber: 14,
    sectionHeader: 'Authentication',
    excerpt: 'OAuth 2.0 with PKCE flow ensures secure token exchange...',
    charStart: 3450,
    charEnd: 3650,
  };

  const onPreview = vi.fn();
  const onOpenDoc = vi.fn();

  render(<CitationCard citation={citation} onPreview={onPreview} onOpen={onOpenDoc} />);

  // Verify metadata rendered
  expect(screen.getByText('[1]')).toBeInTheDocument();
  expect(screen.getByText('Acme Proposal.pdf')).toBeInTheDocument();
  expect(screen.getByText('Page 14')).toBeInTheDocument();
  expect(screen.getByText('Authentication')).toBeInTheDocument();

  // Verify excerpt truncated
  const excerpt = screen.getByTestId('excerpt');
  expect(excerpt.textContent).toContain('OAuth 2.0 with PKCE');
  expect(excerpt.textContent?.length).toBeLessThanOrEqual(250); // Truncation + ellipsis

  // Verify preview action
  fireEvent.click(screen.getByRole('button', { name: /preview/i }));
  expect(onPreview).toHaveBeenCalledWith(citation);

  // Verify open doc action
  fireEvent.click(screen.getByRole('button', { name: /open/i }));
  expect(onOpenDoc).toHaveBeenCalledWith(citation.documentId, citation.charStart, citation.charEnd);
});
```

---

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement                           | Test Level  | Risk Link | Test Count | Owner | Notes                                |
| ------------------------------------- | ----------- | --------- | ---------- | ----- | ------------------------------------ |
| "Find Similar" search                 | API         | -         | 4          | QA    | Semantic similarity via chunk embedding |
| Relevance explanation generation      | Component   | -         | 5          | DEV   | "Why is this relevant?" display      |
| Verify All Citations UI flow          | Component   | -         | 6          | DEV   | Power user feature                   |
| Layout stability (no shift)           | Component   | -         | 3          | DEV   | Visual regression prevention         |
| Quick Search (chunks only, no synthesis) | API      | -         | 3          | QA    | Command palette variant              |
| SSE reconnect logic                   | Integration | R-005     | 2          | QA    | Edge case: network disconnect        |
| Redis caching (query embeddings)      | Unit        | -         | 4          | DEV   | Performance optimization             |

**Total P2**: 27 tests, **13.5 hours**

---

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement                                 | Test Level  | Risk Link | Test Count | Owner | Notes                    |
| ------------------------------------------- | ----------- | --------- | ---------- | ----- | ------------------------ |
| Citation marker tooltip styling             | Component   | -         | 2          | DEV   | Cosmetic                 |
| "Use in Draft" button (Epic 4 handoff)      | E2E         | -         | 1          | QA    | Future feature hook      |
| Semantic distance score display             | Component   | -         | 2          | DEV   | Advanced detail          |
| Qdrant unavailable graceful degradation     | Integration | R-004     | 2          | QA    | Rare failure scenario    |

**Total P3**: 7 tests, **1.75 hours**

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] User can search and receive answer with citations (1 min)
- [ ] Citation markers [1], [2] are clickable (30s)
- [ ] Confidence indicator displays (30s)
- [ ] Cross-KB search returns results from multiple KBs (1 min)
- [ ] Search is logged to audit.events (45s)

**Total**: 5 scenarios

---

### P0 Tests (<15 min)

**Purpose**: Critical path validation

- [ ] Citation extraction with valid markers (Unit)
- [ ] LLM citation format validation (Integration)
- [ ] Cross-KB permission enforcement (Integration)
- [ ] Citation-chunk mapping correctness (Unit)
- [ ] SSE streaming stability (Integration)
- [ ] Search audit logging (Integration)
- [ ] Citation UI rendering (E2E)

**Total**: 30 scenarios

---

### P1 Tests (<30 min)

**Purpose**: Important feature coverage

- [ ] Semantic search returns relevant results (Integration)
- [ ] Cross-KB search merging & ranking (Integration)
- [ ] Confidence score calculation (Unit)
- [ ] Citation preview & source navigation (Component)
- [ ] Command palette (⌘K) interaction (Component)
- [ ] Confidence indicator display (Component)
- [ ] Search performance < 3s p95 (Integration)

**Total**: 29 scenarios

---

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage

- [ ] "Find Similar" search (API)
- [ ] Relevance explanation generation (Component)
- [ ] Verify All Citations UI flow (Component)
- [ ] Layout stability (Component)
- [ ] Quick Search (API)
- [ ] SSE reconnect logic (Integration)
- [ ] Redis caching (Unit)
- [ ] Citation marker tooltip styling (Component)
- [ ] Qdrant unavailable graceful degradation (Integration)

**Total**: 34 scenarios

---

## Resource Estimates

### Test Development Effort

| Priority  | Count | Hours/Test | Total Hours | Notes                                  |
| --------- | ----- | ---------- | ----------- | -------------------------------------- |
| P0        | 30    | 2.0        | 60          | Complex setup, BLOCK risks, security   |
| P1        | 29    | 1.0        | 29          | Standard coverage, integration heavy   |
| P2        | 27    | 0.5        | 13.5        | Simple scenarios, component tests      |
| P3        | 7     | 0.25       | 1.75        | Exploratory, edge cases                |
| **Total** | **93**| **-**      | **104.25**  | **~13 days (8hr workday)**             |

### Prerequisites

**Test Data:**

- `SearchChunkFactory` (faker-based, auto-cleanup) - Generate mock chunks with metadata
- `SearchResponseFixture` (setup/teardown) - Mock LLM responses with citations
- `QdrantMockFactory` - Mock vector search results with scores

**Tooling:**

- **pytest** for backend unit/integration tests
- **testcontainers** for Qdrant/Redis in integration tests
- **Vitest + React Testing Library** for component tests
- **Playwright** for E2E tests
- **k6** for load/performance testing (Story 3.1, 3.6)

**Environment:**

- Qdrant test cluster (in-memory or testcontainer)
- Redis test instance (Docker or testcontainer)
- LiteLLM mock server (for deterministic LLM responses in tests)
- PostgreSQL test DB (Epic 1 infrastructure)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions - BLOCK risks)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths (P0)**: ≥80% code coverage
- **Security scenarios (R-006)**: 100% pass rate
- **Business logic (CitationService)**: ≥70% coverage
- **Edge cases (orphaned markers, OOB)**: ≥50% coverage

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] R-001 (LLM citation quality) mitigated: Few-shot examples + validation tests pass
- [ ] R-002 (Citation mapping) mitigated: Unit tests cover all edge cases
- [ ] R-003 (Performance) mitigated: Load test confirms p95 < 3s with 10 KBs
- [ ] R-007 (Hallucination) mitigated: Confidence scoring + verification flow tested
- [ ] Security tests (R-006) pass 100%
- [ ] No score=9 risks in OPEN status

---

## Mitigation Plans

### R-001: LLM Citation Quality (Score: 9)

**Mitigation Strategy:**
1. **Strong system prompt** with explicit citation instructions and format examples
2. **Few-shot examples** in prompt (3-5 examples of correct citation usage)
3. **CitationService validation** - Reject responses with invalid markers
4. **Manual QA sampling** - Review 50 real queries for citation accuracy in beta

**Owner:** Tech Lead
**Timeline:** Before Story 3.2 implementation
**Status:** Planned
**Verification:** Integration test `test_llm_citation_format_compliance` passes 100 consecutive queries

---

### R-002: Citation Mapping Errors (Score: 6)

**Mitigation Strategy:**
1. **Comprehensive unit tests** - Cover all edge cases (orphaned markers, out-of-bounds, duplicate markers)
2. **Validation logic** - Assert marker number ≤ chunk count before mapping
3. **Structured logging** - Log marker extraction and mapping for debugging

**Owner:** QA Lead
**Timeline:** Before Story 3.2 implementation
**Status:** Planned
**Verification:** Unit tests `test_extract_citations_orphaned_marker`, `test_extract_citations_out_of_bounds` pass

---

### R-003: Cross-KB Search Performance (Score: 6)

**Mitigation Strategy:**
1. **Parallel async queries** - Use `asyncio.gather()` to query all KBs concurrently
2. **Limit to top-3 KBs by usage** - Default to recent/frequent KBs if >10 permitted
3. **Redis caching** - Cache query embeddings (1hr TTL)
4. **Load testing** - k6 script simulating 20 users × 5 searches

**Owner:** Backend Dev
**Timeline:** Before Story 3.6 implementation
**Status:** Planned
**Verification:** Load test confirms p95 < 3s with 10 KBs and 20 concurrent users

---

### R-007: LLM Hallucination (Score: 6)

**Mitigation Strategy:**
1. **Citation validation** - CitationService verifies all facts map to chunks
2. **Confidence scoring** - Score <50% triggers red warning "Low confidence - verify sources"
3. **User verification flow** - Story 3.10 "Verify All Citations" UI for systematic review

**Owner:** Tech Lead
**Timeline:** Before Story 3.4 (confidence UI)
**Status:** Planned
**Verification:** Confidence calculation unit tests pass, manual review of low-confidence queries

---

## Assumptions and Dependencies

### Assumptions

1. **Qdrant metadata richness** - Epic 2 indexed chunks with `page_number`, `section_header`, `char_start`, `char_end`
   - **Validation**: Integration test `test_semantic_search_returns_relevant_results` verifies metadata presence
   - **Fallback**: If metadata missing, citations show doc-level only (less precise but functional)

2. **LLM instruction following** - GPT-4 reliably follows citation format 90%+ of the time
   - **Validation**: Integration test with 100+ queries samples
   - **Fallback**: Switch to JSON mode for structured output if accuracy <90%

3. **User behavior** - Users will verify citations before exporting/sharing answers
   - **Validation**: Onboarding wizard enforces verification demo
   - **Fallback**: Warn on export "Have you verified all sources?"

4. **Network reliability** - SSE streams don't drop frequently (<5% disconnect rate)
   - **Validation**: Integration test simulates disconnect + reconnect
   - **Fallback**: Reconnect logic with 60s state retention

### Dependencies

1. **Epic 2 completion** - Documents MUST be indexed with rich metadata
   - **Required by**: Story 3.1 (search), Story 3.2 (citations)
   - **Blocker if missing**: Cannot extract page/section for citations

2. **Epic 1 authentication** - Current user required for permission checks
   - **Required by**: Story 3.1 (permission enforcement)
   - **Blocker if missing**: Cross-tenant data leak risk

3. **Qdrant deployment** - Vector DB accessible from backend
   - **Required by**: Story 3.1
   - **Blocker if missing**: No semantic search possible

4. **LiteLLM proxy** - LLM API available for embeddings + synthesis
   - **Required by**: Story 3.1 (embeddings), Story 3.2 (synthesis)
   - **Blocker if missing**: Fallback to keyword search only (major degradation)

### Risks to Plan

- **Risk**: LLM API rate limits during load testing
  - **Impact**: Cannot validate p95 < 3s requirement
  - **Contingency**: Use mocked LLM responses for load tests, manual verification in staging

- **Risk**: Qdrant performance degrades with >10 collections
  - **Impact**: p95 > 3s, fails NFR
  - **Contingency**: Implement KB usage-based filtering (top-3 recent KBs by default)

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: __________ Date: __________
- [ ] Tech Lead: __________ Date: __________
- [ ] QA Lead: __________ Date: __________

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework (6 categories, scoring, gate engine)
- `probability-impact.md` - Risk scoring methodology (P×I matrix, thresholds)
- `test-levels-framework.md` - Test level selection (E2E vs API vs Component vs Unit)
- `test-priorities-matrix.md` - P0-P3 prioritization criteria (risk-based mapping)

### Related Documents

- PRD: [docs/PRD.md](PRD.md)
- Epic: [docs/epics/epic-3-semantic-search-citations.md](epics/epic-3-semantic-search-citations.md)
- Architecture: [docs/architecture.md](architecture.md)
- Tech Spec: [docs/sprint-artifacts/tech-spec-epic-3.md](sprint-artifacts/tech-spec-epic-3.md)

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
