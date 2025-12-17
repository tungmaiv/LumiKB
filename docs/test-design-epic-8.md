# Test Design: Epic 8 - GraphRAG Integration

**Date:** 2025-12-17
**Author:** Tung Vu
**Status:** Draft

---

## Executive Summary

**Scope:** Epic-Level (Phase 4) test design for Epic 8: GraphRAG Integration

**Risk Summary:**

- Total risks identified: 24
- High-priority risks (>=6): 8
- Critical categories: TECH, PERF, DATA, SEC

**Coverage Summary:**

- P0 scenarios: 32 (~64 hours)
- P1 scenarios: 48 (~48 hours)
- P2/P3 scenarios: 45 (~15 hours)
- **Total effort**: ~127 hours (~16 days)

**Epic Overview:**
- 18 stories, 81 story points
- 6 execution phases (Phase 0-5)
- Key deliverables: History-aware query rewriting, Neo4j graph storage, domain management, entity extraction, graph-augmented retrieval, hybrid BM25+vector search

---

## Risk Assessment

### High-Priority Risks (Score >=6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-001 | PERF | Neo4j graph traversal >100ms for large graphs (100k+ entities) | 2 | 3 | 6 | Index optimization, query caching, traversal depth limits | Backend | Pre-8.10 |
| R-002 | DATA | Entity extraction produces inconsistent/duplicate entities | 3 | 2 | 6 | Entity deduplication logic, fuzzy matching, validation layer | Backend | Pre-8.8 |
| R-003 | TECH | LLM-based entity extraction fails for complex domains | 2 | 3 | 6 | Fallback extraction, prompt iteration, confidence thresholds | Backend | Pre-8.8 |
| R-004 | PERF | Hybrid retrieval (BM25+Vector) adds >150ms latency | 2 | 3 | 6 | Parallel execution, result caching, early termination | Backend | Pre-8.17 |
| R-005 | DATA | Graph-vector index desync on document updates/deletes | 2 | 3 | 6 | Transactional updates, sync verification jobs, reconciliation | Backend | Pre-8.9 |
| R-006 | SEC | Domain schema allows extraction of sensitive entity types | 2 | 3 | 6 | Schema validation, sensitive field masking, audit logging | Backend | Pre-8.6 |
| R-007 | TECH | Query rewriting degrades conversation flow (wrong reformulations) | 2 | 3 | 6 | Prompt engineering, fallback to original, user feedback loop | Backend | Pre-8.0 |
| R-008 | PERF | Schema re-extraction overwhelms processing queue | 2 | 3 | 6 | Rate limiting, priority queuing, batch size limits | Backend | Pre-8.14 |

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|--------|-------|------------|-------|
| R-009 | TECH | Neo4j connection pool exhaustion under load | 2 | 2 | 4 | Pool size tuning, connection timeouts, monitoring | DevOps |
| R-010 | DATA | Domain versioning conflicts during concurrent updates | 2 | 2 | 4 | Optimistic locking, version conflict resolution | Backend |
| R-011 | BUS | Users unable to understand domain schema concepts | 2 | 2 | 4 | UI/UX improvements, tooltips, templates as examples | Frontend |
| R-012 | TECH | Elasticsearch index mappings incompatible with chunk schemas | 2 | 2 | 4 | Schema validation, migration scripts, mapping tests | Backend |
| R-013 | OPS | Neo4j/Elasticsearch volumes fill up in production | 2 | 2 | 4 | Monitoring, alerts, retention policies, cleanup jobs | DevOps |
| R-014 | PERF | LLM domain recommendations timeout (>30s) | 2 | 2 | 4 | Timeout handling, async processing, caching | Backend |
| R-015 | DATA | Unmatched entities accumulate without review | 2 | 2 | 4 | Notification thresholds, aggregation, auto-cleanup | Backend |
| R-016 | TECH | Visual relationship diagram performance with large schemas | 2 | 2 | 4 | Virtualization, lazy loading, zoom/pan optimization | Frontend |
| R-017 | DATA | BM25 and Qdrant result fusion produces poor rankings | 2 | 2 | 4 | RRF tuning, A/B testing, relevance feedback | Backend |
| R-018 | BUS | Domain template mismatch with actual user data | 1 | 3 | 3 | Template customization, LLM recommendations, feedback | Product |
| R-019 | TECH | Celery task chain failures in graph extraction | 1 | 3 | 3 | Error handling, retry logic, dead letter queue | Backend |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|--------|-------|--------|
| R-020 | OPS | Neo4j image version compatibility issues | 1 | 2 | 2 | Document |
| R-021 | TECH | react-flow library deprecation/breaking changes | 1 | 2 | 2 | Monitor |
| R-022 | BUS | Low adoption of custom domain creation | 1 | 2 | 2 | Monitor |
| R-023 | TECH | Langfuse trace span naming conflicts | 1 | 1 | 1 | Document |
| R-024 | OPS | CI/CD E2E test flakiness from graph timing | 1 | 2 | 2 | Monitor |

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

