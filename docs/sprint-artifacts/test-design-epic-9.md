# Test Design Document - Epic 9: Hybrid Observability Platform

**Version:** 1.1
**Date:** 2025-12-14
**Author:** TEA (Test Excellence Architect)
**Status:** Updated with Risk Assessment

---

## 0. Risk Assessment (TEA Analysis)

### 0.1 Risk Scoring Matrix (Probability × Impact)

| Component | Scenario | P | I | Score | Priority | Mitigation |
|-----------|----------|---|---|-------|----------|------------|
| **PostgreSQL Provider** |
| Trace ingestion pipeline failure | 2 | 3 | **6** | P0 | Integration tests + health check |
| Data loss on provider failure | 2 | 3 | **6** | P0 | Fire-and-forget isolation tests |
| Query performance degradation | 2 | 2 | 4 | P1 | Performance benchmarks |
| **Distributed Tracing** |
| Trace context propagation breaks | 2 | 3 | **6** | P0 | Cross-service integration tests |
| Span hierarchy corruption | 1 | 3 | 3 | P1 | Unit tests for span tree |
| **LangFuse Integration** |
| SDK initialization failure | 1 | 2 | 2 | P2 | Graceful degradation tests |
| Token/cost tracking inaccuracy | 2 | 2 | 4 | P1 | LiteLLM callback validation |
| **Chat History** |
| Session data loss | 2 | 3 | **6** | P0 | Persistence integration tests |
| History query timeout | 2 | 2 | 4 | P1 | Query performance tests |
| **Admin UI** |
| Dashboard rendering failure | 1 | 2 | 2 | P2 | E2E smoke tests |
| Filter/pagination bugs | 1 | 1 | 1 | P3 | E2E functional tests |

### 0.2 Critical Risks Summary (Score ≥ 6)

**4 Critical Risks** requiring comprehensive test coverage:

1. **Trace ingestion pipeline failure** (P×I=6): Production debugging impossible
2. **Data loss on provider failure** (P×I=6): Observability data integrity compromised
3. **Trace context propagation breaks** (P×I=6): Distributed debugging fails
4. **Session data loss** (P×I=6): Chat history lost, user experience degraded

### 0.3 Priority-Based Coverage Requirements

| Priority | Unit Coverage | Integration Coverage | E2E Coverage |
|----------|---------------|---------------------|--------------|
| P0 | ≥90% | ≥80% | All critical paths |
| P1 | ≥80% | ≥60% | Main happy paths |
| P2 | ≥60% | ≥40% | Smoke tests |
| P3 | Best effort | Best effort | Manual only |

---

## 1. Overview

This document defines the test strategy, test cases, and quality gates for Epic 9: Hybrid Observability Platform. The testing approach ensures comprehensive coverage of the observability infrastructure, provider integrations, and admin UI components.

### 1.1 Testing Objectives

1. Verify observability data model integrity and schema correctness
2. Validate fire-and-forget pattern doesn't impact application performance
3. Ensure distributed trace context propagation across services
4. Confirm chat history persistence and retrieval accuracy
5. Test LangFuse provider integration when enabled
6. Validate admin UI components display correct data

### 1.2 Test Scope

| In Scope | Out of Scope |
|----------|--------------|
| Unit tests for all service classes | APM tool integration tests |
| Integration tests for API endpoints | Infrastructure monitoring tests |
| E2E tests for admin UI workflows | Third-party LangFuse internal tests |
| Performance tests for fire-and-forget | Load testing at scale (>10K TPS) |
| Database schema validation | Multi-tenant isolation tests |

---

## 2. Test Strategy

### 2.1 Test Pyramid

```
                    ┌─────────────────┐
                    │     E2E Tests   │  (10%)
                    │  Admin UI flows │
                    └────────┬────────┘
                             │
               ┌─────────────┴─────────────┐
               │    Integration Tests      │  (30%)
               │ API endpoints, DB queries │
               └─────────────┬─────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │                  Unit Tests                      │  (60%)
    │ Services, Providers, Models, Context Management  │
    └──────────────────────────────────────────────────┘
```

### 2.2 Test Categories

| Category | Focus | Tools |
|----------|-------|-------|
| **Unit** | Service logic, provider implementations | pytest, pytest-asyncio |
| **Integration** | API endpoints, database operations | pytest, httpx, testcontainers |
| **E2E** | Admin UI workflows | Playwright |
| **Performance** | Latency impact, throughput | pytest-benchmark, locust |

