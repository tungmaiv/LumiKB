# Traceability Matrix - Epic 9: Hybrid Observability Platform

**Version:** 1.0
**Date:** 2025-12-14
**Author:** Bob (Scrum Master)

---

## 1. PRD → Epic → Stories Mapping

| PRD FR | Description | Epic 9 Story | Notes |
|--------|-------------|--------------|-------|
| FR111 | W3C Trace Context propagation | 9-3 | TraceContext implementation |
| FR112 | TimescaleDB for time-series observability | 9-1 | Schema with hypertables |
| FR113 | Document processing event tracking | 9-4 | Instrumentation hooks |
| FR114 | LLM call tracking (model, tokens, cost) | 9-6 | LiteLLM callback integration |
| FR115 | Chat history persistence | 9-5 | PostgreSQL chat_messages table |
| FR116 | Distributed span hierarchy | 9-2, 9-3 | Parent-child span relationships |
| FR117 | Token usage aggregation | 9-13 | Metrics aggregation worker |
| FR118 | Cost tracking per operation | 9-6, 9-12 | LLM callback + dashboard |
| FR119 | Latency percentiles (p50/p95/p99) | 9-12 | Dashboard widgets |
| FR120 | Admin observability API | 9-7 | REST endpoints |
| FR121 | Trace viewer UI | 9-8 | Admin component |
| FR122 | Chat history viewer UI | 9-9 | Admin component |
| FR123 | Observability dashboard | 9-12 | Dashboard widgets |
| FR124 | LangFuse integration (optional) | 9-11 | Provider implementation |
| FR125 | Data retention policies | 9-14 | Cleanup worker |

---

## 2. Stories → Acceptance Criteria → Tech Spec Sections

### Story 9-1: Observability Schema & Models

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Alembic migration creates observability schema | 4.1 PostgreSQL Schema | Migration file |
| AC2 | traces hypertable with 1-day chunks | 4.1.1 traces table | TimescaleDB |
| AC3 | spans hypertable with trace_id FK | 4.1.2 spans table | TimescaleDB |
| AC4 | chat_messages table with session_id | 4.1.3 chat_messages table | PostgreSQL |
| AC5 | document_events table with step enum | 4.1.4 document_events table | PostgreSQL |
| AC6 | metrics_aggregates for pre-computed stats | 4.1.5 metrics_aggregates | PostgreSQL |
| AC7 | Indexes on trace_id, created_at, user_id | 4.1.6 Indexes | PostgreSQL |
| AC8 | provider_sync_status for external sync | 4.1.7 provider_sync_status | PostgreSQL |
| AC9 | SQLAlchemy models match schema | 4.2 SQLAlchemy Models | Python models |
| AC10 | Unit tests verify model CRUD | test-design-epic-9 OM-U-* | pytest |

### Story 9-2: PostgreSQL Provider Implementation

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | PostgreSQLProvider implements ObservabilityProvider | 5.1.2 PostgreSQLProvider | Provider class |
| AC2 | start_trace() persists to traces table | 5.1.2 start_trace | Method |
| AC3 | end_trace() updates duration, status | 5.1.2 end_trace | Method |
| AC4 | start_span() creates span record | 5.1.2 start_span | Method |
| AC5 | end_span() updates timing, attributes | 5.1.2 end_span | Method |
| AC6 | log_llm_call() populates LLM-specific fields | 5.1.2 log_llm_call | Method |
| AC7 | log_chat_message() persists to chat_messages | 5.1.2 log_chat_message | Method |
| AC8 | log_document_event() persists to document_events | 5.1.2 log_document_event | Method |
| AC9 | Connection pooling configured | 9.1 Configuration | asyncpg pool |
| AC10 | Integration tests verify data persistence | test-design-epic-9 PG-U-* | pytest |

### Story 9-3: TraceContext & Core Service

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | TraceContext class with W3C format | 5.1.1 TraceContext | Context class |
| AC2 | Context propagates trace_id across calls | 5.1.1 propagation | Context var |
| AC3 | Context generates unique span_id | 5.1.1 span_id | UUID generation |
| AC4 | ObservabilityService facade created | 5.1.3 ObservabilityService | Facade class |
| AC5 | Provider registry pattern | 5.1.3 ProviderRegistry | Registry |
| AC6 | Fire-and-forget async dispatch | 5.1.3 dispatch | asyncio |
| AC7 | Provider failures don't propagate | 5.1.3 error handling | try/except |
| AC8 | Context manager for spans | 5.1.1 @trace_span | Decorator |
| AC9 | HTTP header extraction | 5.1.1 from_headers | Parser |
| AC10 | Unit tests for context management | test-design-epic-9 TC-U-* | pytest |

