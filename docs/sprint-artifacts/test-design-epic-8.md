# Test Design Document: Epic 8 - GraphRAG Integration

**Version:** 1.0
**Last Updated:** 2025-12-08
**Author:** Test Engineering Team
**Epic Reference:** Epic 8 - GraphRAG Integration

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Risk Assessment](#risk-assessment)
3. [Test Coverage Plan](#test-coverage-plan)
4. [Test Execution Order](#test-execution-order)
5. [Resource Estimates](#resource-estimates)
6. [Quality Gate Criteria](#quality-gate-criteria)
7. [Mitigation Plans for High-Priority Risks](#mitigation-plans)
8. [Test Scenario Details](#test-scenario-details)

---

## Executive Summary

### Epic Overview

Epic 8 introduces GraphRAG (Graph-based Retrieval Augmented Generation) capabilities to LumiKB, integrating Neo4j as a knowledge graph database alongside the existing Qdrant vector store. This enables enhanced retrieval through entity extraction, relationship mapping, and graph-augmented search.

### Key Components

| Component | Description | Complexity |
|-----------|-------------|------------|
| Neo4j Infrastructure | Docker setup, Python driver, health checks | Medium |
| Domain Data Model | PostgreSQL schema for domains, entity types, relationships | Medium |
| System Templates | Pre-built domain templates for common use cases | Low |
| Entity Extraction | LLM-based NER with domain schema awareness | High |
| Graph Query Service | Neo4j queries for entity search, path finding, neighborhoods | High |
| Graph-Augmented Retrieval | Vector-first + graph augmentation strategy | High |
| Schema Evolution | Version tracking and re-extraction workflows | Medium |
| Batch Processing | Dedicated Celery worker for large-scale operations | Medium |

### Test Summary

| Metric | Value |
|--------|-------|
| Total Stories | 15 |
| Total Risks Identified | 18 |
| High-Priority Risks (score ≥6) | 8 |
| Total Test Scenarios | 142 |
| Estimated Test Effort | 168 hours |

### Risk Distribution

- **Critical Infrastructure (8-1):** Neo4j connectivity, health checks
- **Data Model (8-2 to 8-4):** Schema design, migration, templates
- **Core Features (8-8 to 8-11):** Entity extraction, graph queries, retrieval
- **Advanced Features (8-12 to 8-15):** Strategy abstraction, schema evolution

---

## Risk Assessment

### Risk Scoring Matrix

| Probability | Impact | Score |
|-------------|--------|-------|
| High (3) | High (3) | 9 |
| High (3) | Medium (2) | 6 |
| Medium (2) | High (3) | 6 |
| Medium (2) | Medium (2) | 4 |
| Low (1) | High (3) | 3 |

### Identified Risks

| ID | Risk Description | Probability | Impact | Score | Affected Stories |
|----|------------------|-------------|--------|-------|------------------|
| R-001 | Neo4j connection failures in Docker network | Medium (2) | High (3) | 6 | 8-1, 8-8, 8-10 |
| R-002 | LLM entity extraction inconsistency | High (3) | High (3) | 9 | 8-8, 8-9, 8-13 |
| R-003 | Entity deduplication false positives/negatives | High (3) | Medium (2) | 6 | 8-8 |
| R-004 | Graph query performance degradation at scale | Medium (2) | High (3) | 6 | 8-10, 8-11 |
| R-005 | Vector-graph result fusion quality issues | Medium (2) | High (3) | 6 | 8-11, 8-12 |
| R-006 | Domain schema migration data loss | Low (1) | High (3) | 3 | 8-2, 8-14 |
| R-007 | System template seeding failures | Low (1) | Medium (2) | 2 | 8-3 |
| R-008 | KB-domain linking permission bypass | Medium (2) | High (3) | 6 | 8-7 |
| R-009 | Cross-KB entity contamination | Medium (2) | High (3) | 6 | 8-8, 8-10 |
| R-010 | Re-extraction job corruption on failure | Medium (2) | Medium (2) | 4 | 8-14, 8-15 |
| R-011 | Rate limiting ineffective under load | Medium (2) | Medium (2) | 4 | 8-15 |
| R-012 | Cypher injection vulnerabilities | Low (1) | High (3) | 3 | 8-10, 8-11 |
| R-013 | Domain API access control bypass | Medium (2) | High (3) | 6 | 8-5 |
| R-014 | Schema enrichment suggestion spam | Low (1) | Low (1) | 1 | 8-13 |
| R-015 | Strategy registry race conditions | Low (1) | Medium (2) | 2 | 8-12 |
| R-016 | LLM domain recommendation unreliability | Medium (2) | Low (1) | 2 | 8-4 |
| R-017 | APOC plugin compatibility issues | Low (1) | High (3) | 3 | 8-1 |
| R-018 | Batch job progress tracking desync | Medium (2) | Medium (2) | 4 | 8-15 |

### High-Priority Risks Summary (Score ≥ 6)

1. **R-002 (Score 9):** LLM entity extraction inconsistency
2. **R-001 (Score 6):** Neo4j connection failures
3. **R-003 (Score 6):** Entity deduplication accuracy
4. **R-004 (Score 6):** Graph query performance
5. **R-005 (Score 6):** Vector-graph fusion quality
6. **R-008 (Score 6):** KB-domain permission bypass
7. **R-009 (Score 6):** Cross-KB entity contamination
8. **R-013 (Score 6):** Domain API access control

---

## Test Coverage Plan

### Priority Levels

| Priority | Description | Coverage Target |
|----------|-------------|-----------------|
| P0 | Critical path functionality | 100% |
| P1 | Core features with high risk | 95% |
| P2 | Standard features | 85% |
| P3 | Edge cases and enhancements | 70% |

### Story Coverage Matrix

| Story | Description | Priority | Unit Tests | Integration Tests | E2E Tests |
|-------|-------------|----------|------------|-------------------|-----------|
| 8-1 | Neo4j Docker Infrastructure | P0 | 5 | 4 | 2 |
| 8-2 | Domain Data Model | P0 | 8 | 5 | - |
| 8-3 | System Domain Templates | P1 | 4 | 3 | - |
| 8-4 | LLM Domain Recommendation | P2 | 4 | 3 | 1 |
| 8-5 | Domain Management API | P0 | 12 | 10 | 3 |
| 8-6 | Domain Management UI | P1 | 6 | - | 4 |
| 8-7 | KB-Domain Linking | P0 | 6 | 5 | 2 |
| 8-8 | Entity Extraction Service | P0 | 15 | 8 | 2 |
| 8-9 | Document Processing Integration | P0 | 6 | 5 | 2 |
| 8-10 | Graph Query Service | P0 | 12 | 8 | 2 |
| 8-11 | Graph-Augmented Retrieval | P0 | 10 | 6 | 3 |
| 8-12 | Retrieval Strategy Abstraction | P1 | 8 | 4 | 2 |
| 8-13 | LLM Schema Enrichment | P2 | 8 | 5 | 2 |
| 8-14 | Schema Evolution | P1 | 10 | 6 | 2 |
| 8-15 | Batch Re-processing Worker | P1 | 8 | 5 | 2 |

**Total:** 122 unit tests, 77 integration tests, 29 E2E tests = **142 tests**

---

## Test Execution Order

### Phase 1: Infrastructure Foundation (Week 1)

1. **8-1 Neo4j Docker Infrastructure**
   - Docker compose verification
   - Python driver connectivity
   - Health check endpoint
   - APOC plugin availability

2. **8-2 Domain Data Model**
   - Alembic migration up/down
   - Model relationships
   - Foreign key constraints
   - Index verification

### Phase 2: Domain Management (Week 1-2)

3. **8-3 System Domain Templates**
   - Template seeding
   - Clone functionality
   - Template protection

4. **8-5 Domain Management API**
   - CRUD operations
   - Access control
   - Validation rules

5. **8-4 LLM Domain Recommendation**
   - Document analysis
   - Recommendation generation

6. **8-6 Domain Management UI**
   - UI component tests
   - E2E workflows

7. **8-7 KB-Domain Linking**
   - Link creation/removal
   - Permission propagation

### Phase 3: Entity Extraction Core (Week 2-3)

8. **8-8 Entity Extraction Service**
   - LLM prompt testing
   - Entity storage
   - Deduplication logic
   - Confidence scoring

9. **8-9 Document Processing Integration**
   - Celery task integration
   - Pipeline modification
   - Error handling

### Phase 4: Graph Querying (Week 3)

10. **8-10 Graph Query Service**
    - Entity search
    - Neighborhood queries
    - Path finding
    - Subgraph extraction

11. **8-11 Graph-Augmented Retrieval**
    - Vector-first flow
    - Graph augmentation
    - Result fusion

12. **8-12 Retrieval Strategy Abstraction**
    - Strategy registry
    - Auto-selection
    - KB configuration

### Phase 5: Schema Management (Week 4)

13. **8-13 LLM Schema Enrichment**
    - Unrecognized entity capture
    - Suggestion aggregation
    - Accept/reject workflow

14. **8-14 Schema Evolution**
    - Version tracking
    - Drift detection
    - Re-extraction jobs

15. **8-15 Batch Re-processing Worker**
    - Dedicated queue
    - Rate limiting
    - Progress tracking

---

## Resource Estimates

### Test Development Effort

| Phase | Stories | Unit Tests | Integration | E2E | Hours |
|-------|---------|------------|-------------|-----|-------|
| Infrastructure | 8-1, 8-2 | 13 | 9 | 2 | 20 |
| Domain Management | 8-3 to 8-7 | 32 | 21 | 10 | 48 |
| Entity Extraction | 8-8, 8-9 | 21 | 13 | 4 | 32 |
| Graph Querying | 8-10, 8-11, 8-12 | 30 | 18 | 7 | 40 |
| Schema Management | 8-13, 8-14, 8-15 | 26 | 16 | 6 | 28 |
| **Total** | **15** | **122** | **77** | **29** | **168** |

### Test Environment Requirements

| Resource | Specification | Purpose |
|----------|---------------|---------|
| Neo4j | Community 5.x, 2GB RAM | Graph storage |
| PostgreSQL | 14+, 512MB RAM | Domain metadata |
| Qdrant | Latest, 1GB RAM | Vector search |
| LiteLLM | With NER model access | Entity extraction |
| Redis | 6.x | Task queuing, progress tracking |
| Celery Workers | 2 workers minimum | Background processing |

---

## Quality Gate Criteria

### Story Completion Gates

| Gate | Criteria | Required |
|------|----------|----------|
| G1 | All unit tests passing | Yes |
| G2 | All integration tests passing | Yes |
| G3 | Code coverage ≥ 80% for new code | Yes |
| G4 | No critical security vulnerabilities | Yes |
| G5 | Performance benchmarks met | Yes |
| G6 | API documentation updated | Yes |

### Epic Completion Gates

| Gate | Criteria | Required |
|------|----------|----------|
| E1 | All 15 stories meet G1-G6 | Yes |
| E2 | E2E test suite passing | Yes |
| E3 | Neo4j integration verified in staging | Yes |
| E4 | Entity extraction accuracy ≥ 85% | Yes |
| E5 | Graph query latency < 500ms (p95) | Yes |
| E6 | No P0/P1 bugs open | Yes |

### Performance Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| Entity extraction latency | < 3s per chunk | Median time |
| Graph entity search | < 200ms | p95 latency |
| Neighborhood query (1-hop) | < 300ms | p95 latency |
| Path finding (5-hop max) | < 500ms | p95 latency |
| Graph-augmented retrieval | < 1s | p95 latency |
| Batch job throughput | 10 docs/min | Sustained rate |

---

## Mitigation Plans

### R-001: Neo4j Connection Failures

**Risk:** Neo4j connection failures in Docker network (Score: 6)

**Mitigation Strategy:**
1. Implement connection retry with exponential backoff
2. Add circuit breaker pattern for Neo4j client
3. Include comprehensive health check in startup
4. Document network troubleshooting steps

**Test Coverage:**
- Unit test connection retry logic
- Integration test Docker network isolation
- E2E test service recovery after Neo4j restart

### R-002: LLM Entity Extraction Inconsistency

**Risk:** LLM entity extraction producing inconsistent results (Score: 9)

**Mitigation Strategy:**
1. Use structured output format (JSON) with validation
2. Implement extraction prompt versioning
3. Add confidence threshold filtering
4. Create golden test set for extraction quality
5. Enable model temperature control (low for consistency)

**Test Coverage:**
- Unit test prompt template generation
- Unit test JSON output parsing and validation
- Integration test with multiple LLM models
- Benchmark test with golden dataset (target: 85% F1)

### R-003: Entity Deduplication Accuracy

**Risk:** Entity deduplication producing false positives/negatives (Score: 6)

**Mitigation Strategy:**
1. Use Jaro-Winkler with configurable threshold (0.9)
2. Implement type-aware matching (same entity type only)
3. Add attribute matching for disambiguation
4. Provide manual merge/split UI for corrections

**Test Coverage:**
- Unit test fuzzy matching algorithms
- Unit test edge cases (abbreviations, typos, synonyms)
- Integration test with real document extractions
- Regression test with known deduplication cases

### R-004: Graph Query Performance

**Risk:** Graph query performance degradation at scale (Score: 6)

**Mitigation Strategy:**
1. Add indexes on frequently queried properties (kb_id, name)
2. Implement query result limits
3. Use query timeout configuration
4. Add query plan caching for common patterns

**Test Coverage:**
- Load test with 10K+ entities
- Performance benchmark for each query type
- Stress test concurrent query handling
- Memory usage profiling

### R-005: Vector-Graph Fusion Quality

**Risk:** Vector-graph result fusion producing poor relevance (Score: 6)

**Mitigation Strategy:**
1. Implement configurable fusion weights
2. Add source_type tracking for debugging
3. Create relevance evaluation framework
4. Enable A/B testing between strategies

**Test Coverage:**
- Unit test fusion algorithm variations
- Integration test result ordering
- Benchmark test with human relevance judgments
- Comparison test: vector-only vs augmented

### R-008: KB-Domain Permission Bypass

**Risk:** Users accessing domains without proper KB permissions (Score: 6)

**Mitigation Strategy:**
1. Verify KB access before domain operations
2. Scope all graph queries by kb_id
3. Add audit logging for domain access
4. Implement permission inheritance checks

**Test Coverage:**
- Unit test permission check functions
- Integration test cross-KB isolation
- Security test unauthorized access attempts
- Audit log verification tests

### R-009: Cross-KB Entity Contamination

**Risk:** Entities from one KB appearing in another KB's results (Score: 6)

**Mitigation Strategy:**
1. Mandatory kb_id on all Neo4j nodes
2. Include kb_id filter in all Cypher queries
3. Validate kb_id on entity creation
4. Add cross-KB isolation integration tests

**Test Coverage:**
- Unit test kb_id filtering logic
- Integration test multi-KB scenarios
- Security test cross-KB query attempts
- Data integrity verification tests

### R-013: Domain API Access Control Bypass

**Risk:** Unauthorized modifications to domain schemas (Score: 6)

**Mitigation Strategy:**
1. Verify domain ownership/admin status on all mutations
2. Protect system templates (is_system_template check)
3. Add rate limiting for domain operations
4. Audit log all schema changes

**Test Coverage:**
- Unit test authorization decorators
- Integration test role-based access
- Security test privilege escalation attempts
- System template protection tests

---

## Test Scenario Details

### Story 8-1: Neo4j Docker Infrastructure

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-1-U01 | Neo4jClient initialization with valid credentials | Client created, driver active | P0 |
| 8-1-U02 | Neo4jClient initialization with invalid credentials | AuthenticationError raised | P0 |
| 8-1-U03 | verify_connectivity returns True on healthy connection | True returned | P0 |
| 8-1-U04 | verify_connectivity returns False on failed connection | False returned, no exception | P0 |
| 8-1-U05 | Connection pool respects max_pool_size config | Pool size limited correctly | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-1-I01 | Docker compose starts Neo4j alongside other services | All services healthy | P0 |
| 8-1-I02 | Neo4j data persists across container restart | Data retained after restart | P0 |
| 8-1-I03 | APOC plugin available for text functions | apoc.text functions work | P1 |
| 8-1-I04 | Health endpoint includes Neo4j status | neo4j: "healthy" in response | P0 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-1-E01 | Full environment startup with Neo4j | All services operational | P0 |
| 8-1-E02 | Service recovery after Neo4j restart | Application reconnects | P1 |

---

### Story 8-2: Domain Data Model & Migrations

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-2-U01 | Domain model creates with all required fields | Model saved successfully | P0 |
| 8-2-U02 | DomainEntityType linked to Domain correctly | Relationship works | P0 |
| 8-2-U03 | DomainRelationshipType references entity types | Foreign keys valid | P0 |
| 8-2-U04 | KB-Domain junction table enforces uniqueness | Duplicate rejected | P0 |
| 8-2-U05 | Cascade delete removes entity types with domain | Child records deleted | P0 |
| 8-2-U06 | Unique constraint on domain name | Duplicate name rejected | P0 |
| 8-2-U07 | JSONB attributes stored correctly | JSON round-trip works | P1 |
| 8-2-U08 | Entity type unique within domain constraint | Constraint enforced | P0 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-2-I01 | Alembic migration up creates all tables | Tables exist | P0 |
| 8-2-I02 | Alembic migration down removes tables | Tables removed | P0 |
| 8-2-I03 | Indexes created on domain_id columns | Indexes exist | P1 |
| 8-2-I04 | Foreign key constraints enforced | Invalid refs rejected | P0 |
| 8-2-I05 | Migration idempotent (can run twice safely) | No errors on re-run | P1 |

---

### Story 8-5: Domain Management API

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-5-U01 | Create domain with valid data | Domain created, 201 returned | P0 |
| 8-5-U02 | Create domain with duplicate name | 409 Conflict | P0 |
| 8-5-U03 | Create domain with invalid name (too short) | 422 Validation error | P1 |
| 8-5-U04 | List domains returns user's + public domains | Correct list returned | P0 |
| 8-5-U05 | Get domain by ID returns full details | Complete domain returned | P0 |
| 8-5-U06 | Update domain by owner succeeds | Domain updated | P0 |
| 8-5-U07 | Update domain by non-owner fails | 403 Forbidden | P0 |
| 8-5-U08 | Delete system template fails | 403 Forbidden | P0 |
| 8-5-U09 | Clone domain creates user-owned copy | New domain created | P0 |
| 8-5-U10 | Add entity type to domain | Entity type created | P0 |
| 8-5-U11 | Add relationship type with valid entity refs | Relationship created | P0 |
| 8-5-U12 | Add relationship type with invalid entity ref | 400 Bad Request | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-5-I01 | Full CRUD lifecycle for domain | All operations work | P0 |
| 8-5-I02 | Entity type reorder persists correctly | Order preserved | P1 |
| 8-5-I03 | Domain with entity types and relationships | Complex domain created | P0 |
| 8-5-I04 | Clone includes all entity/relationship types | Full copy created | P0 |
| 8-5-I05 | Private domain hidden from other users | Not in list results | P0 |
| 8-5-I06 | Public domain visible to all authenticated users | In list results | P0 |
| 8-5-I07 | Admin can modify any domain | Modification succeeds | P1 |
| 8-5-I08 | Audit log records domain changes | Events logged | P1 |
| 8-5-I09 | Delete domain cascades to entity types | Children deleted | P0 |
| 8-5-I10 | Color validation accepts valid hex codes | Valid colors accepted | P2 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-5-E01 | Create domain via UI | Domain appears in list | P0 |
| 8-5-E02 | Clone system template and customize | Customized domain works | P1 |
| 8-5-E03 | Link domain to KB and use for extraction | Full workflow succeeds | P0 |

---

### Story 8-8: Per-KB Entity Extraction Service

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-8-U01 | Extraction prompt includes entity types | Prompt formatted correctly | P0 |
| 8-8-U02 | Extraction prompt includes relationship types | Relationships in prompt | P0 |
| 8-8-U03 | LLM response parsed to ExtractedEntity list | Entities parsed | P0 |
| 8-8-U04 | Invalid LLM JSON response handled gracefully | Error logged, empty result | P0 |
| 8-8-U05 | Entity stored in Neo4j with correct label | Node created with type label | P0 |
| 8-8-U06 | Entity includes kb_id property | KB isolation maintained | P0 |
| 8-8-U07 | Relationship stored with correct type | Edge created | P0 |
| 8-8-U08 | Duplicate entity detected by exact name match | Existing entity returned | P0 |
| 8-8-U09 | Near-duplicate detected by fuzzy matching | Merged correctly | P0 |
| 8-8-U10 | Source document reference tracked | document_id in properties | P0 |
| 8-8-U11 | Confidence score stored on entity | Score present | P1 |
| 8-8-U12 | Extraction uses NER model if configured | Correct model selected | P1 |
| 8-8-U13 | Fallback to generation model if no NER | Generation model used | P1 |
| 8-8-U14 | Empty chunk returns empty extraction | No entities created | P2 |
| 8-8-U15 | Very long chunk truncated before LLM call | Within token limit | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-8-I01 | Extract entities from IT Operations document | Servers, services extracted | P0 |
| 8-8-I02 | Extract relationships between entities | Relationships created | P0 |
| 8-8-I03 | Multiple chunks same entity deduplicated | Single node, multiple refs | P0 |
| 8-8-I04 | Cross-document deduplication | Entities merged | P1 |
| 8-8-I05 | KB isolation verified in Neo4j | Queries scoped | P0 |
| 8-8-I06 | Extraction with domain extraction hints | Hints improve accuracy | P2 |
| 8-8-I07 | Large batch extraction performance | < 3s per chunk median | P1 |
| 8-8-I08 | LLM error during extraction recovers | Task retried | P1 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-8-E01 | Upload document, verify entities extracted | Entities in graph | P0 |
| 8-8-E02 | Query extracted entities via API | Results returned | P0 |

---

### Story 8-10: Graph Query Service

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-10-U01 | Entity search by name returns matches | Matching entities returned | P0 |
| 8-10-U02 | Entity search respects kb_id filter | Only KB entities returned | P0 |
| 8-10-U03 | Entity search with type filter | Filtered by entity type | P1 |
| 8-10-U04 | Entity search pagination works | Offset/limit respected | P1 |
| 8-10-U05 | Neighborhood query returns 1-hop neighbors | Direct connections found | P0 |
| 8-10-U06 | Neighborhood query respects depth limit | Max hops honored | P1 |
| 8-10-U07 | Path finding returns shortest path | Correct path returned | P0 |
| 8-10-U08 | Path finding with no path returns None | None returned, no error | P0 |
| 8-10-U09 | Path finding respects max_depth | Long paths rejected | P1 |
| 8-10-U10 | Subgraph extraction returns nodes and edges | Complete subgraph | P0 |
| 8-10-U11 | Subgraph with expand_hops=1 | Expanded correctly | P1 |
| 8-10-U12 | Query result limit enforced | Max results respected | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-10-I01 | Entity search across 1000+ entities | Performance < 200ms | P0 |
| 8-10-I02 | Neighborhood query with dense graph | Handles high connectivity | P1 |
| 8-10-I03 | Path finding in sparse vs dense graphs | Both work correctly | P1 |
| 8-10-I04 | KB access control enforced | Unauthorized KB rejected | P0 |
| 8-10-I05 | Cypher injection attempt blocked | Query safely parameterized | P0 |
| 8-10-I06 | Query timeout prevents runaway queries | Timeout enforced | P1 |
| 8-10-I07 | Concurrent queries handled | No race conditions | P1 |
| 8-10-I08 | Empty KB returns empty results | No errors | P2 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-10-E01 | Search entities via UI | Results displayed | P0 |
| 8-10-E02 | View entity neighborhood visualization | Graph rendered | P1 |

---

### Story 8-11: Graph-Augmented Retrieval

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-11-U01 | Vector search runs first | Qdrant results obtained | P0 |
| 8-11-U02 | Entities extracted from query | Query entities identified | P0 |
| 8-11-U03 | Graph neighborhood retrieved for entities | Neighbors found | P0 |
| 8-11-U04 | Related chunks fetched from graph context | Additional chunks added | P0 |
| 8-11-U05 | Results merged without duplicates | Unique chunks only | P0 |
| 8-11-U06 | Source type tracked (vector/graph) | source_type field set | P1 |
| 8-11-U07 | Graph context included in result | graph_context populated | P1 |
| 8-11-U08 | Options configure expansion depth | Depth respected | P1 |
| 8-11-U09 | Similarity threshold applied | Low-relevance filtered | P1 |
| 8-11-U10 | Empty graph results in vector-only | Graceful fallback | P0 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-11-I01 | Full augmented retrieval flow | Enhanced results returned | P0 |
| 8-11-I02 | Augmentation improves relevance | Quality measurement | P1 |
| 8-11-I03 | Performance within 1s target | Latency acceptable | P0 |
| 8-11-I04 | KB without graph uses vector-only | Fallback works | P0 |
| 8-11-I05 | Large graph doesn't timeout | Bounded expansion | P1 |
| 8-11-I06 | Cross-KB isolation maintained | No contamination | P0 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-11-E01 | Search with graph-augmented strategy | Enhanced results in UI | P0 |
| 8-11-E02 | Compare vector-only vs augmented | Quality difference visible | P1 |
| 8-11-E03 | Graph context displayed with results | Context shown to user | P1 |

---

### Story 8-12: Retrieval Strategy Abstraction

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-12-U01 | VectorOnlyStrategy implements interface | All methods present | P0 |
| 8-12-U02 | VectorFirstGraphAugmentStrategy implements interface | All methods present | P0 |
| 8-12-U03 | StrategyRegistry registers strategies | Strategies available | P0 |
| 8-12-U04 | get_strategy returns correct type | Requested strategy returned | P0 |
| 8-12-U05 | get_best_strategy_for_kb uses KB config | Config respected | P0 |
| 8-12-U06 | Auto-selection uses graph if available | Graph strategy selected | P0 |
| 8-12-U07 | Fallback to vector-only if no graph | Vector strategy selected | P0 |
| 8-12-U08 | list_strategies returns all registered | Complete list | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-12-I01 | KB with graph uses graph strategy | Correct strategy selected | P0 |
| 8-12-I02 | KB without graph uses vector strategy | Fallback works | P0 |
| 8-12-I03 | KB explicit strategy preference honored | Config override works | P1 |
| 8-12-I04 | Strategy switch mid-session | No state issues | P1 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-12-E01 | Configure KB retrieval strategy | Setting persists | P1 |
| 8-12-E02 | Search uses configured strategy | Strategy applied | P0 |

---

### Story 8-14: Schema Evolution & Re-extraction

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-14-U01 | Schema version increments on change | Version bumped | P0 |
| 8-14-U02 | Schema change logged with details | Change record created | P0 |
| 8-14-U03 | Document extraction version tracked | Version stored | P0 |
| 8-14-U04 | Drift detection finds outdated documents | Outdated list returned | P0 |
| 8-14-U05 | Re-extraction job creates tasks | Celery tasks queued | P0 |
| 8-14-U06 | Job status tracks completed/failed/pending | Status accurate | P0 |
| 8-14-U07 | Job cancellation stops pending tasks | Tasks revoked | P1 |
| 8-14-U08 | Cleanup mode "replace" clears entities | Old entities removed | P0 |
| 8-14-U09 | Cleanup mode "append" keeps existing | Entities preserved | P0 |
| 8-14-U10 | Cleanup mode "merge" reconciles entities | Merge logic applied | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-14-I01 | Full re-extraction job lifecycle | Job completes | P0 |
| 8-14-I02 | Partial failure doesn't stop job | Other docs processed | P0 |
| 8-14-I03 | Completion notification sent | Notification works | P1 |
| 8-14-I04 | Schema changes trigger drift detection | Drift detected | P0 |
| 8-14-I05 | Re-extraction updates document version | Version updated | P0 |
| 8-14-I06 | Concurrent jobs handled correctly | No conflicts | P1 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-14-E01 | View schema drift in admin UI | Outdated docs shown | P1 |
| 8-14-E02 | Trigger re-extraction from UI | Job starts, progress shown | P0 |

---

### Story 8-15: Batch Re-processing Worker

#### Unit Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-15-U01 | Tasks routed to reprocessing queue | Queue routing works | P0 |
| 8-15-U02 | Rate limiting applied to LLM calls | Calls throttled | P0 |
| 8-15-U03 | Batch task handles cancellation | Cancelled status returned | P1 |
| 8-15-U04 | Progress updated atomically in Redis | Concurrent safe | P0 |
| 8-15-U05 | ETA calculation accurate | Reasonable estimate | P1 |
| 8-15-U06 | Last 10 errors tracked | Error list maintained | P1 |
| 8-15-U07 | acks_late enables failure recovery | Incomplete tasks requeued | P0 |
| 8-15-U08 | Soft time limit triggers requeue | Remaining docs requeued | P1 |

#### Integration Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-15-I01 | Worker container starts in Docker | Container healthy | P0 |
| 8-15-I02 | Normal processing unaffected | Default queue separate | P0 |
| 8-15-I03 | Rate limiting under load | 10 calls/second max | P0 |
| 8-15-I04 | Worker crash recovery | Jobs resume | P1 |
| 8-15-I05 | Progress API returns accurate data | Stats match reality | P0 |

#### E2E Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| 8-15-E01 | Large batch job completes | All docs processed | P0 |
| 8-15-E02 | Monitor job progress in UI | Progress updates shown | P1 |

---

## Appendix A: Test Data Requirements

### Neo4j Test Data

| Dataset | Entities | Relationships | Purpose |
|---------|----------|---------------|---------|
| Small | 100 | 150 | Unit tests |
| Medium | 1,000 | 3,000 | Integration tests |
| Large | 10,000 | 50,000 | Performance tests |

### Domain Templates for Testing

1. **IT Operations** - Standard template with 5 entity types
2. **Custom Test** - Minimal template for unit tests
3. **Complex** - Template with 15+ entity types for stress testing

### Document Corpus

| Type | Count | Content | Purpose |
|------|-------|---------|---------|
| IT runbooks | 20 | Technical procedures | Entity extraction testing |
| Legal contracts | 10 | Contract clauses | Relationship testing |
| Mixed content | 50 | Various domains | Cross-domain testing |

---

## Appendix B: Test Environment Configuration

### Docker Compose Test Profile

```yaml
services:
  neo4j-test:
    image: neo4j:5-community
    environment:
      - NEO4J_AUTH=neo4j/testpassword
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - "17474:7474"
      - "17687:7687"
```

### Test Database Isolation

- Separate Neo4j database for tests: `neo4j_test`
- PostgreSQL schema prefix: `test_`
- Qdrant collection prefix: `test_kb_`

### CI/CD Integration

- Neo4j service in GitHub Actions
- Testcontainers for local integration tests
- Separate test LiteLLM configuration

---

## Appendix C: Acceptance Criteria Traceability

| Story | AC | Test IDs |
|-------|----|---------|
| 8-1 | AC1 | 8-1-I01, 8-1-E01 |
| 8-1 | AC2 | 8-1-U01, 8-1-U03, 8-1-I03 |
| 8-1 | AC3 | 8-1-I04 |
| 8-1 | AC4 | 8-1-U05 |
| 8-2 | AC1 | 8-2-U01, 8-2-U06 |
| 8-2 | AC2 | 8-2-U02, 8-2-U07 |
| 8-2 | AC3 | 8-2-U03 |
| 8-2 | AC4 | 8-2-U04 |
| 8-2 | AC5 | 8-2-I01, 8-2-I02, 8-2-I03 |
| 8-5 | AC1 | 8-5-U01 to 8-5-U09, 8-5-I01 |
| 8-5 | AC2 | 8-5-U10, 8-5-I02 |
| 8-5 | AC3 | 8-5-U11, 8-5-U12 |
| 8-5 | AC4 | 8-5-U07, 8-5-U08, 8-5-I05, 8-5-I06, 8-5-I07 |
| 8-5 | AC5 | 8-5-U02, 8-5-U03, 8-5-U12, 8-5-I10 |
| 8-5 | AC6 | 8-5-U08, 8-5-I04 |
| 8-8 | AC1 | 8-8-U01, 8-8-U02 |
| 8-8 | AC2 | 8-8-U05, 8-8-U06, 8-8-U10, 8-8-U11 |
| 8-8 | AC3 | 8-8-U07 |
| 8-8 | AC4 | 8-8-U08, 8-8-U09, 8-8-I03, 8-8-I04 |
| 8-8 | AC5 | 8-8-U01, 8-8-U03, 8-8-U04 |
| 8-8 | AC6 | 8-8-U12, 8-8-U13 |
| 8-10 | AC1 | 8-10-U01 to 8-10-U04 |
| 8-10 | AC2 | 8-10-U05, 8-10-U06 |
| 8-10 | AC3 | 8-10-U07 to 8-10-U09 |
| 8-10 | AC4 | 8-10-U10, 8-10-U11 |
| 8-10 | AC5 | 8-10-U02, 8-10-I04, 8-10-I05 |
| 8-10 | AC6 | 8-10-U12, 8-10-I01, 8-10-I06 |
| 8-11 | AC1-AC4 | 8-11-U01 to 8-11-U10, 8-11-I01 to 8-11-I06 |
| 8-12 | AC1-AC6 | 8-12-U01 to 8-12-U08, 8-12-I01 to 8-12-I04 |
| 8-14 | AC1-AC6 | 8-14-U01 to 8-14-U10, 8-14-I01 to 8-14-I06 |
| 8-15 | AC1-AC6 | 8-15-U01 to 8-15-U08, 8-15-I01 to 8-15-I05 |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-08 | Test Engineering | Initial document |
