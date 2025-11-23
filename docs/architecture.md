# LumiKB Architecture

## Executive Summary

LumiKB is an enterprise RAG-powered knowledge management platform built on a **citation-first architecture** that ensures every AI-generated statement traces back to source documents. The architecture prioritizes trust through verifiability, on-premises deployment capability, and cross-service data consistency.

The system follows a modular monolith approach with clear service boundaries, enabling future decomposition into microservices if needed. All components are self-hosted and containerized, meeting Banking & Financial Services compliance requirements (SOC 2, GDPR, PCI-DSS awareness, ISO 27001).

**Core Architectural Principles:**
1. **Trust through verifiability** - Citation assembly is THE core differentiator
2. **On-premises first** - All components self-hosted, air-gap capable
3. **Eventual consistency with guarantees** - Transactional outbox pattern for cross-service operations
4. **Boring technology that works** - Proven, stable choices over cutting-edge experiments

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
| Frontend Framework | Next.js 15 (App Router) | Next.js 15.x, React 19.x | UI | SSR, TypeScript, modern React |
| UI Components | shadcn/ui + Radix UI + Tailwind | Tailwind 4.x, tw-animate-css | UI | Accessible, customizable, Notion-like |
| State Management | Zustand | ≥5.0.0 | Frontend | Minimal boilerplate, TypeScript-first, no providers |
| Monitoring | structlog + Prometheus | structlog ≥25.5.0 | Operations | Structured logs, metrics endpoints |

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
│  ┌─────────────────┐                                                    │
│  │   Next.js App   │ ◄─── Browser (Desktop/Tablet)                      │
│  │   (Frontend)    │                                                    │
│  └────────┬────────┘                                                    │
└───────────┼─────────────────────────────────────────────────────────────┘
            │ HTTPS (REST + SSE)
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │  Auth   │ │   KB    │ │  Docs   │ │ Search  │ │ Generate│   │   │
│  │  │ Router  │ │ Router  │ │ Router  │ │ Router  │ │ Router  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────┬──────────────┬──────────────┬──────────────┬───────────────┘
            │              │              │              │
            ▼              ▼              ▼              ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │    Auth      │  │  Knowledge   │  │   Document   │                 │