### Story 9-4: Document Processing Instrumentation

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Upload creates parent trace | 5.2.1 Instrumentation Points | upload_document |
| AC2 | Parse step creates child span | 5.2.1 parse_document | Celery task |
| AC3 | Chunk step creates child span | 5.2.1 chunk_document | Celery task |
| AC4 | Embed step creates child span | 5.2.1 embed_chunks | Celery task |
| AC5 | Index step creates child span | 5.2.1 index_vectors | Celery task |
| AC6 | Failure creates error span | 5.2.1 error handling | Exception hook |
| AC7 | All spans linked by trace_id | 5.2.1 trace propagation | Header passing |
| AC8 | Step metrics (pages, chunks, vectors) | 5.2.1 span attributes | Metadata |
| AC9 | document_events populated | 5.1.2 log_document_event | Event logging |
| AC10 | E2E test: upload → verify trace | test-design-epic-9 DI-I-* | Integration |

### Story 9-5: Chat/RAG Flow Instrumentation

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Chat message persisted | 5.2.2 Chat Instrumentation | chat_messages |
| AC2 | Retrieval span with sources | 5.2.2 retrieval_span | Span attributes |
| AC3 | LLM span with tokens | 5.2.2 llm_span | Token tracking |
| AC4 | Session groups messages | 5.2.2 session_id | Grouping |
| AC5 | Streaming response tracked | 5.2.2 streaming | Event stream |
| AC6 | Conversation history queryable | 6.1.3 chat-history endpoint | API |
| AC7 | User/KB context attached | 5.2.2 context | Metadata |
| AC8 | Response time tracked | 5.2.2 latency | Timing |
| AC9 | Citations linked | 5.2.2 citations | References |
| AC10 | Integration test: messages persisted | test-design-epic-9 CI-I-* | Integration |

### Story 9-6: LiteLLM Integration Hooks

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | LiteLLM callback registered | 5.2.3 LiteLLM Hooks | Callback class |
| AC2 | Model name captured | 5.2.3 model | Attribute |
| AC3 | Prompt tokens captured | 5.2.3 prompt_tokens | Metric |
| AC4 | Completion tokens captured | 5.2.3 completion_tokens | Metric |
| AC5 | Latency captured | 5.2.3 latency_ms | Timing |
| AC6 | Cost calculated | 5.2.3 cost_usd | Calculation |
| AC7 | Parent span linked | 5.2.3 parent_span_id | Context |
| AC8 | Streaming mode handled | 5.2.3 stream | Token accumulation |
| AC9 | Error responses tracked | 5.2.3 error | Status |
| AC10 | Integration test: LLM call traced | test-design-epic-9 LL-I-* | Integration |

### Story 9-7: Observability Admin API

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | GET /observability/traces | 6.1.1 traces endpoint | FastAPI route |
| AC2 | Pagination support | 6.1.1 pagination | Query params |
| AC3 | Date range filter | 6.1.1 filters | Query params |
| AC4 | Operation filter | 6.1.1 filters | Query params |
| AC5 | GET /traces/{trace_id} with spans | 6.1.2 trace detail | FastAPI route |
| AC6 | GET /chat-history | 6.1.3 chat history | FastAPI route |
| AC7 | GET /documents/{id}/timeline | 6.1.4 document timeline | FastAPI route |
| AC8 | GET /stats | 6.1.5 statistics | FastAPI route |
| AC9 | Admin role required | 6.1 Security | Dependency |
| AC10 | Integration tests | test-design-epic-9 OA-I-* | Integration |

### Story 9-8: Trace Viewer UI Component

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Trace list table | 7.1 Implementation Plan | React component |
| AC2 | Filter controls | UI design | Component |
| AC3 | Trace detail modal | UI design | Component |
| AC4 | Span tree visualization | UI design | Component |
| AC5 | Span detail panel | UI design | Component |
| AC6 | Timeline chart | UI design | Component |
| AC7 | Loading states | UI design | UX |
| AC8 | Error handling | UI design | UX |
| AC9 | Responsive layout | UI design | CSS |
| AC10 | E2E tests | test-design-epic-9 TV-E-* | Playwright |