**Criteria**: Blocks core journey + High risk (>=6) + No workaround

#### Story 8.0: History-Aware Query Rewriting

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.0-E2E-001 | AC-8.0.4 | E2E | R-007 | Multi-turn conversation with pronoun resolution | QA |
| 8.0-API-001 | AC-8.0.1 | API | R-007 | QueryRewriterService.rewrite_with_history() happy path | DEV |
| 8.0-API-002 | AC-8.0.8 | API | R-007 | Graceful degradation on LLM failure | DEV |
| 8.0-API-003 | AC-8.0.9 | API | - | Skip rewriting for standalone queries | DEV |
| 8.0-UNIT-001 | AC-8.0.5 | Unit | R-007 | Prompt template validation | DEV |
| 8.0-UNIT-002 | AC-8.0.7 | Unit | - | Performance constraint verification (<500ms) | DEV |

#### Story 8.1: Neo4j Docker Infrastructure

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.1-API-001 | AC-8.1.2 | API | R-009 | Health check endpoint returns healthy | DEV |
| 8.1-API-002 | AC-8.1.3 | API | R-009 | Connection pooling under concurrent load | DEV |
| 8.1-INT-001 | AC-8.1.4 | Integration | - | Data persistence across restarts | DevOps |

#### Story 8.8: Per-KB Entity Extraction Service

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.8-API-001 | AC-8.8.3 | API | R-002, R-003 | Entity extraction from document chunks | QA |
| 8.8-API-002 | AC-8.8.4 | API | R-002 | Relationship extraction with schema compliance | QA |
| 8.8-API-003 | AC-8.8.5 | API | R-003 | Unknown entity handling (unmatched tagging) | DEV |
| 8.8-UNIT-001 | AC-8.8.2 | Unit | R-003 | Schema-aware prompt generation | DEV |

#### Story 8.9: Document Processing Graph Integration

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.9-E2E-001 | AC-8.9.1 | E2E | R-005 | Full document processing with graph extraction | QA |
| 8.9-API-001 | AC-8.9.3 | API | R-005 | Entity storage in Neo4j with correct labels | DEV |
| 8.9-API-002 | AC-8.9.6 | API | R-005 | Graceful degradation on extraction failure | DEV |
| 8.9-API-003 | AC-8.9.5 | API | R-005 | Document status update after extraction | DEV |

#### Story 8.10: Graph Query Service

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.10-API-001 | AC-8.10.1 | API | R-001 | Find entities by name/partial match | DEV |
| 8.10-API-002 | AC-8.10.2 | API | R-001 | Relationship traversal with max_hops | DEV |
| 8.10-PERF-001 | AC-8.10.6 | Performance | R-001 | Query performance <100ms with 100k entities | QA |

#### Story 8.11: Graph-Augmented Retrieval

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.11-E2E-001 | AC-8.11.1-6 | E2E | R-001 | Full graph-augmented search flow | QA |
| 8.11-API-001 | AC-8.11.7 | API | R-001 | Graceful degradation when graph unavailable | DEV |
| 8.11-PERF-001 | AC-8.11.8 | Performance | R-001 | <200ms additional latency target | QA |

#### Story 8.17: Hybrid BM25 + Vector Retrieval

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.17-E2E-001 | AC-8.17.5-6 | E2E | R-004 | Parallel search with RRF fusion | QA |
| 8.17-API-001 | AC-8.17.3 | API | R-005 | Chunk indexing in both Qdrant and ES | DEV |
| 8.17-API-002 | AC-8.17.9 | API | R-004 | Fallback to vector-only on ES failure | DEV |
| 8.17-API-003 | AC-8.17.10 | API | R-005 | Index sync on document delete/update | DEV |
| 8.17-PERF-001 | AC-8.17.11 | Performance | R-004 | <150ms additional latency, <50ms BM25 | QA |