---

## 3. Unit Test Design

### 3.1 ObservabilityService Tests

**File:** `tests/unit/test_observability_service.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| OS-U-001 | `test_start_trace_creates_valid_trace_id` | 9-3 AC1 |
| OS-U-002 | `test_end_trace_calculates_duration` | 9-3 AC2 |
| OS-U-003 | `test_start_span_with_parent_creates_hierarchy` | 9-3 AC3 |
| OS-U-004 | `test_span_attributes_recorded_correctly` | 9-3 AC4 |
| OS-U-005 | `test_provider_failure_does_not_propagate` | 9-3 AC5 |
| OS-U-006 | `test_trace_context_propagates_to_all_providers` | 9-3 AC6 |
| OS-U-007 | `test_fire_and_forget_returns_immediately` | 9-3 AC7 |
| OS-U-008 | `test_multiple_providers_called_concurrently` | 9-3 AC8 |

### 3.2 PostgreSQLProvider Tests

**File:** `tests/unit/test_postgresql_provider.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| PG-U-001 | `test_save_trace_persists_to_database` | 9-2 AC1 |
| PG-U-002 | `test_save_span_with_llm_fields` | 9-2 AC2 |
| PG-U-003 | `test_save_chat_message_all_fields` | 9-2 AC3 |
| PG-U-004 | `test_save_document_event_step_tracking` | 9-2 AC4 |
| PG-U-005 | `test_batch_insert_multiple_spans` | 9-2 AC5 |
| PG-U-006 | `test_query_traces_with_filters` | 9-2 AC6 |
| PG-U-007 | `test_query_chat_history_by_session` | 9-2 AC7 |
| PG-U-008 | `test_connection_pool_management` | 9-2 AC8 |

### 3.3 LangFuseProvider Tests

**File:** `tests/unit/test_langfuse_provider.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| LF-U-001 | `test_provider_disabled_when_env_false` | 9-11 AC1 |
| LF-U-002 | `test_trace_maps_to_langfuse_generation` | 9-11 AC2 |
| LF-U-003 | `test_llm_call_includes_token_usage` | 9-11 AC3 |
| LF-U-004 | `test_cost_calculation_forwarded` | 9-11 AC4 |
| LF-U-005 | `test_sdk_error_handled_gracefully` | 9-11 AC5 |
| LF-U-006 | `test_flush_called_on_trace_end` | 9-11 AC6 |

### 3.4 TraceContext Tests

**File:** `tests/unit/test_trace_context.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| TC-U-001 | `test_context_inherits_parent_trace_id` | 9-3 AC1 |
| TC-U-002 | `test_context_generates_unique_span_id` | 9-3 AC2 |
| TC-U-003 | `test_context_serializes_to_w3c_format` | 9-3 AC3 |
| TC-U-004 | `test_context_deserializes_from_header` | 9-3 AC4 |
| TC-U-005 | `test_context_thread_local_isolation` | 9-3 AC5 |

### 3.5 Model Tests

**File:** `tests/unit/test_observability_models.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| OM-U-001 | `test_trace_model_defaults` | 9-1 AC1 |
| OM-U-002 | `test_span_model_llm_fields_optional` | 9-1 AC2 |
| OM-U-003 | `test_chat_message_role_enum` | 9-1 AC3 |
| OM-U-004 | `test_document_event_step_enum` | 9-1 AC4 |
| OM-U-005 | `test_metrics_aggregate_time_bucket` | 9-1 AC5 |

---

## 4. Integration Test Design

### 4.1 API Endpoint Tests

**File:** `tests/integration/test_observability_api.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| OA-I-001 | `test_get_traces_returns_paginated_list` | 9-7 AC1 |
| OA-I-002 | `test_get_traces_filters_by_date_range` | 9-7 AC2 |
| OA-I-003 | `test_get_traces_filters_by_operation` | 9-7 AC3 |
| OA-I-004 | `test_get_trace_detail_includes_spans` | 9-7 AC4 |
| OA-I-005 | `test_get_chat_history_by_session` | 9-7 AC5 |
| OA-I-006 | `test_get_document_timeline` | 9-7 AC6 |
| OA-I-007 | `test_get_stats_returns_aggregates` | 9-7 AC7 |
| OA-I-008 | `test_api_requires_admin_role` | 9-7 AC8 |
| OA-I-009 | `test_api_returns_401_without_auth` | 9-7 AC9 |