│  │   Service    │  │  Base Svc    │  │   Service    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Search     │  │  Generation  │  │   Citation   │ ◄── THE CORE    │
│  │   Service    │  │   Service    │  │   Service    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└──────┬─────────────────┬─────────────────┬─────────────────┬──────────┘
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                       DATA & INFRASTRUCTURE                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  PostgreSQL  │  │    Qdrant    │  │    MinIO     │  │   Redis   │ │
│  │  (Metadata)  │  │  (Vectors)   │  │  (Files)     │  │  (Cache)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐                                   │
│  │   LiteLLM    │  │    Celery    │                                   │
│  │   (LLM GW)   │  │  (Workers)   │                                   │
│  └──────────────┘  └──────────────┘                                   │
└───────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
lumikb/
├── frontend/                      # Next.js application
│   ├── src/
│   │   ├── app/                   # App Router pages
│   │   │   ├── (auth)/            # Auth pages (login, register, reset)
│   │   │   ├── (dashboard)/       # Main app pages
│   │   │   │   ├── chat/          # Chat interface
│   │   │   │   ├── kb/            # Knowledge base management
│   │   │   │   ├── search/        # Search results
│   │   │   │   └── admin/         # Admin pages
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/                # shadcn/ui components
│   │   │   ├── chat/              # Chat-specific components
│   │   │   ├── citations/         # Citation components (THE CORE)
│   │   │   ├── kb/                # KB management components
│   │   │   └── layout/            # Layout components
│   │   ├── lib/
│   │   │   ├── api/               # Generated API client
│   │   │   ├── hooks/             # Custom React hooks
│   │   │   └── utils/             # Utility functions
│   │   └── types/                 # TypeScript types
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── package.json
│
├── backend/                       # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py        # Auth endpoints
│   │   │   │   ├── users.py       # User management
│   │   │   │   ├── knowledge_bases.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── search.py
│   │   │   │   ├── chat.py        # SSE streaming
│   │   │   │   ├── generate.py    # SSE streaming
│   │   │   │   └── admin.py
│   │   │   └── deps.py            # Dependency injection
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── security.py        # JWT, password hashing
│   │   │   └── exceptions.py      # Custom exceptions
│   │   ├── models/                # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── document.py
│   │   │   └── audit.py
│   │   ├── schemas/               # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── knowledge_base.py
│   │   │   ├── document.py
│   │   │   ├── search.py
│   │   │   └── generation.py
│   │   ├── services/              # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── kb_service.py
│   │   │   ├── document_service.py
│   │   │   ├── search_service.py
│   │   │   ├── generation_service.py
│   │   │   ├── citation_service.py   # THE CORE DIFFERENTIATOR
│   │   │   └── audit_service.py
│   │   ├── repositories/          # Data access layer
│   │   │   ├── user_repo.py
│   │   │   ├── kb_repo.py
│   │   │   ├── document_repo.py
│   │   │   └── vector_repo.py     # Qdrant operations
│   │   ├── workers/               # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── document_tasks.py  # Parse, chunk, embed
│   │   │   ├── sync_tasks.py      # Cross-service consistency
│   │   │   └── cleanup_tasks.py   # Orphan detection, archival
│   │   ├── integrations/          # External service clients
│   │   │   ├── llm_client.py      # LiteLLM client
│   │   │   ├── qdrant_client.py   # Vector DB client
│   │   │   └── minio_client.py    # Object storage client
│   │   └── main.py                # FastAPI app entry
│   ├── alembic/                   # Database migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── pyproject.toml
│   └── Dockerfile
│
├── infrastructure/                # Deployment configs
│   ├── docker/
│   │   ├── docker-compose.yml     # Local development
│   │   ├── docker-compose.prod.yml
│   │   └── Dockerfile.frontend
│   ├── k8s/                       # Kubernetes manifests (future)
│   └── scripts/
│       ├── init-db.sh
│       └── seed-data.sh
│
├── docs/                          # Project documentation
├── .env.example
├── README.md
└── Makefile                       # Common commands
```

## FR Category to Architecture Mapping

| FR Category | Backend Module | Frontend Component | Data Store |
|-------------|----------------|-------------------|------------|
| User Account & Access (FR1-8) | `api/auth.py`, `services/auth_service.py` | `(auth)/*` pages | PostgreSQL |
| KB Management (FR9-14) | `api/knowledge_bases.py`, `services/kb_service.py` | `kb/*` components | PostgreSQL + Qdrant |
| Document Ingestion (FR15-23) | `api/documents.py`, `workers/document_tasks.py` | `kb/upload` | MinIO + Qdrant |
| Semantic Search (FR24-30) | `api/search.py`, `services/search_service.py` | `search/*`, `chat/*` | Qdrant |
| Chat Interface (FR31-35) | `api/chat.py`, `services/generation_service.py` | `chat/*` components | Redis |
| Document Generation (FR36-42) | `api/generate.py`, `services/generation_service.py` | `chat/generate` | LiteLLM |
| Citation & Provenance (FR43-46) | `services/citation_service.py` | `citations/*` | PostgreSQL + Qdrant |
| Administration (FR47-52) | `api/admin.py` | `admin/*` pages | PostgreSQL |
| Audit & Compliance (FR53-58) | `services/audit_service.py` | `admin/audit` | PostgreSQL (audit schema) |

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

### Integration Points

| Integration | Technology | Version | Protocol | Purpose |
|-------------|------------|---------|----------|---------|
| **LLM Gateway** | LiteLLM Proxy | Latest | HTTP (OpenAI-compatible) | Model abstraction, fallback |
| **Vector Integration** | langchain-qdrant | ≥1.1.0 | gRPC/HTTP | Qdrant vector store |
| **Embeddings** | LiteLLM / local | Latest | HTTP | Text vectorization |
| **Document Parsing** | unstructured | Latest | Library | PDF, DOCX, MD extraction |
| **Text Splitting** | LangChain | ≥0.3.0 | Library | Semantic chunking |
| **Logging** | structlog | ≥25.5.0 | Library | Structured JSON logging |

### Version Pinning Strategy

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

# Logging & Monitoring
structlog>=25.5.0,<26.0.0
prometheus-client>=0.21.0,<1.0.0
```

### Deprecated Components to Avoid

| Deprecated | Use Instead | Notes |
|------------|-------------|-------|
| `langchain_community.vectorstores.qdrant.Qdrant` | `langchain_qdrant.QdrantVectorStore` | Old class deprecated |
| `tailwindcss-animate` | `tw-animate-css` | Package renamed |
| `pydantic.BaseSettings` | `pydantic_settings.BaseSettings` | Moved to separate package |
| `fastapi-users[sqlalchemy2]` | `fastapi-users[sqlalchemy]` | Extra renamed |
| Python 3.10 | Python 3.11 | redis-py 7.1.0 requires ≥3.10, recommend 3.11 |

### Breaking Changes & Migration Notes

This section documents known breaking changes between major versions of key dependencies.

#### LangChain 0.2 → 0.3 → 1.0

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

#### FastAPI-Users 13 → 14

| Change | Migration |
|--------|-----------|
| `[sqlalchemy2]` extra renamed | Use `[sqlalchemy]` |
| Pydantic v2 required | Already using Pydantic v2 |

#### Pydantic 1 → 2

| Change | Migration |
|--------|-----------|
| `BaseSettings` moved | Import from `pydantic_settings` |
| `validator` → `field_validator` | Use `@field_validator` decorator |
| `Config` class deprecated | Use `model_config = ConfigDict(...)` |
| `.dict()` → `.model_dump()` | Use new method name |
| `.json()` → `.model_dump_json()` | Use new method name |

#### Redis-py 4 → 5 → 7

| Version | Change | Migration |
|---------|--------|-----------|
| 5.0 | Async API restructured | Use `redis.asyncio` module |
| 7.0 | Python 3.7-3.9 dropped | Use Python 3.11 (already required) |

#### Next.js 14 → 15

| Change | Migration |
|--------|-----------|
| `next/image` changes | Review image optimization settings |
| Turbopack default for dev | Already using Turbopack |
| React 19 support | Already using React 19 |

## Novel Pattern Designs

### Pattern 1: Citation Assembly System

The citation system is LumiKB's core differentiator. Every AI-generated statement must trace back to source documents with passage-level precision.

#### Architecture

```
RETRIEVAL PHASE
  Query → Qdrant → Chunks with rich metadata
                        │
                        ▼
  ┌─────────────────────────────────────────┐
  │  Chunk Metadata (stored at index time)  │
  │  - document_id, document_name           │
  │  - page_number, section_header          │
  │  - char_start, char_end, chunk_text     │
  └─────────────────────────────────────────┘

GENERATION PHASE
  System prompt instructs LLM to cite using [1], [2], etc.
  LLM Response: "Authentication uses OAuth 2.0 [1] with MFA [2]..."

CITATION EXTRACTION
  Parse output → Extract [n] markers → Map to source chunks
                        │
                        ▼
  ┌─────────────────────────────────────────┐
  │  Citation Object                        │
  │  {                                      │
  │    "number": 1,                         │
  │    "document_id": "doc-xyz",            │
  │    "document_name": "Acme Proposal.pdf",│
  │    "page": 14,                          │
  │    "section": "Authentication",         │
  │    "excerpt": "OAuth 2.0 with PKCE...", │
  │    "confidence": 0.92                   │
  │  }                                      │
  └─────────────────────────────────────────┘

STREAMING SUPPORT
  SSE Events:
    { "type": "token", "content": "OAuth 2.0 " }
    { "type": "token", "content": "[1]" }
    { "type": "citation", "data": { "number": 1, ... }}
```

#### Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| CitationService | `services/citation_service.py` | Core citation logic |
| ChunkMetadata | Qdrant payload | Rich metadata at index time |
| CitationExtractor | `services/citation_service.py` | Parse [n] from LLM output |
| CitationCard | `components/citations/` | UI display |

### Pattern 2: Transactional Outbox (Cross-Service Consistency)

Document operations touch PostgreSQL, MinIO, and Qdrant. The outbox pattern ensures eventual consistency with failure recovery.

#### Document Status State Machine

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  DOCUMENT LIFECYCLE                  │
                    └─────────────────────────────────────────────────────┘

     ┌──────────┐      upload       ┌──────────┐     worker picks up    ┌────────────┐
     │          │ ─────────────────>│          │ ─────────────────────> │            │
     │  (none)  │                   │ PENDING  │                        │ PROCESSING │
     │          │                   │          │                        │            │
     └──────────┘                   └──────────┘                        └─────┬──────┘
                                                                              │
                                    ┌─────────────────────────────────────────┤
                                    │                                         │
                                    ▼ all steps complete                      ▼ step fails
                              ┌──────────┐                              ┌──────────┐
                              │          │                              │          │
                              │  READY   │                              │  FAILED  │
                              │          │                              │          │
                              └──────────┘                              └────┬─────┘
                                    │                                        │
                                    │ user deletes                           │ retry (manual/auto)
                                    ▼                                        ▼
                              ┌──────────┐                              ┌────────────┐
                              │          │                              │            │
                              │ ARCHIVED │                              │ PROCESSING │
                              │          │                              │  (retry)   │
                              └──────────┘                              └────────────┘

Status Values:
- PENDING:    Document uploaded, waiting for processing
- PROCESSING: Celery worker actively processing (parsing, chunking, embedding)
- READY:      All processing complete, document is searchable
- FAILED:     Processing failed after max retries (check last_error)
- ARCHIVED:   Soft-deleted, retained for audit trail
```

#### Flow

```
1. API REQUEST (synchronous)
   BEGIN TRANSACTION
     INSERT INTO documents (id, name, status='pending')
     INSERT INTO outbox (event_type='doc.created', payload)
   COMMIT
   Return 202 Accepted

2. CELERY WORKER (asynchronous)
   Poll outbox → For each event:
     UPDATE documents SET status='processing'
     Step A: Upload file to MinIO
     Step B: Parse document (unstructured)
     Step C: Chunk document (LangChain)
     Step D: Generate embeddings
     Step E: Store vectors in Qdrant
   All complete: UPDATE documents SET status='ready'
   On failure: UPDATE documents SET status='failed', last_error=...

3. RECONCILIATION JOB (hourly)
   Detect: docs without vectors, orphaned files
   Actions: re-queue, cleanup, alert
```

#### Outbox Schema

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    attempts INT DEFAULT 0,
    last_error TEXT
);
CREATE INDEX idx_outbox_unprocessed ON outbox (created_at)
    WHERE processed_at IS NULL;
```

## Implementation Patterns

### Design Principles: KISS, DRY, YAGNI

All implementation patterns follow these core principles:

| Principle | Meaning | Application |
|-----------|---------|-------------|
| **KISS** | Keep It Simple, Stupid | Prefer simple solutions over clever ones. If a pattern requires explanation, simplify it. |
| **DRY** | Don't Repeat Yourself | Extract common code AFTER you see it repeated 3+ times, not before. |
| **YAGNI** | You Aren't Gonna Need It | Don't build features or abstractions until there's a concrete need. |

**When to abstract:** Only when you have 3+ concrete examples of repetition. Premature abstraction is worse than duplication.

### Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| Database Tables | snake_case, plural | `users`, `knowledge_bases` |
| Database Columns | snake_case | `user_id`, `created_at` |
| API Endpoints | kebab-case, plural | `/api/v1/knowledge-bases` |
| Python Files | snake_case | `auth_service.py` |
| Python Classes | PascalCase | `KnowledgeBase` |
| TypeScript Files | kebab-case | `knowledge-base.tsx` |
| React Components | PascalCase | `CitationCard` |
| Environment Vars | SCREAMING_SNAKE | `DATABASE_URL` |

### Date/Time Formatting

All date/time values use consistent formats across the application:

| Context | Format | Example | Library |
|---------|--------|---------|---------|
| API responses | ISO 8601 UTC | `2025-11-23T10:30:00Z` | Native Python `datetime.isoformat()` |
| Database storage | TIMESTAMPTZ | `2025-11-23 10:30:00+00` | PostgreSQL native |
| UI display (full) | Locale-aware | `Nov 23, 2025, 10:30 AM` | `date-fns` with `format()` |
| UI display (relative) | Relative | `2 hours ago` | `date-fns` with `formatDistanceToNow()` |
| File exports | ISO 8601 | `2025-11-23T10:30:00Z` | Native |

```typescript
// frontend/src/lib/utils/date.ts
import { format, formatDistanceToNow } from 'date-fns';

export const formatDate = (date: string | Date) =>
  format(new Date(date), 'MMM d, yyyy, h:mm a');

export const formatRelative = (date: string | Date) =>
  formatDistanceToNow(new Date(date), { addSuffix: true });

// Usage in components
<span>{formatDate(document.createdAt)}</span>      // "Nov 23, 2025, 10:30 AM"
<span>{formatRelative(document.updatedAt)}</span>  // "2 hours ago"
```

```python
# backend/app/schemas/base.py
from datetime import datetime, timezone

class TimestampMixin:
    """All timestamps returned as ISO 8601 UTC"""
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat()
        }
```

### Code Organization

| Layer | Purpose | Pattern |
|-------|---------|---------|
| `api/` | HTTP routing | Thin controllers, delegate to services |
| `services/` | Business logic | Orchestration, validation, domain rules |
| `repositories/` | Data access | Database queries, external data sources |
| `models/` | Data structures | SQLAlchemy ORM models |
| `schemas/` | API contracts | Pydantic request/response models |
| `workers/` | Async tasks | Celery task definitions |

### Error Handling

```python
# Standardized error response
{
    "error": {
        "code": "DOCUMENT_NOT_FOUND",
        "message": "Document with ID xyz not found",
        "details": {"document_id": "xyz"},
        "request_id": "req-abc-123"
    }
}

# HTTP Status Codes
400 - Validation errors
401 - Authentication required
403 - Permission denied
404 - Resource not found
409 - Conflict
422 - Business logic error
500 - Internal server error
503 - Service unavailable
```

### Logging Strategy

```python
# Structured JSON logs
{
    "timestamp": "2025-11-22T10:30:00Z",
    "level": "INFO",
    "message": "Document processed",
    "request_id": "req-abc-123",
    "user_id": "user-xyz",
    "document_id": "doc-789",
    "duration_ms": 1250
}
```

### Common Patterns (KISS/DRY/YAGNI)

#### 1. Centralized Exception Handling (DRY)

All errors flow through a single exception handler. Services raise exceptions, middleware formats responses.

```python
# backend/app/core/exceptions.py
class AppException(Exception):
    """Base exception - all custom exceptions inherit from this"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with ID {resource_id} not found",
            status_code=404,
            details={"resource": resource, "id": resource_id}
        )

class PermissionDeniedError(AppException):
    def __init__(self, action: str, resource: str):
        super().__init__(
            code="PERMISSION_DENIED",
            message=f"You don't have permission to {action} this {resource}",
            status_code=403
        )

# backend/app/main.py - Single handler for ALL app errors
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request.state.request_id
            }
        }
    )

# In services - just raise, never handle (KISS)
class KBService:
    async def get(self, kb_id: str) -> KnowledgeBase:
        kb = await self.repo.get(kb_id)
        if not kb:
            raise NotFoundError("knowledge_base", kb_id)
        return kb
```

#### 2. Request-Scoped Logging Context (DRY)

Set logging context once in middleware, available everywhere automatically.

```python
# backend/app/core/logging.py
import structlog
from contextvars import ContextVar

request_context: ContextVar[dict] = ContextVar("request_context", default={})

def get_logger():
    """Get logger with current request context automatically included"""
    return structlog.get_logger().bind(**request_context.get())

# backend/app/middleware/logging.py
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request_context.set({
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
    })

    logger = get_logger()
    start = time.time()
    logger.info("request_started")

    response = await call_next(request)

    logger.info("request_completed",
                status_code=response.status_code,
                duration_ms=int((time.time() - start) * 1000))
    return response

# In services - context is automatic (KISS)
class DocumentService:
    async def process(self, doc_id: str):
        logger = get_logger()  # Already has request_id, user_id
        logger.info("processing_document", document_id=doc_id)
```

#### 3. Pydantic-Only Validation (DRY)

Validation happens ONCE in Pydantic schemas. Services trust validated input.

```python
# backend/app/schemas/document.py
class DocumentCreate(BaseModel):
    """Validation defined HERE, once"""
    name: str = Field(..., min_length=1, max_length=255)
    kb_id: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Document name cannot be empty")
        return v.strip()

# In API route - Pydantic validates automatically
@router.post("/")
async def upload_document(data: DocumentCreate):  # Validated!
    return await service.create(data)

# In service - NO re-validation (YAGNI)
class DocumentService:
    async def create(self, data: DocumentCreate):
        # data is ALREADY validated, just use it
        doc = Document(name=data.name, kb_id=data.kb_id)
```

#### 4. Generic Repository Base (DRY)

Standard CRUD operations in base class. Only override for unique queries.

```python
# backend/app/repositories/base.py
class BaseRepository(Generic[ModelType]):
    """Generic CRUD - add specific methods only when needed (YAGNI)"""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, id: str) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def list(self, skip: int = 0, limit: int = 20) -> list[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

# Specific repository - ONLY unique methods
class DocumentRepository(BaseRepository[Document]):
    async def get_by_kb(self, kb_id: str) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        return result.scalars().all()
```

#### 5. Dependency Injection (KISS)

FastAPI's `Depends()` with simple factory functions.

```python
# backend/app/api/deps.py
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

def get_repository(repo_class):
    async def _get_repo(session: AsyncSession = Depends(get_db)):
        return repo_class(session)
    return _get_repo

def get_service(service_class, repo_class):
    async def _get_service(repo = Depends(get_repository(repo_class))):
        return service_class(repo)
    return _get_service

# Usage - one-liner (KISS)
@router.get("/{kb_id}")
async def get_kb(
    kb_id: str,
    service: KBService = Depends(get_service(KBService, KBRepository))
):
    return await service.get(kb_id)
```

#### Pattern Summary

| Pattern | Principle | Rule |
|---------|-----------|------|
| Exception Handling | DRY | Define exceptions once, handler formats all errors |
| Logging | DRY | Set context in middleware, `get_logger()` everywhere |
| Validation | DRY + YAGNI | Pydantic validates, services trust input |
| Repository | DRY + YAGNI | Generic base, add methods only when needed |
| Dependency Injection | KISS | Simple factory functions, one-liner usage |

### Testing Conventions

#### Test File Organization

| Stack | Test Location | Naming Pattern | Example |
|-------|---------------|----------------|---------|
| Backend unit | `backend/tests/unit/` | `test_{module}.py` | `test_citation_service.py` |
| Backend integration | `backend/tests/integration/` | `test_{feature}_integration.py` | `test_document_upload_integration.py` |
| Frontend unit | `frontend/__tests__/` | `{component}.test.tsx` | `CitationCard.test.tsx` |
| Frontend E2E | `frontend/e2e/` | `{feature}.spec.ts` | `document-upload.spec.ts` |

#### Backend Testing (pytest)

```python
# backend/tests/conftest.py - Shared fixtures
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.core.config import settings

@pytest.fixture
async def db_session():
    """Fresh database session for each test"""
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Test client with database override"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_qdrant(mocker):
    """Mock Qdrant client for unit tests"""
    return mocker.patch("app.integrations.qdrant_client.QdrantClient")

# backend/tests/unit/test_citation_service.py - Unit test example
import pytest
from app.services.citation_service import CitationService

class TestCitationService:
    async def test_extract_citations_from_text(self):
        """Test citation marker extraction"""
        service = CitationService()
        text = "OAuth 2.0 [1] with MFA [2] is required."

        citations = service.extract_markers(text)

        assert len(citations) == 2
        assert citations[0].number == 1
        assert citations[1].number == 2

    async def test_no_citations_returns_empty(self):
        """Test handling of text without citations"""
        service = CitationService()
        result = service.extract_markers("No citations here")
        assert result == []
```

#### Frontend Testing (Jest + React Testing Library)

```typescript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testMatch: ['**/__tests__/**/*.test.{ts,tsx}'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};