**Total P0**: 32 tests, ~64 hours

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-5) + Common workflows

#### Story 8.2: Domain Data Model & Migrations

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.2-INT-001 | AC-8.2.1-6 | Integration | - | Alembic migrations create all tables | DEV |
| 8.2-UNIT-001 | AC-8.2.1 | Unit | - | SQLAlchemy model validation | DEV |

#### Story 8.3: System Domain Templates

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.3-API-001 | AC-8.3.1-5 | API | R-018 | All 5 templates load correctly | QA |
| 8.3-API-002 | AC-8.3.6 | API | - | System templates cannot be deleted | DEV |

#### Story 8.4: LLM Domain Recommendation Service

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.4-API-001 | AC-8.4.1 | API | R-014 | Recommendation from description | QA |
| 8.4-API-002 | AC-8.4.3 | API | - | Structured output parsing | DEV |
| 8.4-API-003 | AC-8.4.4 | API | R-018 | Template matching for known domains | DEV |
| 8.4-API-004 | AC-8.4.2 | API | - | Uses NER model from registry | DEV |

#### Story 8.5: Domain Management API

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.5-API-001 | AC-8.5.1 | API | - | List domains with filters | QA |
| 8.5-API-002 | AC-8.5.3 | API | R-010 | Create domain | QA |
| 8.5-API-003 | AC-8.5.4 | API | R-010 | Update domain with version history | DEV |
| 8.5-API-004 | AC-8.5.5 | API | - | Delete domain (blocked if in use) | DEV |
| 8.5-API-005 | AC-8.5.6 | API | - | Clone domain | DEV |
| 8.5-API-006 | AC-8.5.8-9 | API | - | Entity/Relationship type CRUD | DEV |

#### Story 8.6: Domain Management UI

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.6-E2E-001 | AC-8.6.1-3 | E2E | R-011 | Create domain with LLM recommendations | QA |
| 8.6-E2E-002 | AC-8.6.4-5 | E2E | R-016 | Entity/Relationship editor flow | QA |
| 8.6-E2E-003 | AC-8.6.6 | E2E | R-016 | Visual diagram renders correctly | QA |
| 8.6-E2E-004 | AC-8.6.8 | E2E | - | Validation errors display | QA |
| 8.6-E2E-005 | AC-8.6.9 | E2E | - | Delete protection warning | QA |
| 8.6-COMP-001 | AC-8.6.4 | Component | - | EntityTypeEditor component | DEV |
| 8.6-COMP-002 | AC-8.6.5 | Component | - | RelationshipTypeEditor component | DEV |

#### Story 8.7: KB-Domain Linking

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.7-E2E-001 | AC-8.7.1-2 | E2E | - | Domain selection in KB creation | QA |
| 8.7-E2E-002 | AC-8.7.5 | E2E | - | Change domain warning | QA |
| 8.7-API-001 | AC-8.7.6 | API | - | No domain = vector-only processing | DEV |

#### Story 8.12: Retrieval Strategy Abstraction

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.12-UNIT-001 | AC-8.12.1 | Unit | - | Strategy interface contract | DEV |
| 8.12-UNIT-002 | AC-8.12.2-3 | Unit | - | Strategy selection logic | DEV |
| 8.12-API-001 | AC-8.12.4 | API | - | Correct strategy selected per KB config | DEV |
| 8.12-API-002 | AC-8.12.6 | API | - | Strategy metrics emitted | DEV |

#### Story 8.13: LLM Schema Enrichment Suggestions

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.13-API-001 | AC-8.13.1-2 | API | R-015 | Unmatched entity tracking/aggregation | DEV |
| 8.13-API-002 | AC-8.13.5 | API | - | Accept suggestion updates schema | DEV |
| 8.13-E2E-001 | AC-8.13.4 | E2E | - | Suggestion review UI flow | QA |