### Story 9-9: Chat History Viewer UI

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Session list | 7.1 Implementation Plan | React component |
| AC2 | Message thread view | UI design | Component |
| AC3 | Role indicators | UI design | UI |
| AC4 | Token usage display | UI design | Metrics |
| AC5 | User filter | UI design | Filter |
| AC6 | KB filter | UI design | Filter |
| AC7 | Search within messages | UI design | Search |
| AC8 | Export functionality | UI design | Action |
| AC9 | Pagination | UI design | UX |
| AC10 | E2E tests | test-design-epic-9 CH-E-* | Playwright |

### Story 9-10: Document Timeline UI

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Timeline visualization | 7.1 Implementation Plan | React component |
| AC2 | Step duration bars | UI design | Visualization |
| AC3 | Status icons | UI design | Icons |
| AC4 | Error details | UI design | Expandable |
| AC5 | Retry indicators | UI design | UI |
| AC6 | Linked from document detail | Navigation | Route |
| AC7 | Responsive design | UI design | CSS |
| AC8 | Loading skeleton | UI design | UX |
| AC9 | Empty state | UI design | UX |
| AC10 | E2E tests | test-design-epic-9 DT-E-* | Playwright |

### Story 9-11: LangFuse Provider Implementation

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Provider disabled when env false | 5.1.4 LangFuseProvider | Config check |
| AC2 | Trace maps to LangFuse generation | 5.1.4 mapping | SDK call |
| AC3 | LLM call includes token usage | 5.1.4 tokens | Metadata |
| AC4 | Cost forwarded | 5.1.4 cost | Metadata |
| AC5 | SDK error handled gracefully | 5.1.4 error handling | try/except |
| AC6 | Flush on trace end | 5.1.4 flush | SDK call |
| AC7 | Tags and metadata | 5.1.4 metadata | Enrichment |
| AC8 | Sync status tracked | 4.1.7 provider_sync_status | Tracking |
| AC9 | Health check | 5.1.4 health | Endpoint |
| AC10 | Unit tests | test-design-epic-9 LF-U-* | pytest |

### Story 9-12: Observability Dashboard Widgets

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Token usage chart | 7.1 Implementation Plan | Chart component |
| AC2 | Cost summary widget | UI design | Widget |
| AC3 | Latency percentiles | UI design | Chart |
| AC4 | Throughput chart | UI design | Chart |
| AC5 | Date range selector | UI design | Control |
| AC6 | Real-time updates | UI design | Polling/SSE |
| AC7 | Dashboard layout | UI design | Grid |
| AC8 | Widget configuration | UI design | Settings |
| AC9 | Export to CSV | UI design | Action |
| AC10 | E2E tests | test-design-epic-9 DW-E-* | Playwright |

### Story 9-13: Metrics Aggregation Worker

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Celery beat schedule | 5.3 Workers | Schedule |
| AC2 | Hourly aggregation | 5.3.1 aggregation | Task |
| AC3 | Daily aggregation | 5.3.1 aggregation | Task |
| AC4 | metrics_aggregates populated | 4.1.5 table | Data |
| AC5 | Incremental updates | 5.3.1 incremental | Logic |
| AC6 | Idempotent execution | 5.3.1 idempotent | Design |
| AC7 | Error recovery | 5.3.1 retry | Error handling |
| AC8 | Performance optimization | 5.3.1 batch | Batching |
| AC9 | Logging | 5.3.1 logging | Observability |
| AC10 | Unit tests | test-design-epic-9 | pytest |

### Story 9-14: Data Retention & Cleanup

| AC | Description | Tech Spec Section | Component |
|----|-------------|-------------------|-----------|
| AC1 | Retention policy configurable | 9.1 Environment Variables | Config |
| AC2 | Celery beat schedule | 5.3 Workers | Schedule |
| AC3 | TimescaleDB drop_chunks used | 5.3.2 retention | SQL |
| AC4 | Cascade delete for related data | 5.3.2 cascade | Logic |
| AC5 | Dry-run mode | 5.3.2 dry-run | Safety |
| AC6 | Audit log of deletions | 5.3.2 logging | Compliance |
| AC7 | Compression policy | 5.3.2 compression | TimescaleDB |
| AC8 | Provider sync cleanup | 5.3.2 sync cleanup | LangFuse |
| AC9 | Alerting on failures | 5.3.2 alerting | Monitoring |
| AC10 | Unit tests | test-design-epic-9 | pytest |

---

## 3. Test Cases → Stories Mapping

