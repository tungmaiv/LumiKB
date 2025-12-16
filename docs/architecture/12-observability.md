# 12 - Observability Architecture

## Overview

LumiKB implements a **Hybrid Observability Platform** that provides full visibility into document processing pipelines, chat/RAG operations, and LLM interactions. The architecture uses internal PostgreSQL storage (always-on) with optional LangFuse integration for advanced LLM analytics.

## Architecture Diagram

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

## Key Components

### 1. TraceContext

W3C-compliant trace context propagation:

```python
@dataclass
class TraceContext:
    trace_id: str      # 32-byte hex (128-bit)
    span_id: str       # 16-byte hex (64-bit)
    parent_span_id: Optional[str] = None

    @classmethod
    def generate(cls) -> "TraceContext":
        return cls(
            trace_id=secrets.token_hex(16),
            span_id=secrets.token_hex(8)
        )

    def child(self) -> "TraceContext":
        return TraceContext(
            trace_id=self.trace_id,
            span_id=secrets.token_hex(8),
            parent_span_id=self.span_id
        )
```

### 2. Provider Interface

Extensible provider pattern for multiple backends:

```python
class ObservabilityProvider(ABC):
    @abstractmethod
    async def record_span(self, span: SpanData) -> None: ...

    @abstractmethod
    async def record_llm_call(self, call: LLMCallData) -> None: ...

    @abstractmethod
    async def record_chat_message(self, message: ChatMessageData) -> None: ...

    @abstractmethod
    async def record_document_event(self, event: DocumentEventData) -> None: ...
```

### 3. PostgreSQL Provider (Always Active)

TimescaleDB-optimized storage for time-series observability data:

| Table | Purpose | Retention |
|-------|---------|-----------|
| `observability.traces` | Trace metadata with W3C context | 90 days |
| `observability.spans` | Individual operation spans | 90 days |
| `observability.llm_calls` | LLM invocations with tokens/cost | 90 days |
| `observability.chat_messages` | Persistent chat history | 365 days |
| `observability.document_events` | Processing timeline events | 90 days |

### 4. LangFuse Provider (Optional)

External integration for advanced LLM analytics when enabled:

```python
class LangFuseProvider(ObservabilityProvider):
    def __init__(self, public_key: str, secret_key: str, host: str):
        self.client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
```

## Data Models

### Trace

```python
class Trace(Base):
    __tablename__ = "traces"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public.users.id"))
    kb_id: Mapped[Optional[uuid.UUID]]
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    ended_at: Mapped[Optional[datetime]]
    status: Mapped[TraceStatus]
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
```

### Span

```python
class Span(Base):
    __tablename__ = "spans"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    span_id: Mapped[str] = mapped_column(String(16), unique=True)
    parent_span_id: Mapped[Optional[str]]
    name: Mapped[str] = mapped_column(String(255))
    span_type: Mapped[SpanType]  # DOCUMENT_PROCESSING, LLM_CALL, RETRIEVAL, etc.
    started_at: Mapped[datetime]
    ended_at: Mapped[Optional[datetime]]
    status: Mapped[SpanStatus]
    attributes: Mapped[dict] = mapped_column(JSONB, default={})
```

### LLM Call

```python
class LLMCall(Base):
    __tablename__ = "llm_calls"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    span_id: Mapped[str] = mapped_column(String(16), index=True)
    model: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    prompt_tokens: Mapped[int]
    completion_tokens: Mapped[int]
    total_tokens: Mapped[int]
    latency_ms: Mapped[int]
    estimated_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6))
    temperature: Mapped[Optional[float]]
    created_at: Mapped[datetime]
```

### Chat Message (Persistent)

```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(32))
    user_id: Mapped[uuid.UUID]
    kb_id: Mapped[uuid.UUID]
    role: Mapped[str]  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)
    sources_used: Mapped[list] = mapped_column(JSONB, default=[])
    created_at: Mapped[datetime]
```

## Integration Points

### Document Processing Pipeline