#### Story 8.14: Schema Evolution & Re-extraction

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.14-API-001 | AC-8.14.1 | API | R-008 | Schema version tracking | DEV |
| 8.14-API-002 | AC-8.14.2-5 | API | R-008 | Re-extraction job queuing | DEV |
| 8.14-API-003 | AC-8.14.7 | API | R-008 | Schema rollback capability | DEV |
| 8.14-E2E-001 | AC-8.14.3-6 | E2E | - | Re-extraction prompt and progress | QA |

#### Story 8.15: Batch Re-processing Worker

| Test ID | Requirement | Test Level | Risk Link | Description | Owner |
|---------|-------------|------------|-----------|-------------|-------|
| 8.15-API-001 | AC-8.15.1-3 | API | R-008 | Batch processing trigger and progress API | DEV |
| 8.15-API-002 | AC-8.15.4 | API | R-019 | Error handling with retry | DEV |
| 8.15-API-003 | AC-8.15.5 | API | - | Cancel batch preserves completed work | DEV |

**Total P1**: 48 tests, ~48 hours

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Test ID | Story | Requirement | Test Level | Description | Owner |
|---------|-------|-------------|------------|-------------|-------|
| 8.0-E2E-002 | 8.0 | AC-8.0.2-3 | E2E | Admin UI model configuration | QA |
| 8.0-E2E-003 | 8.0 | AC-8.0.6 | E2E | Debug mode shows rewritten query | QA |
| 8.0-API-004 | 8.0 | AC-8.0.10 | API | Langfuse trace spans | DEV |
| 8.1-INT-002 | 8.1 | AC-8.1.5 | Integration | Environment variable configuration | DevOps |
| 8.3-UNIT-001 | 8.3 | AC-8.3.1-5 | Unit | Template entity/relationship validation | DEV |
| 8.4-UNIT-001 | 8.4 | AC-8.4.5 | Unit | Confidence score calculation | DEV |
| 8.5-API-007 | 8.5 | AC-8.5.7 | API | Get recommendations endpoint | DEV |
| 8.6-E2E-006 | 8.6 | AC-8.6.7 | E2E | Start from template flow | QA |
| 8.7-E2E-003 | 8.7 | AC-8.7.3 | E2E | Create domain inline from KB creation | QA |
| 8.8-API-004 | 8.8 | AC-8.8.6 | API | Batch processing with progress | DEV |
| 8.8-API-005 | 8.8 | AC-8.8.7 | API | Extraction metrics recording | DEV |
| 8.9-INT-001 | 8.9 | AC-8.9.2 | Integration | Skip graph extraction when no domain | DEV |
| 8.9-API-004 | 8.9 | AC-8.9.7 | API | Processing status includes graph step | DEV |
| 8.10-API-003 | 8.10 | AC-8.10.3 | API | Filter by relationship type | DEV |
| 8.10-API-004 | 8.10 | AC-8.10.4 | API | Get entity source chunks | DEV |
| 8.10-API-005 | 8.10 | AC-8.10.5 | API | KB-scoped query isolation | DEV |
| 8.11-API-002 | 8.11 | AC-8.11.3 | API | Graph traversal hop limiting | DEV |
| 8.11-API-003 | 8.11 | AC-8.11.5 | API | Merge and dedupe results | DEV |
| 8.12-UNIT-003 | 8.12 | AC-8.12.5 | Unit | Feature flag strategy switching | DEV |
| 8.13-API-003 | 8.13 | AC-8.13.3 | API | Suggestion notification trigger | DEV |
| 8.13-API-004 | 8.13 | AC-8.13.6-7 | API | Relationship suggestions, threshold config | DEV |
| 8.15-E2E-001 | 8.15 | AC-8.15.6 | E2E | Batch completion notification | QA |
| 8.17-E2E-002 | 8.17 | AC-8.17.7-8 | E2E | Admin UI hybrid configuration | QA |
| 8.17-API-004 | 8.17 | AC-8.17.2 | API | BM25 index per KB creation | DEV |
| 8.17-API-005 | 8.17 | AC-8.17.12 | API | Observability metrics/traces | DEV |

