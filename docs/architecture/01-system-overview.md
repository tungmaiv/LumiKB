# System Overview

← Back to [Architecture Index](index.md)

---

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
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Entity     │  │    Graph     │  │   GraphRAG   │ ◄── OPTIONAL    │
│  │  Extraction  │  │   Storage    │  │   Retrieval  │                 │
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
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   LiteLLM    │  │    Celery    │  │    Neo4j     │ ◄── OPTIONAL   │
│  │   (LLM GW)   │  │  (Workers)   │  │  (Graph DB)  │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└───────────────────────────────────────────────────────────────────────┘
```

---

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
│   │   │   ├── audit_service.py
│   │   │   ├── entity_extraction_service.py  # LLM-based NER
│   │   │   ├── graph_storage_service.py      # Neo4j operations
│   │   │   ├── graphrag_service.py           # Graph-augmented retrieval
│   │   │   ├── domain_service.py             # Domain schema management
│   │   │   └── schema_drift_service.py       # Schema version tracking
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
│   │   │   ├── minio_client.py    # Object storage client
│   │   │   └── neo4j_client.py    # Graph DB client (optional)
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

---

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
| LLM Model Configuration (FR78-83) | `api/admin.py`, `services/model_registry_service.py` | `admin/models/*` | PostgreSQL + LiteLLM |
| GraphRAG & Knowledge Graph (FR84-98) | `api/domains.py`, `services/graphrag_service.py` | `admin/domains/*`, `kb/graph/*` | Neo4j + PostgreSQL |

---

**Next**: [02 - Technology Stack](02-technology-stack.md) | **Index**: [Architecture](index.md)
