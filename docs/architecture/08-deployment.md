# Deployment Architecture

← Back to [Architecture Index](index.md) | **Previous**: [07 - Security](07-security.md)

---

## Performance Considerations

### Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Search Response | < 3 seconds | Qdrant gRPC, Redis caching |
| Document Processing | < 2 minutes | Celery workers, parallel chunking |
| Chat Response | < 5 seconds | SSE streaming (first token fast) |
| Concurrent Users | 20+ | FastAPI async, connection pooling |
| Graph Traversal | < 500ms | Neo4j connection pooling, query optimization |
| Entity Extraction | < 5s per chunk | LLM batching, rate limiting |
| GraphRAG Retrieval | < 4 seconds | Parallel vector+graph queries |

### Optimization Strategies

| Area | Strategy |
|------|----------|
| Vector Search | HNSW index, scalar quantization |
| Database | Connection pooling (asyncpg), query optimization |
| Caching | Redis for frequent queries, session data |
| File Uploads | Chunked uploads, background processing |
| LLM Calls | Streaming responses, request caching |
| Graph Queries | Cypher query optimization, index on Entity.name |
| Entity Extraction | Batch processing, dedicated worker queue |

---

## Container Architecture

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
  # ollama:        # Runs on HOST (see Ollama Setup below)
```

### Ollama Setup

**Docker Desktop (Development/E2E):** Docker Desktop on Linux does not support GPU passthrough. Ollama runs on the host machine and Docker containers connect via `host.docker.internal`.

```bash
# Prerequisites - run on host machine
ollama serve                    # Start Ollama server
ollama pull nomic-embed-text    # Embedding model (768 dimensions)
ollama pull gemma3:4b           # Default generation model
```

LiteLLM is configured with:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
environment:
  OLLAMA_API_BASE: http://host.docker.internal:11434
```

**Production (Standard Docker):** Production servers use standard Docker with nvidia-container-toolkit which supports GPU passthrough. Ollama runs as a Docker service with GPU access.

---

## Environment Configuration

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

---

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

---

**Previous**: [07 - Security](07-security.md) | **Next**: [09 - ADRs](09-adrs.md) | **Index**: [Architecture](index.md)