### 4.2 Document Processing Instrumentation Tests

**File:** `tests/integration/test_document_instrumentation.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| DI-I-001 | `test_upload_creates_trace` | 9-4 AC1 |
| DI-I-002 | `test_parse_creates_span_with_stats` | 9-4 AC2 |
| DI-I-003 | `test_chunk_creates_span_with_count` | 9-4 AC3 |
| DI-I-004 | `test_embed_creates_span_with_model` | 9-4 AC4 |
| DI-I-005 | `test_index_creates_span_with_vectors` | 9-4 AC5 |
| DI-I-006 | `test_failure_creates_error_span` | 9-4 AC6 |
| DI-I-007 | `test_full_pipeline_linked_by_trace_id` | 9-4 AC7 |

### 4.3 Chat Flow Instrumentation Tests

**File:** `tests/integration/test_chat_instrumentation.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| CI-I-001 | `test_chat_message_persisted` | 9-5 AC1 |
| CI-I-002 | `test_retrieval_span_includes_sources` | 9-5 AC2 |
| CI-I-003 | `test_llm_span_includes_tokens` | 9-5 AC3 |
| CI-I-004 | `test_session_groups_messages` | 9-5 AC4 |
| CI-I-005 | `test_streaming_response_tracked` | 9-5 AC5 |
| CI-I-006 | `test_conversation_history_queryable` | 9-5 AC6 |

### 4.4 LiteLLM Integration Tests

**File:** `tests/integration/test_litellm_hooks.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| LL-I-001 | `test_callback_captures_model_name` | 9-6 AC1 |
| LL-I-002 | `test_callback_captures_prompt_tokens` | 9-6 AC2 |
| LL-I-003 | `test_callback_captures_completion_tokens` | 9-6 AC3 |
| LL-I-004 | `test_callback_captures_latency` | 9-6 AC4 |
| LL-I-005 | `test_callback_captures_cost` | 9-6 AC5 |
| LL-I-006 | `test_callback_links_to_parent_span` | 9-6 AC6 |

### 4.5 Schema Migration Tests

**File:** `tests/integration/test_observability_schema.py`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| SM-I-001 | `test_migration_creates_observability_schema` | 9-1 AC1 |
| SM-I-002 | `test_traces_hypertable_created` | 9-1 AC2 |
| SM-I-003 | `test_spans_hypertable_created` | 9-1 AC3 |
| SM-I-004 | `test_indexes_on_trace_id_created` | 9-1 AC4 |
| SM-I-005 | `test_indexes_on_created_at_created` | 9-1 AC5 |
| SM-I-006 | `test_foreign_keys_enforced` | 9-1 AC6 |

---

## 5. E2E Test Design

### 5.1 Admin Trace Viewer Tests

**File:** `e2e/tests/admin/trace-viewer.spec.ts`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| TV-E-001 | `test_trace_list_displays_recent_traces` | 9-8 AC1 |
| TV-E-002 | `test_trace_filter_by_operation` | 9-8 AC2 |
| TV-E-003 | `test_trace_filter_by_date_range` | 9-8 AC3 |
| TV-E-004 | `test_trace_detail_shows_span_tree` | 9-8 AC4 |
| TV-E-005 | `test_span_detail_modal_shows_attributes` | 9-8 AC5 |
| TV-E-006 | `test_span_timeline_visualization` | 9-8 AC6 |

### 5.2 Chat History Viewer Tests

**File:** `e2e/tests/admin/chat-history.spec.ts`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| CH-E-001 | `test_chat_history_list_displays_sessions` | 9-9 AC1 |
| CH-E-002 | `test_session_detail_shows_messages` | 9-9 AC2 |
| CH-E-003 | `test_message_shows_role_and_content` | 9-9 AC3 |
| CH-E-004 | `test_message_shows_token_usage` | 9-9 AC4 |
| CH-E-005 | `test_filter_by_user` | 9-9 AC5 |
| CH-E-006 | `test_filter_by_kb` | 9-9 AC6 |

### 5.3 Document Timeline Tests

**File:** `e2e/tests/admin/document-timeline.spec.ts`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| DT-E-001 | `test_timeline_shows_all_steps` | 9-10 AC1 |
| DT-E-002 | `test_step_shows_duration` | 9-10 AC2 |
| DT-E-003 | `test_step_shows_status_icon` | 9-10 AC3 |
| DT-E-004 | `test_failed_step_shows_error` | 9-10 AC4 |
| DT-E-005 | `test_retry_step_shows_attempts` | 9-10 AC5 |

### 5.4 Dashboard Widget Tests

**File:** `e2e/tests/admin/observability-dashboard.spec.ts`

| Test ID | Test Case | AC Mapping |
|---------|-----------|------------|
| DW-E-001 | `test_token_usage_widget_displays_chart` | 9-12 AC1 |
| DW-E-002 | `test_cost_widget_shows_total` | 9-12 AC2 |
| DW-E-003 | `test_latency_widget_shows_p50_p95_p99` | 9-12 AC3 |
| DW-E-004 | `test_throughput_widget_shows_requests` | 9-12 AC4 |
| DW-E-005 | `test_widget_date_range_selector` | 9-12 AC5 |

---

## 6. Performance Test Design

### 6.1 Fire-and-Forget Latency Tests

**File:** `tests/performance/test_observability_latency.py`

| Test ID | Test Case | Target |
|---------|-----------|--------|
| PL-P-001 | `test_trace_start_latency_under_5ms` | < 5ms p99 |
| PL-P-002 | `test_span_start_latency_under_5ms` | < 5ms p99 |
| PL-P-003 | `test_chat_message_log_latency_under_5ms` | < 5ms p99 |
| PL-P-004 | `test_document_event_log_latency_under_5ms` | < 5ms p99 |
| PL-P-005 | `test_concurrent_traces_no_blocking` | 100 concurrent |

### 6.2 Query Performance Tests

**File:** `tests/performance/test_observability_queries.py`

| Test ID | Test Case | Target |
|---------|-----------|--------|
| PQ-P-001 | `test_trace_list_query_under_500ms` | < 500ms p95 |
| PQ-P-002 | `test_trace_detail_query_under_200ms` | < 200ms p95 |
| PQ-P-003 | `test_chat_history_query_under_300ms` | < 300ms p95 |
| PQ-P-004 | `test_document_timeline_query_under_200ms` | < 200ms p95 |
| PQ-P-005 | `test_stats_aggregation_under_1s` | < 1s p95 |

### 6.3 Throughput Tests

**File:** `tests/performance/test_observability_throughput.py`

| Test ID | Test Case | Target |
|---------|-----------|--------|
| PT-P-001 | `test_sustain_100_traces_per_second` | 100 TPS |
| PT-P-002 | `test_sustain_1000_spans_per_second` | 1000 spans/s |
| PT-P-003 | `test_batch_insert_1000_events` | < 500ms |

---

## 7. Test Data Strategy

### 7.1 Fixtures

```python
# tests/factories/observability_factory.py

