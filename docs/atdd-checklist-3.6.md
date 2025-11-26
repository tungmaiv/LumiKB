# ATDD Checklist: Story 3.6 - Cross-KB Search & Merging

**Date:** 2025-11-25
**Story ID:** 3.6
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.6 - Cross-KB Search & Merging

**Description:**
Enable users to search across ALL their permitted knowledge bases by default, with results merged and ranked by relevance. This dramatically improves discoverability by removing the need to know which KB contains the information.

**Priority:** P1 - High (Core functionality enhancement)

**Risk Level:** MEDIUM
- **R-003**: Cross-KB search performance (Score: 6 - MITIGATE) - Parallel queries required
- **R-006**: Permission bypass (Score: 6 - MITIGATE) - Must enforce cross-tenant isolation

**User Value:**
- Find information without knowing which KB it's in
- Discover connections across organizational silos (Sales KB + Engineering KB)
- Faster answers for power users with many KBs

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.6.1 | Search with kb_ids=None queries all permitted KBs | Integration | `test_cross_kb_search.py::test_cross_kb_search_queries_all_permitted_kbs` | ❌ RED |
| AC-3.6.1 | Only permitted KBs are queried (security) | Integration | `test_cross_kb_search.py::test_cross_kb_search_respects_permissions` | ❌ RED |
| AC-3.6.2 | Results merged and ranked by relevance_score | Integration | `test_cross_kb_search.py::test_cross_kb_results_ranked_by_relevance` | ❌ RED |
| AC-3.6.2 | Limit applies across all KBs (not per-KB) | Integration | `test_cross_kb_search.py::test_cross_kb_search_merges_results_with_limit` | ❌ RED |
| AC-3.6.3 | Each result includes kb_id and kb_name | Integration | `test_cross_kb_search.py::test_cross_kb_results_include_kb_name` | ❌ RED |
| AC-3.6.4 | Performance < 5s for ≤10 KBs (smoke test) | Integration | `test_cross_kb_search.py::test_cross_kb_search_performance_basic_timing` | ❌ RED |
| AC-3.6.4 | Queries run in parallel (not sequential) | Integration | `test_cross_kb_search.py::test_cross_kb_search_uses_parallel_queries` | ❌ RED |

**Total Tests**: 10 integration tests (7 primary + 3 edge cases)

---

## Test Files Created

### Integration Tests

**File**: `backend/tests/integration/test_cross_kb_search.py`

**Tests (10 integration tests):**
1. ✅ `test_cross_kb_search_queries_all_permitted_kbs` - Default behavior
2. ✅ `test_cross_kb_search_respects_permissions` - Security (R-006)
3. ✅ `test_cross_kb_results_ranked_by_relevance` - Ranking logic
4. ✅ `test_cross_kb_search_merges_results_with_limit` - Limit enforcement
5. ✅ `test_cross_kb_results_include_kb_name` - Metadata display
6. ✅ `test_cross_kb_search_performance_basic_timing` - Performance smoke test
7. ✅ `test_cross_kb_search_uses_parallel_queries` - Parallelization (R-003)
8. ✅ `test_cross_kb_search_with_no_results` - Edge case (empty results)
9. ✅ `test_cross_kb_search_with_explicit_kb_ids` - Subset filtering
10. ✅ Edge cases covered

---

## Supporting Infrastructure

### Data Flow

```
User submits query with kb_ids=None
    ↓
SearchService.search(query, kb_ids=None, user_id)
    ↓
Get all KBs user has READ permission on
    permission_service.get_permitted_kbs(user_id, action="READ")
    → Returns [KB1, KB2, KB3, ...]
    ↓
For each KB: Launch parallel Qdrant query
    asyncio.gather(
        search_single_kb(KB1, embedding, limit),
        search_single_kb(KB2, embedding, limit),
        search_single_kb(KB3, embedding, limit),
        ...
    )
    ↓
Merge all results into single list
    all_results = KB1_results + KB2_results + KB3_results + ...
    ↓
Re-rank by relevance_score (descending)
    all_results.sort(key=lambda r: r.relevance_score, reverse=True)
    ↓
Apply limit
    top_results = all_results[:limit]
    ↓
Enrich with KB metadata
    for result in top_results:
        result["kb_name"] = kb_metadata[result["kb_id"]]["name"]
    ↓
Return to user
```