**Total P2**: 25 tests, ~12.5 hours

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Test ID | Story | Test Level | Description | Owner |
|---------|-------|------------|-------------|-------|
| 8.0-PERF-001 | 8.0 | Performance | Query rewriting latency distribution | QA |
| 8.1-PERF-001 | 8.1 | Performance | Neo4j connection pool stress test | QA |
| 8.4-PERF-001 | 8.4 | Performance | Recommendation latency with complex descriptions | QA |
| 8.6-PERF-001 | 8.6 | Performance | Visual diagram with 100+ entities | QA |
| 8.8-PERF-001 | 8.8 | Performance | Entity extraction on 10k+ chunk document | QA |
| 8.9-PERF-001 | 8.9 | Performance | Full pipeline with large documents | QA |
| 8.10-PERF-002 | 8.10 | Performance | Graph traversal with 500k entities | QA |
| 8.11-PERF-002 | 8.11 | Performance | Graph-augmented search under load | QA |
| 8.14-PERF-001 | 8.14 | Performance | Re-extraction of 1000 documents | QA |
| 8.17-PERF-002 | 8.17 | Performance | Hybrid search with 1M+ chunks | QA |
| 8.16-E2E-ALL | 8.16 | E2E | Full E2E test suite (Epic 3-8) | QA |
| EXPL-001 | All | Exploratory | Edge cases in domain schema design | QA |
| EXPL-002 | All | Exploratory | Complex multi-hop graph queries | QA |
| EXPL-003 | All | Exploratory | LLM extraction with non-English content | QA |
| EXPL-004 | All | Exploratory | Concurrent schema updates | QA |
| SEC-001 | 8.6 | Security | Domain schema injection attempts | SEC |
| SEC-002 | 8.8 | Security | Entity extraction of PII | SEC |
| SEC-003 | 8.5 | Security | Authorization bypass in domain API | SEC |
| A11Y-001 | 8.6 | Accessibility | Domain editor keyboard navigation | QA |
| A11Y-002 | 8.6 | Accessibility | Visual diagram screen reader support | QA |

**Total P3**: 20 tests, ~2.5 hours (exploratory time varies)

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] Neo4j health check (30s)
- [ ] Elasticsearch health check (30s)
- [ ] Domain API list endpoint (30s)
- [ ] KB API with domain_id (30s)
- [ ] Chat API with query rewriting (1min)
- [ ] Search API with hybrid retrieval (1min)

**Total**: 6 scenarios, ~4 min

### P0 Tests (<15 min)

**Purpose**: Critical path validation

**Phase 0 (Query Rewriting):**
- [ ] 8.0-E2E-001: Multi-turn conversation flow
- [ ] 8.0-API-001-003: Rewriter service tests
- [ ] 8.0-UNIT-001-002: Prompt and performance tests

**Phase 1-2 (Graph Foundation & Extraction):**
- [ ] 8.1-API-001-002: Neo4j infrastructure
- [ ] 8.8-API-001-003: Entity extraction
- [ ] 8.9-E2E-001, 8.9-API-001-003: Document processing

**Phase 3 (Retrieval):**
- [ ] 8.10-API-001-002, 8.10-PERF-001: Graph queries
- [ ] 8.11-E2E-001, 8.11-API-001, 8.11-PERF-001: Graph-augmented search

**Phase 5 (Hybrid):**
- [ ] 8.17-E2E-001, 8.17-API-001-003, 8.17-PERF-001: Hybrid retrieval

**Total**: 32 scenarios, ~12 min

### P1 Tests (<30 min)

**Purpose**: Important feature coverage

- [ ] Domain data model migrations (8.2)
- [ ] System templates validation (8.3)
- [ ] LLM recommendations (8.4)
- [ ] Domain CRUD API (8.5)
- [ ] Domain management UI flows (8.6)
- [ ] KB-Domain linking (8.7)
- [ ] Retrieval strategy abstraction (8.12)
- [ ] Schema evolution (8.13-8.15)

**Total**: 48 scenarios, ~25 min

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage

- [ ] Secondary features (8.0 debug mode, 8.6 templates)
- [ ] Edge cases (isolation, filtering, metrics)
- [ ] Performance benchmarks (large scale tests)
- [ ] Security scenarios
- [ ] Accessibility tests

**Total**: 45 scenarios, ~45 min

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
|----------|-------|------------|-------------|-------|
| P0 | 32 | 2.0 | 64 | Complex setup, integration, performance |
| P1 | 48 | 1.0 | 48 | Standard coverage |
| P2 | 25 | 0.5 | 12.5 | Simple scenarios |
| P3 | 20 | 0.25 | 5 | Exploratory, on-demand |
| **Total** | **125** | **-** | **~130 hours** | **~16 days** |