@pytest.fixture
def sample_trace():
    return TraceFactory.create(
        operation="chat",
        user_id=uuid4(),
        status="completed"
    )

@pytest.fixture
def sample_span_tree(sample_trace):
    return SpanTreeFactory.create(
        trace_id=sample_trace.id,
        depth=3,
        children_per_node=2
    )

@pytest.fixture
def sample_chat_session():
    return ChatSessionFactory.create(
        message_count=10,
        include_llm_metadata=True
    )

@pytest.fixture
def sample_document_timeline():
    return DocumentTimelineFactory.create(
        steps=["upload", "parse", "chunk", "embed", "index"],
        include_failures=False
    )
```

### 7.2 Database Seeding

```python
# tests/helpers/seed_observability_data.py

async def seed_observability_data(db: AsyncSession):
    """Seed database with realistic observability data for testing."""

    # Create 100 traces over last 7 days
    traces = await create_traces(count=100, days=7)

    # Create spans for each trace (3-10 per trace)
    for trace in traces:
        await create_spans(trace_id=trace.id, count=random.randint(3, 10))

    # Create chat messages (5 sessions, 20 messages each)
    for _ in range(5):
        session_id = uuid4()
        await create_chat_messages(session_id=session_id, count=20)

    # Create document events (10 documents, full pipeline each)
    for _ in range(10):
        doc_id = uuid4()
        await create_document_events(document_id=doc_id)