### Response Schema Update

**Updated SearchResultSchema** (from Story 3.1):

```python
class SearchResultSchema(BaseModel):
    document_id: str
    document_name: str
    kb_id: str
    kb_name: str  # NEW for Story 3.6
    chunk_text: str
    relevance_score: float
    page_number: int | None
    section_header: str | None
```

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 10 tests written and failing
- [x] Cross-KB query logic defined
- [x] Performance expectations documented

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Update SearchService to Handle kb_ids=None

- [ ] Modify `SearchService.search()` signature:
  ```python
  async def search(
      self,
      query: str,
      kb_ids: list[str] | None,  # None = all permitted KBs
      user_id: str,
      limit: int = 10,
  ) -> list[SearchResult]:
      """Search across one or more KBs.

      If kb_ids is None, search ALL KBs user has READ permission on.
      """
      if kb_ids is None:
          # Get all permitted KBs for user
          kb_ids = await self.get_permitted_kb_ids(user_id)

      # Proceed with search
      ...
  ```
- [ ] Run test: `test_cross_kb_search_queries_all_permitted_kbs`
- [ ] ✅ Test passes (queries all permitted KBs)

#### Task 2: Implement Permission Filtering

- [ ] Create `get_permitted_kb_ids()` method:
  ```python
  async def get_permitted_kb_ids(self, user_id: str) -> list[str]:
      """Get all KB IDs user has READ permission on."""
      from app.services import PermissionService

      permission_service = PermissionService(self.db)

      # Query KBs where user is owner OR has explicit READ permission
      permitted_kbs = await permission_service.get_user_kbs(
          user_id=user_id,
          required_action="READ"
      )

      return [kb.id for kb in permitted_kbs]
  ```
- [ ] Run test: `test_cross_kb_search_respects_permissions`
- [ ] ✅ Test passes (permission filtering works)

#### Task 3: Implement Parallel Qdrant Queries

- [ ] Modify search logic to use `asyncio.gather()`:
  ```python
  async def search(self, query: str, kb_ids: list[str], ...):
      # 1. Generate embedding
      embedding = await self.litellm_client.embed(query)

      # 2. Query all KBs in parallel
      search_tasks = [
          self.search_single_kb(kb_id, embedding, limit)
          for kb_id in kb_ids
      ]

      kb_results = await asyncio.gather(*search_tasks)

      # 3. Merge results
      all_results = []
      for results in kb_results:
          all_results.extend(results)

      # 4. Re-rank and limit (next task)
      ...
  ```
- [ ] Create `search_single_kb()` helper:
  ```python
  async def search_single_kb(
      self,
      kb_id: str,
      embedding: list[float],
      limit: int
  ) -> list[SearchResult]:
      """Search a single KB's Qdrant collection."""
      collection_name = f"kb_{kb_id}"

      results = await self.qdrant_client.search(
          collection_name=collection_name,
          query_vector=embedding,
          limit=limit,
          with_payload=True
      )

      return [
          SearchResult(
              kb_id=kb_id,
              relevance_score=hit.score,
              **hit.payload
          )
          for hit in results
      ]
  ```
- [ ] Run test: `test_cross_kb_search_uses_parallel_queries`
- [ ] ✅ Test passes (parallel execution confirmed)

#### Task 4: Merge and Re-Rank Results

- [ ] Implement result merging and ranking:
  ```python
  # After asyncio.gather
  all_results = []
  for kb_results in kb_results:
      all_results.extend(kb_results)

  # Sort by relevance_score (descending)
  all_results.sort(key=lambda r: r.relevance_score, reverse=True)

  # Apply limit across all KBs
  top_results = all_results[:limit]

  return top_results
  ```