// frontend/jest.setup.ts
import '@testing-library/jest-dom';

// frontend/__tests__/components/CitationCard.test.tsx
import { render, screen } from '@testing-library/react';
import { CitationCard } from '@/components/citations/CitationCard';

describe('CitationCard', () => {
  const mockCitation = {
    number: 1,
    documentName: 'Security Policy.pdf',
    page: 14,
    excerpt: 'OAuth 2.0 with PKCE flow...',
  };

  it('renders citation number and document name', () => {
    render(<CitationCard citation={mockCitation} />);

    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('Security Policy.pdf')).toBeInTheDocument();
  });

  it('shows page number when provided', () => {
    render(<CitationCard citation={mockCitation} />);

    expect(screen.getByText('Page 14')).toBeInTheDocument();
  });
});
```

#### Mocking Strategy

| What to Mock | When | How |
|--------------|------|-----|
| External APIs (LiteLLM, Qdrant) | Unit tests | `pytest-mock` / `jest.mock()` |
| Database | Unit tests only | In-memory SQLite or mocks |
| Database | Integration tests | Test PostgreSQL instance |
| File system (MinIO) | Unit tests | Mock boto3/minio client |
| Time/dates | When testing time-sensitive logic | `freezegun` / `jest.useFakeTimers()` |

#### Test Commands

```bash
# Backend
cd backend
pytest                           # Run all tests
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests only
pytest -k "citation"            # Tests matching pattern
pytest --cov=app --cov-report=html  # With coverage