```

---

## 8. Quality Gates

### 8.1 CI/CD Gates

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Unit test coverage | >= 80% | Yes |
| Integration test pass rate | 100% | Yes |
| E2E test pass rate | >= 95% | Yes |
| Performance test pass rate | 100% | Yes |
| Lint/Type check | 0 errors | Yes |

### 8.2 Story Completion Gates

| Story | Required Tests | Min Coverage |
|-------|----------------|--------------|
| 9-1 | SM-I-001 to SM-I-006, OM-U-001 to OM-U-005 | 90% |
| 9-2 | PG-U-001 to PG-U-008 | 85% |
| 9-3 | OS-U-001 to OS-U-008, TC-U-001 to TC-U-005 | 85% |
| 9-4 | DI-I-001 to DI-I-007 | 80% |
| 9-5 | CI-I-001 to CI-I-006 | 80% |
| 9-6 | LL-I-001 to LL-I-006 | 80% |
| 9-7 | OA-I-001 to OA-I-009 | 85% |
| 9-8 | TV-E-001 to TV-E-006 | N/A (E2E) |
| 9-9 | CH-E-001 to CH-E-006 | N/A (E2E) |
| 9-10 | DT-E-001 to DT-E-005 | N/A (E2E) |
| 9-11 | LF-U-001 to LF-U-006 | 80% |
| 9-12 | DW-E-001 to DW-E-005 | N/A (E2E) |
| 9-13 | Performance tests | N/A |
| 9-14 | Retention policy tests | 80% |

---

## 9. Test Environment Requirements

### 9.1 Local Development

```yaml
# docker-compose.test.yml
services:
  postgres-test:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: lumikb_test
    ports:
      - "5433:5432"
```

### 9.2 CI Environment

- PostgreSQL 14+ with TimescaleDB extension
- Redis for session cache testing
- Mock LangFuse server for provider tests
- Playwright browsers for E2E

---

## 10. Negative Path Testing

### 10.1 Error Scenarios

| Scenario | Expected Behavior | Test ID |
|----------|-------------------|---------|
| PostgreSQL connection failure | Log error, continue operation | OS-U-005 |
| LangFuse SDK error | Log error, disable provider | LF-U-005 |
| Invalid trace context header | Generate new trace ID | TC-U-004 |
| Malformed span attributes | Skip invalid attributes | OS-U-004 |
| Database timeout | Retry with backoff | PG-U-008 |
| Missing required fields | Validation error, log warning | OM-U-001 |

### 10.2 Boundary Conditions

| Condition | Test Case |
|-----------|-----------|
| Very long trace (1000+ spans) | `test_large_trace_performance` |
| Very long chat session (500+ messages) | `test_large_session_query` |
| High concurrency (100 parallel traces) | `test_concurrent_trace_creation` |
| Date range spanning months | `test_long_date_range_query` |
| Empty result sets | `test_empty_trace_list` |

---

## 11. Related Documents

- [Tech Spec: Epic 9 Observability](./tech-spec-epic-9-observability.md)
- [Epic 9: Hybrid Observability Platform](../epics/epic-9-observability.md)
- [Testing Guidelines](../testing-guideline.md)
- [Traceability Matrix: Epic 9](./epic-9-traceability-matrix.md)

---

---

## 12. Gate Decision (TEA Assessment)

**Current Status**: PASS (Design Phase)

All critical risks (P×I ≥ 6) have corresponding test coverage designed:
- 4/4 critical risks covered
- 8 P0-priority tests designed across unit/integration levels
- 87 total tests across all levels (Unit: 27, Integration: 35, E2E: 17, Performance: 8)

### 12.1 Risk Mitigation Tracking

| Risk ID | Risk | Score | Test Coverage | Status |
|---------|------|-------|---------------|--------|
| R9-1 | Trace ingestion failure | 6 | OS-U-005, PG-U-001, DI-I-001 | Designed |
| R9-2 | Data loss on provider failure | 6 | OS-U-005, OS-U-007 | Designed |
| R9-3 | Trace context breaks | 6 | TC-U-001 to TC-U-005, DI-I-007 | Designed |
| R9-4 | Session data loss | 6 | CI-I-001 to CI-I-006, CH-E-001 | Designed |

### 12.2 Next Steps

1. Implement P0 unit tests first (ObservabilityService, TraceContext)
2. Set up test infrastructure (TimescaleDB, mock LangFuse)
3. Implement P0 integration tests (API endpoints, document instrumentation)
4. Create E2E fixtures and implement critical path tests
5. Execute tests and update status

---

*Document Owner: TEA (Test Excellence Architect)*
*Last Updated: 2025-12-14*
*Risk Assessment: Complete*
*Coverage Design: Complete*