### Prerequisites

**Test Data:**

- DocumentFactory (faker-based chunks with entity-rich content)
- DomainFactory (IT Operations, Legal templates with variants)
- EntityFactory (entities with relationships for graph tests)
- KnowledgeBaseFactory (with/without domain configurations)

**Tooling:**

- Playwright for E2E tests
- pytest for API/Unit/Integration tests
- Neo4j test container for graph tests
- Elasticsearch test container for BM25 tests
- Mock LLM responses for deterministic entity extraction tests

**Environment:**

- Docker Compose with Neo4j, Elasticsearch, Qdrant
- Test database with seeded domain templates
- Mock LiteLLM endpoint for controlled responses
- CI/CD pipeline with E2E test stage

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: >=95% (waivers required for failures)
- **P2/P3 pass rate**: >=90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths (P0)**: >=90%
- **Security scenarios**: 100%
- **Business logic**: >=80%
- **Edge cases**: >=60%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (>=6) items unmitigated
- [ ] Security tests (R-006, SEC-001-003) pass 100%
- [ ] Performance targets met (R-001, R-004: <100ms graph, <150ms hybrid)
- [ ] Data integrity tests pass (R-002, R-005: no duplicates, sync verified)

### Story-Level Gate Mapping

| Story | Required P0 Tests | Performance Gate | Data Gate |
|-------|-------------------|------------------|-----------|
| 8.0 | 8.0-E2E-001, 8.0-API-001-003 | <500ms rewrite | - |
| 8.1 | 8.1-API-001-002 | Health <5s | Volume persistence |
| 8.8 | 8.8-API-001-003 | <2s extraction | No duplicates |
| 8.9 | 8.9-E2E-001, 8.9-API-001-003 | - | Graph-vector sync |
| 8.10 | 8.10-API-001-002, 8.10-PERF-001 | <100ms query | - |
| 8.11 | 8.11-E2E-001, 8.11-API-001, 8.11-PERF-001 | <200ms additional | - |
| 8.17 | 8.17-E2E-001, 8.17-API-001-003, 8.17-PERF-001 | <150ms additional, <50ms BM25 | ES-Qdrant sync |

---

## Mitigation Plans

### R-001: Neo4j Graph Traversal Performance (Score: 6)

**Mitigation Strategy:**
1. Create composite indexes on (kb_id, entity_type, name)
2. Implement query result caching with Redis (TTL: 5min)
3. Add configurable max_hops limit (default: 2)
4. Profile and optimize Cypher queries before release

**Owner:** Backend Team
**Timeline:** Before Story 8.10 completion
**Status:** Planned
**Verification:** 8.10-PERF-001 passes with 100k entities

### R-002: Entity Extraction Duplicates (Score: 6)

**Mitigation Strategy:**
1. Implement fuzzy matching with Levenshtein distance (threshold: 0.85)
2. Add entity deduplication step post-extraction
3. Use deterministic entity ID generation (hash of kb_id + type + normalized_name)
4. Create validation layer to check existing entities before insert

**Owner:** Backend Team
**Timeline:** Before Story 8.8 completion
**Status:** Planned
**Verification:** 8.8-API-001-002 show no duplicates

### R-003: LLM Entity Extraction Failures (Score: 6)

**Mitigation Strategy:**
1. Implement confidence threshold (reject <0.6 confidence)
2. Add fallback regex-based extraction for common patterns
3. Iterate prompt with few-shot examples per domain
4. Store failed extractions for manual review

**Owner:** Backend Team
**Timeline:** Before Story 8.8 completion
**Status:** Planned
**Verification:** 8.8-API-003 handles unknown entities gracefully

### R-004: Hybrid Retrieval Latency (Score: 6)

**Mitigation Strategy:**
1. Execute BM25 and vector search in parallel (asyncio.gather)
2. Implement result caching for repeated queries
3. Add early termination if either search exceeds timeout
4. Tune RRF k parameter for optimal fusion speed

**Owner:** Backend Team
**Timeline:** Before Story 8.17 completion
**Status:** Planned
**Verification:** 8.17-PERF-001 shows <150ms additional latency

### R-005: Graph-Vector Index Desync (Score: 6)

