# Epic 9: Hybrid Observability Platform

**Epic ID:** EPIC-9
**Status:** Draft
**Priority:** High
**Estimated Points:** 70
**Target Sprint:** Sprint 17-21

---

## Epic Summary

Implement a comprehensive Hybrid Observability Platform that provides full visibility into LumiKB's document processing pipelines, chat/RAG operations, and LLM interactions. The platform uses internal PostgreSQL storage (always-on) with optional LangFuse integration for advanced LLM analytics.

## Business Value

- **Operational Visibility:** Admins can track all document processing steps in real-time
- **Debug Capability:** Trace end-to-end requests across services for troubleshooting
- **Chat History:** Persistent storage of all user conversations for compliance and analysis
- **Cost Tracking:** Monitor LLM token usage and costs across all operations
- **Performance Insights:** Identify bottlenecks in processing pipelines and chat responses

## Key Features

1. **Distributed Tracing** - W3C-compliant trace context across all services
2. **Document Processing Timeline** - Step-by-step visibility into parse/chunk/embed/index
3. **Chat History Persistence** - PostgreSQL storage of all conversations (not just Redis cache)
4. **LLM Call Tracking** - Model, tokens, latency, cost for every LLM invocation
5. **Admin Dashboard** - Visual trace viewer, chat browser, and observability widgets
6. **Optional LangFuse** - External provider for advanced LLM analytics when needed

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ObservabilityService                      │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   TraceContext  │  │ Provider Registry│                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────┐   ┌──────────────────────┐
│ PostgreSQL Provider  │   │  LangFuse Provider   │
│   (Always Active)    │   │    (Optional)        │
└──────────────────────┘   └──────────────────────┘
                │
                ▼
┌──────────────────────┐
│  observability.*     │
│  - traces            │
│  - spans             │
│  - chat_messages     │
│  - document_events   │
└──────────────────────┘
```

## Stories

### Phase 1: Core Infrastructure (13 points)

| ID | Title | Points | Priority |
|----|-------|--------|----------|
| 9-1 | Observability Schema & Models | 5 | P0 |
| 9-2 | PostgreSQL Provider Implementation | 5 | P0 |
| 9-3 | TraceContext & Core Service | 3 | P0 |

### Phase 2: Pipeline Instrumentation (13 points)

| ID | Title | Points | Priority |
|----|-------|--------|----------|
| 9-4 | Document Processing Instrumentation | 5 | P0 |
| 9-5 | Chat/RAG Flow Instrumentation | 5 | P0 |
| 9-6 | LiteLLM Integration Hooks | 3 | P0 |

### Phase 3: API & UI (18 points)

| ID | Title | Points | Priority |
|----|-------|--------|----------|
| 9-7 | Observability Admin API | 5 | P0 |
| 9-8 | Trace Viewer UI Component | 5 | P1 |
| 9-9 | Chat History Viewer UI | 5 | P1 |
| 9-10 | Document Timeline UI | 3 | P1 |

### Phase 4: Advanced Features (26 points)

| ID | Title | Points | Priority |
|----|-------|--------|----------|
| 9-11 | LangFuse Provider Implementation | 5 | P1 |
| 9-12 | Observability Dashboard Widgets | 5 | P1 |
| 9-13 | Metrics Aggregation Worker | 5 | P2 |
| 9-14 | Data Retention & Cleanup | 3 | P2 |
| 9-15 | KB Debug Mode & Prompt Integration | 8 | P1 |

## Dependencies

- **Epic 4:** Chat infrastructure (conversation service, generation service)
- **Epic 5:** Admin dashboard (for embedding observability widgets)
- **Epic 7:** KB configuration (for per-KB observability settings)

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary Storage | PostgreSQL + TimescaleDB | Time-series optimization, no new infrastructure |
| External Provider | LangFuse (optional) | Best LLM analytics, good Python SDK |
| Trace Format | W3C Trace Context | Industry standard, future OpenTelemetry compatibility |
| Chat Persistence | PostgreSQL (primary) + Redis (cache) | Compliance-friendly, Redis for hot data |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance impact from logging | Medium | Medium | Fire-and-forget async pattern |
| Storage growth | Medium | Low | TimescaleDB compression + retention policies |
| LangFuse SDK compatibility | Low | Medium | Use OTEL bridge, test thoroughly |
| Migration complexity | Low | Medium | Coexist with existing audit, gradual migration |

## Success Criteria

- [ ] All document processing steps visible with timing and metrics
- [ ] All chat conversations persisted and queryable
- [ ] LLM token usage and cost tracked per operation
- [ ] Admin can trace any request end-to-end
- [ ] Dashboard shows real-time observability metrics
- [ ] Data retention automatically enforced

## Configuration

```env
# Internal observability (always enabled)
OBSERVABILITY_ENABLED=true
OBSERVABILITY_RETENTION_DAYS=90

# External LangFuse (optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Related Documents

- [Tech Spec: Epic 9 Observability](../sprint-artifacts/tech-spec-epic-9-observability.md)
- [PRD: Observability Requirements](../prd.md#observability)
- [Architecture: Monitoring Stack](../architecture.md#monitoring)

---

*Epic Owner: Architecture Team*
*Last Updated: 2025-12-14*