- [ ] Run tests:
  - `test_cross_kb_results_ranked_by_relevance`
  - `test_cross_kb_search_merges_results_with_limit`
- [ ] ✅ Tests pass (ranking and limiting work)

#### Task 5: Enrich Results with KB Metadata

- [ ] Add KB name to each result:
  ```python
  # After merging and ranking
  kb_metadata = await self.get_kb_metadata(kb_ids)

  for result in top_results:
      kb = kb_metadata.get(result.kb_id)
      if kb:
          result.kb_name = kb.name

  return top_results
  ```
- [ ] Create `get_kb_metadata()` helper:
  ```python
  async def get_kb_metadata(self, kb_ids: list[str]) -> dict[str, KB]:
      """Fetch KB metadata for enrichment."""
      from app.models import KnowledgeBase

      kbs = await self.db.execute(
          select(KnowledgeBase).where(KnowledgeBase.id.in_(kb_ids))
      )

      return {kb.id: kb for kb in kbs.scalars().all()}
  ```
- [ ] Run test: `test_cross_kb_results_include_kb_name`
- [ ] ✅ Test passes (KB metadata included)

#### Task 6: Performance Optimization

- [ ] Add Redis caching for query embeddings:
  ```python
  async def embed_with_cache(self, query: str) -> list[float]:
      """Generate embedding with Redis caching."""
      import hashlib

      cache_key = f"embedding:{hashlib.sha256(query.encode()).hexdigest()}"

      # Check cache
      cached = await self.redis.get(cache_key)
      if cached:
          return json.loads(cached)

      # Generate embedding
      embedding = await self.litellm_client.embed(query)

      # Cache for 1 hour
      await self.redis.setex(cache_key, 3600, json.dumps(embedding))

      return embedding
  ```
- [ ] Run test: `test_cross_kb_search_performance_basic_timing`
- [ ] ✅ Test passes (performance acceptable)

#### Task 7: Handle Edge Cases

- [ ] Handle no results gracefully:
  ```python
  if len(all_results) == 0:
      return {
          "results": [],
          "query": query,
          "kb_count": len(kb_ids),
          "message": "No results found across your knowledge bases"
      }
  ```
- [ ] Support explicit KB subset:
  ```python
  # User can still specify kb_ids=[...] to filter
  if kb_ids is not None and len(kb_ids) > 0:
      # Use provided KB list (no permission expansion)
      # But still validate user has access
      kb_ids = await self.validate_kb_access(user_id, kb_ids)
  else:
      # kb_ids=None → all permitted KBs
      kb_ids = await self.get_permitted_kb_ids(user_id)
  ```
- [ ] Run tests:
  - `test_cross_kb_search_with_no_results`
  - `test_cross_kb_search_with_explicit_kb_ids`
- [ ] ✅ Tests pass (edge cases handled)

#### Task 8: Frontend Integration (Optional)

- [ ] Update search UI to show KB tags:
  ```tsx
  {results.map(result => (
    <SearchResultCard key={result.id}>
      <div className="flex items-center gap-2">
        <h3>{result.document_name}</h3>
        <Badge variant="secondary">{result.kb_name}</Badge>
      </div>
      <p>{result.chunk_text}</p>
    </SearchResultCard>
  ))}
  ```
- [ ] Add filter toggle: "Search current KB only" vs "Search all KBs"
- [ ] ✅ UI displays KB source tags

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 10 tests written and failing
- ✅ Tests define cross-KB search behavior
- ✅ Failures due to missing parallel query logic

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (Handle kb_ids=None) - API contract
2. Task 2 (Permission filtering) - Security (R-006)
3. Task 3 (Parallel queries) - Performance (R-003)
4. Task 4 (Merge and rank) - Core logic
5. Task 5 (KB metadata) - Display
6. Task 6 (Performance optimization) - Caching
7. Task 7 (Edge cases) - Robustness
8. Task 8 (Frontend integration) - UX