**Mitigation Strategy:**
1. Wrap document updates in transactional context
2. Use saga pattern: vector delete -> graph delete -> commit
3. Implement nightly reconciliation job comparing indexes
4. Add sync verification in document status response

**Owner:** Backend Team
**Timeline:** Before Stories 8.9, 8.17 completion
**Status:** Planned
**Verification:** 8.9-API-003, 8.17-API-003 verify sync after operations

### R-006: Sensitive Entity Extraction (Score: 6)

**Mitigation Strategy:**
1. Add schema validation rejecting sensitive field names (SSN, credit_card, password)
2. Implement entity masking for PII patterns
3. Add audit logging for all entity extractions
4. Review domain schemas before production use

**Owner:** Security Team
**Timeline:** Before Story 8.6 approval
**Status:** Planned
**Verification:** SEC-002 shows PII is masked

### R-007: Query Rewriting Quality (Score: 6)

**Mitigation Strategy:**
1. Extensive prompt engineering with diverse examples
2. Add fallback to original query on low confidence
3. Implement user feedback mechanism for bad rewrites
4. A/B test rewriting vs direct search

**Owner:** Backend Team
**Timeline:** Before Story 8.0 completion
**Status:** Planned
**Verification:** 8.0-E2E-001 shows correct pronoun resolution

### R-008: Re-extraction Queue Overload (Score: 6)

**Mitigation Strategy:**
1. Implement rate limiting (max 100 docs/hour re-extraction)
2. Use priority queue (new uploads > re-extractions)
3. Add configurable batch sizes with backpressure
4. Provide cancel capability for runaway jobs

**Owner:** Backend Team
**Timeline:** Before Story 8.14 completion
**Status:** Planned
**Verification:** 8.14-API-002, 8.15-API-001 show controlled processing

---

## Assumptions and Dependencies

### Assumptions

1. Neo4j Community Edition sufficient for expected graph sizes (up to 1M entities)
2. LLM-based entity extraction quality acceptable for domain-specific use cases
3. Users will primarily use system templates or LLM-recommended schemas
4. Elasticsearch/OpenSearch available in production environment
5. Existing Celery infrastructure can handle additional graph extraction tasks

### Dependencies

1. **Story 7.9 (LLM Model Registry)** - Required for Story 8.0, 8.4, 8.8
2. **Story 9.15 (Debug Mode)** - Required for Story 8.0 debug features
3. **Story 7.1 (Docker E2E Infrastructure)** - Required for Story 8.16
4. **LiteLLM proxy NER model type support** - Required for Stories 8.4, 8.8
5. **Neo4j Docker image availability** - Required for Story 8.1
6. **Elasticsearch/OpenSearch Docker image** - Required for Story 8.17

### Risks to Plan

- **Risk**: LLM provider rate limiting affects entity extraction throughput
  - **Impact**: Slower document processing, queue backlog
  - **Contingency**: Implement request batching, use local Ollama models

- **Risk**: Neo4j Community Edition lacks enterprise features needed
  - **Impact**: May need to migrate to Enterprise or alternative
  - **Contingency**: Design abstraction layer, evaluate alternatives early

- **Risk**: E2E test infrastructure not ready (Story 7.1 delayed)
  - **Impact**: Story 8.16 cannot complete E2E automation
  - **Contingency**: Prioritize API-level tests, defer full E2E suite

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: _________________ Date: _______
- [ ] Tech Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection guidance
- `test-priorities-matrix.md` - P0-P3 prioritization criteria

### Related Documents

- PRD: [docs/prd.md](docs/prd.md)
- Epic: [docs/epics/epic-8-graphrag.md](docs/epics/epic-8-graphrag.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Tech Spec: [docs/sprint-artifacts/tech-spec-epic-8.md](docs/sprint-artifacts/tech-spec-epic-8.md)

### Test ID Naming Convention

Format: `{EPIC}.{STORY}-{LEVEL}-{SEQ}`

- **EPIC**: Epic number (8)
- **STORY**: Story number (0-17)
- **LEVEL**: E2E, API, INT (Integration), COMP (Component), UNIT, PERF (Performance)
- **SEQ**: Sequential number (001, 002, ...)

Examples:
- `8.0-E2E-001`: Epic 8, Story 0, E2E test #1
- `8.17-PERF-001`: Epic 8, Story 17, Performance test #1

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `.bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