# Frontend
cd frontend
npm test                        # Run all tests
npm test -- --watch            # Watch mode
npm test -- --coverage         # With coverage
npm run test:e2e               # E2E tests (Playwright)
```

## Data Architecture

### Core Entities

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    User     │────<│ KBPermission    │>────│KnowledgeBase│
└─────────────┘     └─────────────────┘     └──────┬──────┘
                                                   │
                                                   │ 1:N
                                                   ▼
                                            ┌─────────────┐
                                            │  Document   │
                                            └──────┬──────┘
                                                   │
                                                   │ 1:N (Qdrant)
                                                   ▼
                                            ┌─────────────┐
                                            │   Chunk     │
                                            │  (Vector)   │
                                            └─────────────┘
```

### PostgreSQL Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User accounts | id, email, hashed_password, is_active |
| `knowledge_bases` | KB metadata | id, name, description, owner_id, status |
| `kb_permissions` | Access control | user_id, kb_id, permission_level |
| `documents` | Document metadata | id, kb_id, name, file_path, status, chunk_count |
| `outbox` | Event queue | event_type, aggregate_id, payload, processed_at |
| `audit.events` | Audit trail | user_id, action, resource_type, resource_id, details |

### Qdrant Collections

- One collection per Knowledge Base: `kb_{kb_id}`
- Vector dimension: 1536 (OpenAI ada-002) or configurable
- Payload includes: document_id, document_name, page, section, char_start, char_end, text