### REFACTOR Phase (After all tests green)

1. Extract parallel query logic to reusable utility
2. Add monitoring: track cross-KB query count, avg KBs per query
3. Optimize: Cache KB permission lookups (user_id → permitted_kb_ids)
4. Add telemetry: p95 latency for cross-KB queries
5. Code review with senior dev
6. Commit: "feat: implement cross-KB search with parallel queries (Story 3.6)"

---

## Running Tests

### Run All Story 3.6 Tests

```bash
cd backend
pytest tests/integration/test_cross_kb_search.py -v

# Expected: All tests FAIL (RED phase)
```

### Run Specific Test

```bash
# Test permission filtering (CRITICAL - R-006)
pytest tests/integration/test_cross_kb_search.py::test_cross_kb_search_respects_permissions -vv

# Test parallel execution (CRITICAL - R-003)
pytest tests/integration/test_cross_kb_search.py::test_cross_kb_search_uses_parallel_queries -vv
```

### Run After Implementation

```bash
# Run full Story 3.6 test suite
pytest tests/integration/test_cross_kb_search.py -v

# Expected: All 10 tests PASS (GREEN phase)
```

---

## Performance Benchmarks

### Target Performance (NFR-2, NFR-3)

| Scenario | Target | Measurement |
|----------|--------|-------------|
| Single KB search | < 1s (p95) | Manual load test |
| Cross-KB (3 KBs) | < 2s (p95) | Manual load test |
| Cross-KB (10 KBs) | < 3s (p95) | Manual load test |
| Integration test | < 5s (smoke) | `test_cross_kb_search_performance_basic_timing` |

### Performance Formula

```
Expected Time (parallel) ≈ max(single_kb_times) + merge_overhead
Expected Time (sequential) = sum(single_kb_times)

Example:
- KB1: 0.8s, KB2: 0.9s, KB3: 0.7s
- Parallel: ~0.9s + 0.1s = 1.0s
- Sequential: 0.8 + 0.9 + 0.7 = 2.4s
- Speedup: 2.4x
```

### Optimization Strategies

1. **Parallel Queries** (CRITICAL)
   - Use `asyncio.gather()` for concurrent Qdrant requests
   - Target: N KBs in ~1x time (not Nx)

2. **Embedding Caching** (HIGH)
   - Redis cache: `embedding:{query_hash} → vector`
   - TTL: 1 hour (queries repeat frequently)
   - Speedup: ~200ms saved per cached query

3. **Permission Caching** (MEDIUM)
   - Cache: `user:{user_id}:permitted_kbs → [kb_ids]`
   - TTL: 5 minutes (permissions change infrequently)
   - Invalidate on KB permission change

4. **Result Caching** (LOW - Deferred)
   - Cache full search results: `search:{query_hash}:{kb_ids} → results`
   - Complex invalidation (document updates)
   - Consider for Epic 5

---

## Security Considerations

### R-006: Permission Bypass Mitigation

**Risk**: User accesses KBs they don't have permission to via cross-KB search

**Mitigation**:
1. **Always filter by permissions** before querying:
   ```python
   if kb_ids is None:
       kb_ids = await self.get_permitted_kb_ids(user_id)
   else:
       # Validate user has access to requested KBs
       kb_ids = await self.validate_kb_access(user_id, kb_ids)
   ```

2. **Test coverage**: `test_cross_kb_search_respects_permissions`
   - User A cannot see User B's KBs in cross-KB search
   - MUST pass 100% (security critical)

3. **Audit logging**: Log cross-KB queries with KB list:
   ```python
   await audit_service.log_event(
       user_id=user_id,
       action="cross_kb_search",
       details={
           "query": query,
           "kb_ids_queried": kb_ids,
           "result_count": len(results)
       }
   )
   ```

### Permission Check Performance

**Problem**: Checking permissions for 10 KBs on every query is slow

**Solution**: Cache permission lookups
```python
@cached(ttl=300)  # 5 minutes
async def get_permitted_kb_ids(user_id: str) -> list[str]:
    # Expensive DB query
    ...
```