```python
async def process_document(document_id: UUID, ctx: TraceContext):
    # Create trace for entire processing
    trace = await observability.start_trace(
        name=f"process_document:{document_id}",
        ctx=ctx
    )

    # Parse stage
    with trace.span("parse", SpanType.DOCUMENT_PROCESSING) as span:
        result = await parse_document(document_id)
        span.set_attribute("pages", result.page_count)

    # Chunk stage
    with trace.span("chunk", SpanType.DOCUMENT_PROCESSING) as span:
        chunks = await chunk_document(result)
        span.set_attribute("chunk_count", len(chunks))

    # Embed stage
    with trace.span("embed", SpanType.DOCUMENT_PROCESSING) as span:
        embeddings = await embed_chunks(chunks)
        # LLM call automatically recorded

    # Index stage
    with trace.span("index", SpanType.DOCUMENT_PROCESSING) as span:
        await index_vectors(embeddings)

    await trace.end(status=TraceStatus.SUCCESS)
```

### Chat/RAG Flow

```python
async def handle_chat(message: str, kb_id: UUID, user_id: UUID):
    ctx = TraceContext.generate()

    trace = await observability.start_trace(
        name="chat",
        ctx=ctx,
        user_id=user_id,
        kb_id=kb_id
    )

    # Retrieval
    with trace.span("retrieval", SpanType.RETRIEVAL) as span:
        sources = await search_service.semantic_search(message, kb_id)
        span.set_attribute("sources_count", len(sources))

    # LLM Generation
    with trace.span("generation", SpanType.LLM_CALL) as span:
        response = await llm_client.generate(message, sources)
        # LLM call metrics automatically captured

    # Persist chat message
    await observability.record_chat_message(
        conversation_id=conversation_id,
        trace_id=ctx.trace_id,
        user_id=user_id,
        kb_id=kb_id,
        role="assistant",
        content=response.text,
        sources_used=response.citations
    )

    await trace.end()
```

### LiteLLM Integration

```python
# Callback hook for LiteLLM
class ObservabilityCallback(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        await observability.record_llm_call(
            span_id=kwargs.get("litellm_call_id"),
            model=kwargs.get("model"),
            provider=kwargs.get("custom_llm_provider"),
            prompt_tokens=response_obj.usage.prompt_tokens,
            completion_tokens=response_obj.usage.completion_tokens,
            latency_ms=int((end_time - start_time).total_seconds() * 1000),
            estimated_cost_usd=calculate_cost(kwargs.get("model"), response_obj.usage)
        )
```

## Admin API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/observability/traces` | GET | List traces with filters |
| `/api/v1/admin/observability/traces/{trace_id}` | GET | Get trace with all spans |
| `/api/v1/admin/observability/chat-history` | GET | Browse chat messages |
| `/api/v1/admin/observability/chat-history/{conversation_id}` | GET | Get conversation |
| `/api/v1/admin/observability/documents/{doc_id}/timeline` | GET | Processing timeline |
| `/api/v1/admin/observability/llm-costs` | GET | Aggregated LLM costs |
| `/api/v1/admin/observability/metrics` | GET | Dashboard metrics |

## Configuration

```env
# Internal observability (always enabled)
OBSERVABILITY_ENABLED=true
OBSERVABILITY_RETENTION_DAYS=90
OBSERVABILITY_CHAT_RETENTION_DAYS=365

# External LangFuse (optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Performance Considerations

1. **Fire-and-Forget Pattern**: All observability writes are non-blocking
2. **TimescaleDB Compression**: Automatic compression for data older than 7 days
3. **Partitioning**: Daily partitions for high-volume tables
4. **Retention Policies**: Automatic cleanup via TimescaleDB policies

## Related Documents

- [Tech Spec: Epic 9 Observability](../sprint-artifacts/tech-spec-epic-9-observability.md)
- [Epic 9: Observability](../epics/epic-9-observability.md)
- [PRD: Observability Requirements](../prd.md#observability)

---

## Chat Message Content Logging

As of 2025-12-16, chat message content is fully logged for the Chat History viewer functionality:

- **User messages**: Full content of user queries is persisted to `observability.chat_messages`
- **Assistant messages**: Complete response text is logged, including streamed responses (buffered during streaming)
- **Error traces**: Only contain error type information, not message content (for security)

This enables the Chat History viewer to display complete conversation threads for admin review, compliance, and troubleshooting.

---

_Document Author: Architecture Team_
_Last Updated: 2025-12-16_