## API Contracts

### Route Structure

```
/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   ├── POST /logout
│   └── POST /reset-password
├── /users
│   ├── GET /me
│   └── PATCH /me
├── /knowledge-bases
│   ├── GET /
│   ├── POST /
│   ├── GET /{kb_id}
│   ├── PATCH /{kb_id}
│   ├── DELETE /{kb_id}
│   └── GET /{kb_id}/stats
├── /documents
│   ├── GET /
│   ├── POST /
│   ├── GET /{doc_id}
│   ├── DELETE /{doc_id}
│   └── GET /{doc_id}/content
├── /search
│   ├── POST /
│   └── POST /quick
├── /chat
│   ├── POST /                    # SSE streaming
│   └── GET /history
├── /generate
│   └── POST /                    # SSE streaming
└── /admin
    ├── GET /audit-logs
    ├── GET /stats
    └── GET /health
```

### Response Format

```python
# Success
{
    "data": { ... },
    "meta": {
        "requestId": "req-abc",
        "timestamp": "2025-11-22T10:30:00Z"
    }
}

# Paginated
{
    "data": [ ... ],
    "meta": {
        "total": 150,
        "page": 1,
        "perPage": 20,
        "totalPages": 8
    }
}
```

## Security Architecture

### Authentication Flow

```
Frontend → POST /auth/login → FastAPI-Users → PostgreSQL
    ↓
JWT token (httpOnly cookie)
    ↓
Subsequent requests include cookie
    ↓
FastAPI middleware validates JWT on each request
```