**Cache Invalidation**:
- Invalidate on KB permission change
- Invalidate on user role change
- TTL: 5 minutes (safety fallback)

---

## Known Issues / TODOs

### Issue 1: Result Quality with Many KBs

**Problem**: User with 50 KBs gets diluted results (limit=10 across all 50 KBs)

**Solution** (Future):
- Increase default limit for cross-KB search: `limit = max(10, num_kbs * 2)`
- Add "More Results" pagination
- Consider KB-level relevance filtering (exclude KBs with max_score < 0.3)

### Issue 2: KB Explosion

**Problem**: User with 100+ KBs → 100+ parallel Qdrant queries

**Solution** (Future):
- Limit max KBs per query: `kb_ids = permitted_kb_ids[:20]` (top 20 by last access)
- Prompt user to select KBs for search
- Add "Smart KB Selection" (ML model predicts relevant KBs)

### Issue 3: Slow KB Queries

**Problem**: One slow KB (5s) blocks entire cross-KB response

**Solution** (Future):
- Timeout per-KB query: `async with timeout(3.0): await search_kb(...)`
- Return partial results if some KBs timeout
- Log slow KB warnings for admin investigation

---

## Dependencies

### Backend Services

- **PermissionService** - `get_user_kbs(user_id, action="READ")`
- **QdrantClient** - `search(collection_name, query_vector, limit)`
- **LiteLLMClient** - `embed(query)` (existing from Story 3.1)
- **Redis** - Caching for embeddings and permissions

### Database Schema

- No new tables (read-only against Epic 2 data)
- Uses existing: `knowledge_bases`, `kb_permissions`, `documents`

---

## Next Steps for DEV Team

### Immediate Actions

1. **Review parallel query pattern**:
   - Understand `asyncio.gather()` for concurrent Qdrant requests
   - Review Python async/await best practices

2. **Run failing tests** to confirm RED phase:
   ```bash
   pytest tests/integration/test_cross_kb_search.py -v
   # Expected: All FAIL
   ```

3. **Start GREEN phase** with Task 1 (Handle kb_ids=None)

### Definition of Done

- [ ] All 10 tests pass
- [ ] Cross-KB search queries all permitted KBs
- [ ] Results merged and ranked correctly
- [ ] Permission filtering enforced (R-006)
- [ ] Parallel queries implemented (R-003)
- [ ] Performance < 5s for ≤10 KBs
- [ ] KB metadata (kb_name) displayed
- [ ] Edge cases handled (no results, explicit subset)
- [ ] Code reviewed by senior dev
- [ ] Merged to main branch

---

## Knowledge Base References Applied

**Frameworks:**
- `test-levels-framework.md` - Integration test level
- `test-quality.md` - Performance testing

**Risk Management:**
- `test-design-epic-3.md` - R-003 (performance) and R-006 (security) assessment

**Patterns:**
- `network-first.md` - Parallel query pattern

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.6 - Cross-KB Search & Merging
**Primary Test Level**: Integration

**Failing Tests Created**:
- Integration tests: 10 tests in `backend/tests/integration/test_cross_kb_search.py`

**Supporting Infrastructure**:
- Parallel query logic (asyncio.gather)
- Permission filtering service
- Result merging and ranking
- Redis caching for performance

**Implementation Checklist**:
- Total tasks: 8 tasks
- Estimated effort: 8-10 hours

**Risk Mitigation**:
- R-003 (Score 6): Cross-KB performance (parallel queries)
- R-006 (Score 6): Permission bypass (security filtering)

**Dependencies**:
- Story 3.1 (Semantic Search) must be complete
- PermissionService from Epic 2
- Qdrant integration
- Redis caching

**Next Steps for DEV Team**:
1. Review parallel query pattern (`asyncio.gather`)
2. Run failing tests: `pytest tests/integration/test_cross_kb_search.py -v`
3. Implement Task 1 (Handle kb_ids=None)
4. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.6.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
