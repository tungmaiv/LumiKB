# Technology Stack

← Back to [Architecture Index](index.md) | **Previous**: [01 - System Overview](01-system-overview.md)

---

## Project Initialization

First implementation story should initialize the project structure.

### Starter Template Versions (Verified 2025-11-23)

| Tool | Version | Verify Command |
|------|---------|----------------|
| create-next-app | 15.x (matches Next.js) | `npm view create-next-app version` |
| shadcn CLI | Latest (use @latest) | `npm view shadcn version` |
| Next.js | 15.x | `npm view next version` |

> **Note:** `create-next-app` version always matches Next.js version. The CLI extracts from the canary branch, so pinning CLI version doesn't pin Next.js version. Use `@latest` and verify Next.js version in generated package.json.

**Frontend:**
```bash
npx create-next-app@latest lumikb --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd lumikb
# Verify Next.js version after generation
cat package.json | grep '"next"'
npx shadcn@latest init
npm install zustand  # State management
# Note: Use tw-animate-css instead of deprecated tailwindcss-animate
```

**Backend:**
```bash
mkdir backend && cd backend
python3.11 -m venv .venv  # Requires Python 3.11 for redis-py compatibility
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg pydantic-settings
```

---

## Decision Summary

| Category | Decision | Version | Affects | Rationale |
|----------|----------|---------|---------|-----------|
| Backend Framework | Python + FastAPI | Python 3.11, FastAPI ≥0.115.0 | All backend | LangChain native ecosystem, best for RAG workloads |
| Database | PostgreSQL + SQLAlchemy 2.0 + asyncpg | PostgreSQL 16, SQLAlchemy 2.0.44, asyncpg 0.30.0 | All data | ACID guarantees, async support, audit logging |
| Vector Database | Qdrant + langchain-qdrant + gRPC | Qdrant ≥1.10.0, langchain-qdrant ≥1.1.0 | Search, RAG | Self-hosted, 3ms latency, hybrid search ready |
| LLM Integration | LiteLLM Proxy Server | LiteLLM ≥1.50.0 | Generation | Provider flexibility, fallback, cost tracking |
| Authentication | FastAPI-Users + argon2 + JWT | FastAPI-Users ≥14.0.0 | Security | Battle-tested, SQLAlchemy compatible, extensible |
| API Pattern | REST + OpenAPI + SSE | OpenAPI 3.1 | Client-server | Auto-generated docs, typed client generation |
| Document Processing | unstructured + LangChain splitters | unstructured ≥0.16.0, LangChain ≥0.3.0 | Ingestion | Best Python parsers, semantic chunking |
| Object Storage | MinIO | Latest | Files | S3-compatible, self-hosted, proven |
| Background Jobs | Celery + Redis | Celery 5.5.x, redis-py ≥7.1.0 | Async tasks | Industry standard, reliable |
| Caching | Redis | Redis ≥7.0.0 | Performance | Shared with Celery, session cache |
| Cross-Service Sync | Transactional Outbox | Custom | Data integrity | Eventual consistency with guarantees |
| Audit Logging | PostgreSQL audit schema | N/A | Compliance | INSERT-only, queryable, immutable |
| Graph Database | Neo4j | 5.x | GraphRAG | Entity-relationship storage, traversal queries |
| Entity Extraction | LLM-based NER | Custom | GraphRAG | Domain-aware entity/relationship extraction |
| Frontend Framework | Next.js 15 (App Router) | Next.js 15.x, React 19.x | UI | SSR, TypeScript, modern React |
| UI Components | shadcn/ui + Radix UI + Tailwind | Tailwind 4.x, tw-animate-css | UI | Accessible, customizable, Notion-like |
| State Management | Zustand | ≥5.0.0 | Frontend | Minimal boilerplate, TypeScript-first, no providers |
| Monitoring | structlog + Prometheus | structlog ≥25.5.0 | Operations | Structured logs, metrics endpoints |

---

## Technology Stack Details

### Core Technologies (Verified November 2025)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Runtime** | Python | 3.11 | Application runtime (required for redis-py ≥7.1.0) |
| **Web Framework** | FastAPI | ≥0.115.0 | REST API, SSE streaming |
| **ORM** | SQLAlchemy | 2.0.44 | Database access, migrations |
| **DB Driver** | asyncpg | 0.30.0 | Async PostgreSQL driver |
| **Validation** | Pydantic | ≥2.7.0, <3.0.0 | Request/response validation |
| **Settings** | pydantic-settings | ≥2.0.0 | Environment configuration |
| **Auth** | FastAPI-Users | ≥14.0.0 | User management, JWT |
| **Task Queue** | Celery | 5.5.x | Background job processing |
| **Frontend** | Next.js | 15.x | React framework, App Router |
| **React** | React | 19.x | UI library |
| **UI Components** | shadcn/ui | Latest | Radix-based components |
| **Styling** | Tailwind CSS | 4.x | Utility-first CSS |
| **CSS Animations** | tw-animate-css | Latest | Animation utilities |
| **State Management** | Zustand | ≥5.0.0 | Client-side state |
| **Date Utilities** | date-fns | ≥4.0.0 | Date formatting, parsing |

### Data Stores

| Store | Technology | Version | Purpose | Configuration |
|-------|------------|---------|---------|---------------|
| **Relational** | PostgreSQL | 16 | Metadata, users, audit | Primary data store |
| **Vector** | Qdrant | ≥1.10.0 | Embeddings, search | Collection per KB, gRPC |
| **Object** | MinIO | Latest | Document files | S3-compatible buckets |
| **Cache** | Redis | ≥7.0.0 | Sessions, queue, cache | Shared instance |
| **Graph** | Neo4j | 5.x | Entities, relationships | Optional, GraphRAG feature |