### Authorization Model

| Role | Capabilities |
|------|--------------|
| **Admin** | All operations, audit logs, system config |
| **User** | Access assigned KBs only |

| KB Permission | Capabilities |
|---------------|--------------|
| **Read** | Search, view documents |
| **Write** | Upload, delete documents |
| **Admin** | Manage KB settings, permissions |

### Security Measures

| Measure | Implementation |
|---------|----------------|
| Password Hashing | argon2 (memory-hard) |
| Session Tokens | JWT with short expiry |
| CSRF Protection | SameSite cookies |
| Rate Limiting | Redis-based, per endpoint |
| Input Validation | Pydantic schemas |
| SQL Injection | SQLAlchemy parameterized queries |
| Encryption at Rest | PostgreSQL TDE, MinIO encryption |
| Encryption in Transit | TLS 1.3 everywhere |
| Audit Logging | Immutable append-only table |

### Audit Schema

```sql
CREATE SCHEMA audit;

CREATE TABLE audit.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET
);

-- INSERT-only permissions for application
CREATE ROLE audit_writer;
GRANT USAGE ON SCHEMA audit TO audit_writer;
GRANT INSERT ON audit.events TO audit_writer;

-- Indexes for common queries
CREATE INDEX idx_audit_user ON audit.events (user_id);
CREATE INDEX idx_audit_timestamp ON audit.events (timestamp);
CREATE INDEX idx_audit_resource ON audit.events (resource_type, resource_id);
```

