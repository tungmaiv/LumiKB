# Architecture Decision Records (ADRs)

← Back to [Architecture Index](index.md) | **Previous**: [08 - Deployment](08-deployment.md)

---

## ADR-001: Python Monolith over Go + Python Microservices

**Decision:** Use Python + FastAPI monolith instead of Go API Gateway + Python RAG Workers

**Context:** Brainstorming session proposed Go (Gin/Fiber) for API Gateway with Python workers for RAG. After architectural review, we chose a unified Python approach.

**Alternatives Considered:**
1. **Go API Gateway + Python Workers + Redis** (from brainstorming) - Separates API concerns from RAG/ML
2. **Python + FastAPI monolith** (selected) - Single language, simpler deployment

**Rationale for Python Monolith:**
- **Ecosystem Unity**: LangChain, unstructured, embeddings - all Python-native. No Go bindings required.
- **Simpler Operations**: One language = one deployment pipeline, one set of expertise
- **FastAPI Performance**: Async Python with uvicorn handles API workloads well for MVP scale (20+ concurrent users)
- **KISS Principle**: Two languages + message queue adds complexity without proven need
- **Celery for Async**: Background processing via Celery workers achieves the same decoupling as Go + Redis

**When to Reconsider:**
- API latency becomes bottleneck at >100 concurrent users
- Team grows with dedicated Go expertise
- Need for CPU-intensive API processing (not I/O-bound)

**Consequences:**
- Two-language stack (Python backend, TypeScript frontend)
- Team needs Python expertise
- Future scaling may require revisiting Go gateway

**Supersedes:** Brainstorming decision A5 (Go API Gateway + Python Workers)

---

## ADR-002: Collection-per-KB for Qdrant

**Decision:** Create separate Qdrant collection for each Knowledge Base

**Context:** Need to ensure KB-level data isolation

**Rationale:**
- Strong isolation guarantees (no accidental cross-KB leakage)
- Independent scaling per collection
- Simpler permission enforcement
- Clean deletion (drop collection)

**Consequences:**
- More collections to manage
- Cross-KB search requires multi-collection query

---

## ADR-003: Transactional Outbox over Distributed Transactions

**Decision:** Use outbox pattern for cross-service consistency

**Context:** Document operations touch PostgreSQL, MinIO, and Qdrant

**Rationale:**
- Different database technologies can't share transactions
- Outbox provides eventual consistency with guarantees
- Failed operations can be retried
- Audit trail of all operations

**Consequences:**
- Eventual consistency (not immediate)
- Need reconciliation job for drift detection
- Slightly more complex error handling

---

## ADR-004: PostgreSQL Audit Table over File Logs

**Decision:** Store audit logs in PostgreSQL, not files

**Context:** Compliance requires queryable, immutable audit trail

**Rationale:**
- Admins need to query logs (FR48: filters by user, action, date)
- Same transaction as business operation ensures consistency
- INSERT-only permissions enforce immutability
- No additional log aggregation infrastructure

**Consequences:**
- Database storage for logs (mitigated by archival policy)
- Slightly more write load on PostgreSQL

---

## ADR-005: Citation-First Architecture

**Decision:** Build citation assembly as core architectural component, not afterthought

**Context:** Trust through verifiability is THE differentiator

**Rationale:**
- Citations are not optional - they're the product
- Passage-level precision requires rich chunk metadata
- Streaming citations need dedicated event types
- Verification flow needs confidence scoring

**Consequences:**
- More complex indexing (rich metadata per chunk)
- Dedicated CitationService with careful testing
- UI must prominently display citations

---

## ADR-006: LiteLLM Proxy for Model Abstraction (Epic 7)

**Decision:** Use LiteLLM Proxy as centralized LLM gateway with database-backed model registry and automatic DB-to-Proxy synchronization

**Context:** Need to support multiple LLM providers (Ollama, OpenAI, Gemini, Anthropic, Cohere) with per-KB model configuration and runtime switching. Administrators must be able to add/edit/test models via Admin UI without editing YAML configuration files.