| Test File | Test IDs | Stories Covered |
|-----------|----------|-----------------|
| test_observability_service.py | OS-U-001 to OS-U-008 | 9-3 |
| test_postgresql_provider.py | PG-U-001 to PG-U-008 | 9-2 |
| test_langfuse_provider.py | LF-U-001 to LF-U-006 | 9-11 |
| test_trace_context.py | TC-U-001 to TC-U-005 | 9-3 |
| test_observability_models.py | OM-U-001 to OM-U-005 | 9-1 |
| test_observability_api.py | OA-I-001 to OA-I-009 | 9-7 |
| test_document_instrumentation.py | DI-I-001 to DI-I-007 | 9-4 |
| test_chat_instrumentation.py | CI-I-001 to CI-I-006 | 9-5 |
| test_litellm_hooks.py | LL-I-001 to LL-I-006 | 9-6 |
| test_observability_schema.py | SM-I-001 to SM-I-006 | 9-1 |
| trace-viewer.spec.ts | TV-E-001 to TV-E-006 | 9-8 |
| chat-history.spec.ts | CH-E-001 to CH-E-006 | 9-9 |
| document-timeline.spec.ts | DT-E-001 to DT-E-005 | 9-10 |
| observability-dashboard.spec.ts | DW-E-001 to DW-E-005 | 9-12 |

---

## 4. Component → Stories Mapping

| Component | File Path | Stories |
|-----------|-----------|---------|
| TraceContext | app/services/observability/trace_context.py | 9-3 |
| ObservabilityService | app/services/observability/service.py | 9-3 |
| PostgreSQLProvider | app/services/observability/providers/postgresql.py | 9-2 |
| LangFuseProvider | app/services/observability/providers/langfuse.py | 9-11 |
| ObservabilityProvider (ABC) | app/services/observability/providers/base.py | 9-2, 9-11 |
| Trace Model | app/models/observability/trace.py | 9-1 |
| Span Model | app/models/observability/span.py | 9-1 |
| ChatMessage Model | app/models/observability/chat_message.py | 9-1 |
| DocumentEvent Model | app/models/observability/document_event.py | 9-1 |
| MetricsAggregate Model | app/models/observability/metrics.py | 9-1 |
| Observability Router | app/api/v1/observability.py | 9-7 |
| TraceViewer Component | src/components/admin/trace-viewer.tsx | 9-8 |
| ChatHistoryViewer | src/components/admin/chat-history-viewer.tsx | 9-9 |
| DocumentTimeline | src/components/admin/document-timeline.tsx | 9-10 |
| ObservabilityDashboard | src/components/admin/observability-dashboard.tsx | 9-12 |
| MetricsWorker | app/workers/observability_tasks.py | 9-13 |
| RetentionWorker | app/workers/observability_tasks.py | 9-14 |

---

## 5. Coverage Summary

| Category | Total Items | Stories | Coverage |
|----------|-------------|---------|----------|
| PRD Requirements | 15 (FR111-FR125) | 14 | 100% |
| Epic Stories | 14 | 14 | 100% |
| Acceptance Criteria | 140 | 14 | 100% |
| Unit Test Cases | 35 | 6 | 100% |
| Integration Test Cases | 31 | 7 | 100% |
| E2E Test Cases | 22 | 4 | 100% |
| Backend Components | 11 | 7 | 100% |
| Frontend Components | 4 | 4 | 100% |

---

## 6. Dependencies

| Story | Depends On | Dependency Type |
|-------|------------|-----------------|
| 9-2 | 9-1 | Schema required |
| 9-3 | 9-2 | Provider required |
| 9-4 | 9-3 | Service required |
| 9-5 | 9-3 | Service required |
| 9-6 | 9-3 | Service required |
| 9-7 | 9-2, 9-3 | Data layer required |
| 9-8 | 9-7 | API required |
| 9-9 | 9-7 | API required |
| 9-10 | 9-7 | API required |
| 9-11 | 9-3 | Registry required |
| 9-12 | 9-7 | API required |
| 9-13 | 9-1, 9-2 | Schema + Provider required |
| 9-14 | 9-1 | Schema required |

---

## Related Documents

- [Tech Spec: Epic 9 Observability](./tech-spec-epic-9-observability.md)
- [Test Design: Epic 9](./test-design-epic-9.md)
- [Epic 9: Hybrid Observability Platform](../epics/epic-9-observability.md)
- [PRD: Observability Requirements](../prd.md#observability)

---

*Document Owner: Bob (Scrum Master)*
*Last Updated: 2025-12-14*