**Retention Policy:**
- Archive to MinIO after 90 days
- Delete from database after 1 year

## Performance Considerations

### Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Search Response | < 3 seconds | Qdrant gRPC, Redis caching |
| Document Processing | < 2 minutes | Celery workers, parallel chunking |
| Chat Response | < 5 seconds | SSE streaming (first token fast) |
| Concurrent Users | 20+ | FastAPI async, connection pooling |

### Optimization Strategies

| Area | Strategy |
|------|----------|
| Vector Search | HNSW index, scalar quantization |
| Database | Connection pooling (asyncpg), query optimization |
| Caching | Redis for frequent queries, session data |
| File Uploads | Chunked uploads, background processing |
| LLM Calls | Streaming responses, request caching |

## Deployment Architecture

### Container Architecture

```yaml
# docker-compose.yml services
services:
  frontend:        # Next.js (port 3000)
  backend:         # FastAPI (port 8000)
  celery-worker:   # Celery workers
  celery-beat:     # Scheduled tasks
  postgres:        # PostgreSQL (port 5432)
  qdrant:          # Qdrant (port 6333/6334)
  minio:           # MinIO (port 9000/9001)
  redis:           # Redis (port 6379)
  litellm:         # LiteLLM Proxy (port 4000)
```

### Environment Configuration

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/lumikb