**Alternatives Considered:**
1. **Direct provider SDKs** - Each provider called directly from services
2. **LangChain model abstraction** - Use LangChain's ChatModel interface
3. **LiteLLM Proxy with YAML config only** - Static configuration file
4. **LiteLLM Proxy with DB-to-Proxy Sync** (selected) - Database models auto-registered with proxy

**Rationale for LiteLLM Proxy + DB-to-Proxy Sync:**
- **Single API**: All providers accessed via OpenAI-compatible interface
- **Runtime flexibility**: Model routing without code changes or YAML edits
- **Zero YAML editing**: Admin UI creates models → automatic proxy registration
- **Connection testing**: DB models testable immediately after creation
- **Observability**: Built-in request logging, cost tracking
- **Fallbacks**: Automatic failover between providers
- **KB-level overrides**: Route requests to different models per KB
- **NER model type**: Natural extension for GraphRAG entity extraction

**Implementation (Option C: DB-to-Proxy Sync):**

The system uses LiteLLM's runtime model registration API (`/model/new`, `/model/delete`) to synchronize database models with the proxy:

```python
# backend/app/services/litellm_proxy_service.py
async def register_model_with_proxy(model: LLMModel, decrypted_api_key: str | None):
    """Register a DB model with LiteLLM proxy using db-{uuid} alias."""
    payload = {
        "model_name": f"db-{model.id}",  # Unique alias
        "litellm_params": {
            "model": f"{provider_prefix}/{model.model_id}",
            "api_base": resolve_api_base(model),  # Docker networking
            "api_key": decrypted_api_key,
        },
    }
    await httpx.post(f"{litellm_url}/model/new", json=payload)
```

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| `db-{uuid}` alias pattern | Prevents conflicts with YAML-defined models |
| `openai/` prefix for connection tests | Universal routing through LiteLLM proxy |
| `ollama_url_for_proxy` setting | Docker networking (host.docker.internal) |
| Clear-before-sync on startup | Prevents duplicate entries after proxy restart |
| `STORE_MODEL_IN_DB: "True"` | LiteLLM environment variable enabling runtime registration |

**Sync Lifecycle:**

1. **On Model Create/Update**: `register_model_with_proxy()` → POST `/model/new`
2. **On Model Delete**: `unregister_model_from_proxy()` → Lookup `model_info.id`, then POST `/model/delete`
3. **On Backend Startup**: `sync_all_models_to_proxy()` → Clear `db-*` models (using `model_info.id`), re-register all

**LiteLLM API Deletion Requirement:**

LiteLLM's `/model/delete` endpoint requires the internal `model_info.id` (a hash), **not** the `model_name` alias. The sync service handles this by:
- Looking up `model_info.id` from `/model/info` response before deletion
- Using `{"id": "<model_info_id>"}` in delete requests (not `{"model_name": "db-..."}`)

**Consequences:**
- Additional container to manage (LiteLLM proxy)
- ~~Configuration split between LiteLLM config and database~~ → **Resolved**: All DB models sync automatically
- Model names must match LiteLLM routing rules
- Proxy restart requires backend restart or manual sync (handled by startup sync)

**Implements:** FR78-FR83 (LLM Model Configuration)

---

## ADR-007: Neo4j for GraphRAG Entity Storage (Epic 8)

**Decision:** Use Neo4j Community Edition as optional graph database for entity-relationship storage

**Context:** GraphRAG requires storing entities and their relationships extracted from documents. Need traversal queries for graph-augmented retrieval.

**Alternatives Considered:**
1. **PostgreSQL with JSONB** - Store relationships as JSON, use recursive CTEs
2. **Apache AGE (PostgreSQL extension)** - Graph queries on PostgreSQL
3. **Neo4j Community Edition** (selected) - Purpose-built graph database
4. **Amazon Neptune** - Managed graph service (cloud-only)