### Integration Points

| Integration | Technology | Version | Protocol | Purpose |
|-------------|------------|---------|----------|---------|
| **LLM Gateway** | LiteLLM Proxy | Latest | HTTP (OpenAI-compatible) | Model abstraction, fallback |
| **Vector Integration** | langchain-qdrant | ≥1.1.0 | gRPC/HTTP | Qdrant vector store |
| **Embeddings** | LiteLLM / local | Latest | HTTP | Text vectorization |
| **Document Parsing** | unstructured | Latest | Library | PDF, DOCX, MD extraction (default) |
| **Document Parsing (Optional)** | docling | Latest | Library | Advanced PDF/DOCX parsing with better tables (feature-flagged) |
| **Text Splitting** | LangChain | ≥0.3.0 | Library | Semantic chunking |
| **Logging** | structlog | ≥25.5.0 | Library | Structured JSON logging |
| **Graph Database** | neo4j (Python driver) | ≥5.0.0 | Bolt | Entity/relationship storage |
| **NER Provider** | LLM-based / spaCy | Latest | Library/HTTP | Named entity recognition |

---

## Version Pinning Strategy

```txt
# backend/requirements.txt - Pin major.minor, allow patch updates

# Core Framework
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.32.0,<1.0.0
pydantic>=2.7.0,<3.0.0
pydantic-settings>=2.0.0,<3.0.0

# Database
sqlalchemy[asyncio]>=2.0.44,<3.0.0
asyncpg>=0.30.0,<1.0.0
alembic>=1.14.0,<2.0.0

# Auth
fastapi-users[sqlalchemy]>=14.0.0,<15.0.0  # Note: NOT sqlalchemy2
argon2-cffi>=23.1.0,<24.0.0

# Vector & LLM
langchain>=0.3.0,<1.0.0
langchain-qdrant>=1.1.0,<2.0.0  # Use QdrantVectorStore, NOT deprecated Qdrant class
qdrant-client>=1.10.0,<2.0.0
litellm>=1.50.0,<2.0.0

# Task Queue
celery>=5.5.0,<6.0.0
redis>=7.1.0,<8.0.0  # Requires Python ≥3.10

# Document Processing
unstructured>=0.16.0,<1.0.0
# Optional: Advanced document parsing with better table extraction
# docling>=2.0.0,<3.0.0  # Enable with LUMIKB_PARSER_DOCLING_ENABLED=true

# Logging & Monitoring
structlog>=25.5.0,<26.0.0
prometheus-client>=0.21.0,<1.0.0
```

---

## Deprecated Components to Avoid

| Deprecated | Use Instead | Notes |
|------------|-------------|-------|
| `langchain_community.vectorstores.qdrant.Qdrant` | `langchain_qdrant.QdrantVectorStore` | Old class deprecated |
| `tailwindcss-animate` | `tw-animate-css` | Package renamed |
| `pydantic.BaseSettings` | `pydantic_settings.BaseSettings` | Moved to separate package |
| `fastapi-users[sqlalchemy2]` | `fastapi-users[sqlalchemy]` | Extra renamed |
| Python 3.10 | Python 3.11 | redis-py 7.1.0 requires ≥3.10, recommend 3.11 |

---

## Breaking Changes & Migration Notes

This section documents known breaking changes between major versions of key dependencies.

### LangChain 0.2 → 0.3 → 1.0

| Version | Breaking Change | Migration |
|---------|-----------------|-----------|
| 0.3.0 | Python 3.8 dropped | Use Python 3.11 (already required) |
| 0.3.0 | `openai_functions_agent` removed | Use `create_react_agent` or LangGraph |
| 0.3.0 | `chains.openai_tools.extraction` removed | Use `with_structured_output()` on chat models |
| 1.0.0 | Python 3.9 dropped | Use Python 3.11 (already required) |
| 1.0.0 | `langgraph.prebuilt.create_react_agent` moved | Use `langchain.agents.create_agent` |
| 1.0.0 | `prompt` parameter renamed | Use `system_prompt` |
| 1.0.0 | `message.text()` method → property | Use `message.text` (no parentheses) |
| 1.0.0 | `AIMessage.example` removed | Use `additional_kwargs` for metadata |
| 1.0.0 | Pydantic state schemas removed | Use `TypedDict` for agent state |

**Migration tool:** `pip install langchain-cli && langchain-cli migrate` (run twice for complete migration)

### FastAPI-Users 13 → 14

| Change | Migration |
|--------|-----------|
| `[sqlalchemy2]` extra renamed | Use `[sqlalchemy]` |
| Pydantic v2 required | Already using Pydantic v2 |

### Pydantic 1 → 2

| Change | Migration |
|--------|-----------|
| `BaseSettings` moved | Import from `pydantic_settings` |
| `validator` → `field_validator` | Use `@field_validator` decorator |
| `Config` class deprecated | Use `model_config = ConfigDict(...)` |
| `.dict()` → `.model_dump()` | Use new method name |
| `.json()` → `.model_dump_json()` | Use new method name |

### Redis-py 4 → 5 → 7

| Version | Change | Migration |
|---------|--------|-----------|
| 5.0 | Async API restructured | Use `redis.asyncio` module |
| 7.0 | Python 3.7-3.9 dropped | Use Python 3.11 (already required) |

### Next.js 14 → 15

| Change | Migration |
|--------|-----------|
| `next/image` changes | Review image optimization settings |
| Turbopack default for dev | Already using Turbopack |
| React 19 support | Already using React 19 |

---

**Previous**: [01 - System Overview](01-system-overview.md) | **Next**: [03 - LLM Configuration](03-llm-configuration.md) | **Index**: [Architecture](index.md)