# Vector DB
QDRANT_HOST=qdrant
QDRANT_PORT=6334
QDRANT_GRPC=true

# Object Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...

# LLM
LITELLM_URL=http://litellm:4000
LITELLM_API_KEY=...

# Cache/Queue
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# Security
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
```

## Development Environment

### Prerequisites

- Python 3.11 (required - redis-py ≥7.1.0 needs Python ≥3.10)
- Node.js 20+ (LTS recommended)
- Docker & Docker Compose
- Git

### Setup Commands

```bash
# Clone and setup
git clone <repo>
cd lumikb

# Start infrastructure
docker compose up -d postgres qdrant minio redis litellm

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test
```

### Makefile Commands

```makefile
dev:           # Start all services for development
test:          # Run all tests
lint:          # Run linters
migrate:       # Run database migrations
seed:          # Seed sample data
docker-build:  # Build production images
```

## Architecture Decision Records (ADRs)

### ADR-001: Python Monolith over Go + Python Microservices

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

### ADR-002: Collection-per-KB for Qdrant

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

### ADR-003: Transactional Outbox over Distributed Transactions

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

### ADR-004: PostgreSQL Audit Table over File Logs

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

### ADR-005: Citation-First Architecture

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

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-22_
_Versions Verified: 2025-11-23_
_For: Tung Vu_