**Rationale for Neo4j:**
- **Native graph model**: First-class support for nodes, relationships, properties
- **Cypher query language**: Expressive traversal queries with path patterns
- **Performance**: O(log n) relationship traversal vs O(n) for relational joins
- **APOC procedures**: Rich library for graph algorithms
- **Self-hosted**: Meets on-premises deployment requirement
- **Community Edition**: Free for single-instance deployment

**Consequences:**
- Additional infrastructure component (optional, only when GraphRAG enabled)
- Team needs Cypher query expertise
- Different consistency model than PostgreSQL
- Backup/restore procedures specific to Neo4j

**Implements:** FR84-FR98 (GraphRAG & Knowledge Graph)

---

## ADR-008: Retrieval Strategy Abstraction (Epic 8)

**Decision:** Implement retrieval as pluggable strategy pattern, enabling seamless switching between vector-only and graph-augmented retrieval

**Context:** GraphRAG is an optional feature. KBs without graph enabled should use existing vector search. KBs with graph enabled should use enhanced retrieval.

**Alternatives Considered:**
1. **Hardcoded conditionals** - `if graph_enabled: use_graphrag() else: use_vector()`
2. **Strategy pattern** (selected) - Abstract retrieval interface with swappable implementations
3. **Feature flags** - Runtime toggles in search service

**Rationale for Strategy Pattern:**
- **Clean separation**: Vector retrieval remains unchanged
- **Testability**: Each strategy tested independently
- **Extensibility**: Future strategies (hybrid, semantic graph, etc.)
- **Configuration-driven**: KB settings drive strategy selection
- **Graceful degradation**: Fall back to vector-only if Neo4j unavailable

**Implementation:**
```python
class RetrievalStrategy(Protocol):
    async def retrieve(self, query: str, kb_id: UUID, top_k: int) -> List[Chunk]

class VectorOnlyRetrieval(RetrievalStrategy):
    # Existing Qdrant-based retrieval

class GraphAugmentedRetrieval(RetrievalStrategy):
    # Vector search + Neo4j graph traversal + merge/re-rank
```

**Consequences:**
- Slight abstraction overhead
- Strategy selected at request time (minor latency)
- Requires careful testing of both paths

---

## ADR-009: LLM-based Entity Extraction with Domain Schemas (Epic 8)

**Decision:** Use LLM-based Named Entity Recognition with configurable domain schemas instead of fixed NER models

**Context:** Different knowledge bases contain different types of entities (legal: contracts, parties; IT: servers, applications). Need flexible entity extraction that adapts to domain.

**Alternatives Considered:**
1. **spaCy NER models** - Pre-trained models for standard entities (PERSON, ORG, LOC)
2. **Fine-tuned BERT/RoBERTa** - Custom NER models per domain
3. **LLM-based extraction** (selected) - Prompt-based extraction with domain schema
4. **Hybrid approach** - spaCy for speed, LLM for complex cases

**Rationale for LLM-based:**
- **Zero-shot**: No model training required for new domains
- **Domain flexibility**: Schema defines entity/relationship types
- **Relationship extraction**: LLMs can extract relationships, not just entities
- **Quality**: Better handling of context, coreference, implicit relationships
- **Confidence scores**: LLM can assess extraction confidence

**Trade-offs:**
- **Cost**: LLM calls more expensive than local NER
- **Latency**: ~1-2s per chunk vs <100ms for spaCy
- **Rate limiting**: Need batch processing for large documents

**Mitigation:**
- Batch extraction during document processing (not real-time)
- Celery rate limiting (10 calls/second default)
- Optional spaCy fallback for cost-sensitive deployments
- Dedicated reprocessing worker queue

**Implements:** FR90-FR93 (Entity Extraction Configuration)

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-22_
_Versions Verified: 2025-11-23_
_Updated: 2025-12-08 (Epic 7 & 8 ADRs added)_
_For: Tung Vu_
