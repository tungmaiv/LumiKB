# Story 1.3: Docker Compose Development Environment

Status: done

## Story

As a **developer**,
I want **a complete local development environment via Docker Compose**,
so that **all services can be started with a single command**.

## Acceptance Criteria

1. **Given** Docker and Docker Compose are installed **When** I run `docker compose up -d` from the infrastructure/docker directory **Then** all required services start successfully:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - MinIO (ports 9000, 9001)
   - Qdrant (ports 6333, 6334)
   - LiteLLM Proxy (port 4000)

2. **Given** all services are running **When** I check their status **Then** health checks pass for all services

3. **Given** the services are running **When** I stop and restart Docker Compose **Then** data persists in named volumes

4. **Given** the repository is cloned **When** I check the infrastructure/docker directory **Then** `.env.example` documents all required environment variables

5. **Given** the services are healthy **When** the backend application starts **Then** it can connect to PostgreSQL, Redis, MinIO, and Qdrant successfully

## Tasks / Subtasks

- [x] **Task 1: Create Docker Compose configuration** (AC: 1)
  - [x] Create/update `infrastructure/docker/docker-compose.yml` with all services
  - [x] Configure PostgreSQL 16 service with health check
  - [x] Configure Redis >=7.0.0 service with health check
  - [x] Configure MinIO (latest) service with health check and console
  - [x] Configure Qdrant >=1.10.0 service with health check (REST and gRPC ports)
  - [x] Configure LiteLLM Proxy service with health check

- [x] **Task 2: Configure service networking** (AC: 1, 5)
  - [x] Create dedicated Docker network for service isolation
  - [x] Ensure all services are on the same network
  - [x] Map appropriate ports for development access

- [x] **Task 3: Configure named volumes for persistence** (AC: 3)
  - [x] Create named volume for PostgreSQL data
  - [x] Create named volume for Redis data
  - [x] Create named volume for MinIO data
  - [x] Create named volume for Qdrant data

- [x] **Task 4: Create environment configuration** (AC: 4)
  - [x] Create `infrastructure/docker/.env.example` with all required variables
  - [x] Document each environment variable with comments
  - [x] Include default development values where appropriate
  - [x] Add instructions for copying to `.env`

- [x] **Task 5: Configure LiteLLM Proxy** (AC: 1)
  - [x] Create `infrastructure/docker/litellm_config.yaml` for LiteLLM configuration
  - [x] Configure model routing and fallback settings
  - [x] Set up health check endpoint

- [x] **Task 6: Verify services and health checks** (AC: 1, 2, 5)
  - [x] Run `docker compose up -d` and verify all services start
  - [x] Verify health checks pass for all services
  - [x] Test PostgreSQL connectivity from backend
  - [x] Test Redis connectivity from backend
  - [x] Test MinIO connectivity (create bucket, upload file)
  - [x] Test Qdrant connectivity (create collection, query)
  - [x] Test LiteLLM connectivity (if API key available)

- [x] **Task 7: Document startup and usage** (AC: 4)
  - [x] Add comments in docker-compose.yml explaining each service
  - [x] Documentation in .env.example with setup instructions
  - [x] Service-specific comments in docker-compose.yml

## Dev Notes

### Learnings from Previous Story

**From Story 1-2-database-schema-and-migration-setup (Status: done)**

- **PostgreSQL Already Configured**: Story 1.2 added PostgreSQL to docker-compose.yml as a prerequisite. Verify and enhance the existing configuration.
- **Database Schema Ready**: All tables exist (users, knowledge_bases, kb_permissions, documents, outbox, audit.events)
- **Models Use SQLAlchemy 2.0**: Async patterns with `Mapped[]` and `mapped_column()`
- **Database Connection**: `backend/app/core/database.py` exists with async session factory
- **Config Pattern**: `DATABASE_URL` already in `backend/app/core/config.py` with `LUMIKB_` prefix

**Key Files from Previous Stories:**
- `infrastructure/docker/docker-compose.yml` - Already contains PostgreSQL from Story 1.2
- `backend/app/core/config.py` - Settings class for environment variables
- `backend/app/core/database.py` - Database session management

[Source: docs/sprint-artifacts/1-2-database-schema-and-migration-setup.md#Dev-Agent-Record]

### Architecture Constraints

From [architecture.md](../../docs/architecture.md):

| Service | Version | Port(s) | Purpose |
|---------|---------|---------|---------|
| PostgreSQL | 16 | 5432 | Primary database |
| Redis | >=7.0.0 | 6379 | Sessions, cache, rate limiting, Celery broker |
| MinIO | latest | 9000, 9001 | Object storage (S3-compatible) for documents |
| Qdrant | >=1.10.0 | 6333, 6334 | Vector database (REST and gRPC) |
| LiteLLM | latest | 4000 | LLM gateway for model abstraction |

### Service Configuration Details

#### PostgreSQL
- Image: `postgres:16`
- Health check: `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}`
- Volume: `postgres_data:/var/lib/postgresql/data`

#### Redis
- Image: `redis:7-alpine`
- Health check: `redis-cli ping`
- Volume: `redis_data:/data`

#### MinIO
- Image: `minio/minio:latest`
- Command: `server /data --console-address ":9001"`
- Health check: `curl -f http://localhost:9000/minio/health/live`
- Volume: `minio_data:/data`
- Console at port 9001

#### Qdrant
- Image: `qdrant/qdrant:latest` (or pin to >=1.10.0)
- Health check: `curl -f http://localhost:6333/health`
- Ports: 6333 (REST), 6334 (gRPC)
- Volume: `qdrant_data:/qdrant/storage`

#### LiteLLM
- Image: `ghcr.io/berriai/litellm:main-latest`
- Health check: `curl -f http://localhost:4000/health`
- Requires config file mount
- Environment variables for API keys

### Environment Variables

```bash
# PostgreSQL
POSTGRES_USER=lumikb
POSTGRES_PASSWORD=lumikb_dev_password
POSTGRES_DB=lumikb

# Redis
REDIS_PASSWORD=  # Optional for dev

# MinIO
MINIO_ROOT_USER=lumikb
MINIO_ROOT_PASSWORD=lumikb_dev_password

# LiteLLM
LITELLM_MASTER_KEY=sk-dev-master-key
OPENAI_API_KEY=  # Optional, for actual LLM calls
```

### Project Structure Notes

- Docker Compose file at `infrastructure/docker/docker-compose.yml`
- Environment example at `infrastructure/docker/.env.example`
- LiteLLM config at `infrastructure/docker/litellm_config.yaml`
- Backend connects via environment variables with `LUMIKB_` prefix

### References

- [Source: docs/architecture.md#Deployment-Architecture] - Container architecture and service ports
- [Source: docs/architecture.md#Infrastructure-Dependencies] - Service versions and purposes
- [Source: docs/architecture.md#Environment-Configuration] - Environment variable patterns
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#Infrastructure-Dependencies] - Service versions and ports
- [Source: docs/epics.md#Story-1.3] - Original story definition

## Dev Agent Record

### Context Reference

- [1-3-docker-compose-development-environment.context.xml](1-3-docker-compose-development-environment.context.xml)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- Implemented complete Docker Compose configuration with all 5 infrastructure services
- Used bash TCP health check for Qdrant (no curl/wget in image)
- Used Python urllib for LiteLLM health check
- Updated backend config.py with Redis, MinIO, Qdrant, LiteLLM settings
- Fixed test database URL parsing in conftest.py
- All 23 tests passing (14 from Story 1.2 + 7 connectivity + 2 unit)

### Completion Notes List

- All 5 acceptance criteria verified:
  - AC1: `docker compose up -d` starts all services (PostgreSQL, Redis, MinIO, Qdrant, LiteLLM)
  - AC2: All health checks pass (verified via `docker compose ps`)
  - AC3: Named volumes configured for persistence (postgres_data, redis_data, minio_data, qdrant_data)
  - AC4: `.env.example` created with documented environment variables
  - AC5: Backend can connect to all services (verified via integration tests)
- 7 new connectivity tests added in `test_service_connectivity.py`
- Integration marker registered in pytest configuration

### File List

**New Files:**
- infrastructure/docker/.env.example
- infrastructure/docker/litellm_config.yaml
- backend/tests/integration/test_service_connectivity.py

**Modified Files:**
- infrastructure/docker/docker-compose.yml (complete rewrite with all services)
- backend/app/core/config.py (added Redis, MinIO, Qdrant, LiteLLM settings)
- backend/pyproject.toml (added integration marker)
- backend/tests/conftest.py (fixed test database URL parsing)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-23 | Initial draft created from epics.md, tech-spec-epic-1.md, and architecture.md | SM Agent (Bob) |
| 2025-11-23 | Story context generated, status updated to ready-for-dev | SM Agent (Bob) |
| 2025-11-23 | Implementation complete - all 7 tasks done, all ACs verified | Dev Agent (Amelia) |
| 2025-11-23 | Senior Developer Review - APPROVED | Dev Agent (Amelia) |

## Senior Developer Review (AI)

### Reviewer
Tung Vu

### Date
2025-11-23

### Outcome
**✅ APPROVED**

All acceptance criteria are fully implemented and verified with evidence. All tasks marked complete have been confirmed through code inspection and integration tests. No issues found.

### Summary

Story 1.3 successfully delivers a complete Docker Compose development environment with all 5 required infrastructure services (PostgreSQL, Redis, MinIO, Qdrant, LiteLLM). The implementation follows architecture guidelines, uses appropriate health checks, and includes comprehensive integration tests verifying backend connectivity to all services.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity (Advisory):**
- Note: The LiteLLM container pulls `main-latest` tag which may introduce unexpected changes. Consider pinning to a specific version for production stability.
- Note: Default passwords are documented in `.env.example` - ensure these are changed in any non-local deployment.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | `docker compose up -d` starts all services (PostgreSQL 5432, Redis 6379, MinIO 9000/9001, Qdrant 6333/6334, LiteLLM 4000) | ✅ IMPLEMENTED | [docker-compose.yml:11-127](infrastructure/docker/docker-compose.yml#L11-L127) - All 5 services defined with correct ports |
| AC2 | Health checks pass for all services | ✅ IMPLEMENTED | [docker-compose.yml:22-26](infrastructure/docker/docker-compose.yml#L22-L26) (PostgreSQL), [docker-compose.yml:44-48](infrastructure/docker/docker-compose.yml#L44-L48) (Redis), [docker-compose.yml:70-74](infrastructure/docker/docker-compose.yml#L70-L74) (MinIO), [docker-compose.yml:92-96](infrastructure/docker/docker-compose.yml#L92-L96) (Qdrant), [docker-compose.yml:118-123](infrastructure/docker/docker-compose.yml#L118-L123) (LiteLLM). Verified via `docker compose ps` showing all "healthy" |
| AC3 | Data persists in named volumes across restarts | ✅ IMPLEMENTED | [docker-compose.yml:141-149](infrastructure/docker/docker-compose.yml#L141-L149) - Named volumes: postgres_data, redis_data, minio_data, qdrant_data |
| AC4 | `.env.example` documents all required environment variables | ✅ IMPLEMENTED | [.env.example:1-86](infrastructure/docker/.env.example#L1-L86) - All variables documented with comments and setup instructions |
| AC5 | Backend can connect to PostgreSQL, Redis, MinIO, Qdrant successfully | ✅ IMPLEMENTED | [test_service_connectivity.py:22-145](backend/tests/integration/test_service_connectivity.py#L22-L145) - Integration tests verify all connections. [config.py:31-49](backend/app/core/config.py#L31-L49) - Backend settings configured |

**Summary: 5 of 5 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Create Docker Compose configuration | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:1-150](infrastructure/docker/docker-compose.yml) - All 5 services with health checks |
| Task 1.1: Create/update docker-compose.yml | ✅ Complete | ✅ VERIFIED | File exists with all services |
| Task 1.2: Configure PostgreSQL 16 with health check | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:11-29](infrastructure/docker/docker-compose.yml#L11-L29) |
| Task 1.3: Configure Redis >=7.0.0 with health check | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:36-51](infrastructure/docker/docker-compose.yml#L36-L51) - redis:7-alpine |
| Task 1.4: Configure MinIO with health check and console | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:58-77](infrastructure/docker/docker-compose.yml#L58-L77) - Ports 9000, 9001 |
| Task 1.5: Configure Qdrant with health check (REST and gRPC) | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:84-99](infrastructure/docker/docker-compose.yml#L84-L99) - Ports 6333, 6334 |
| Task 1.6: Configure LiteLLM Proxy with health check | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:106-127](infrastructure/docker/docker-compose.yml#L106-L127) |
| Task 2: Configure service networking | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:133-136](infrastructure/docker/docker-compose.yml#L133-L136) - lumikb-network bridge |
| Task 2.1: Create dedicated Docker network | ✅ Complete | ✅ VERIFIED | Network definition at line 133-136 |
| Task 2.2: Ensure all services on same network | ✅ Complete | ✅ VERIFIED | Each service has `networks: - lumikb-network` |
| Task 2.3: Map appropriate ports | ✅ Complete | ✅ VERIFIED | All services expose required ports |
| Task 3: Configure named volumes for persistence | ✅ Complete | ✅ VERIFIED | [docker-compose.yml:141-149](infrastructure/docker/docker-compose.yml#L141-L149) |
| Task 3.1: PostgreSQL volume | ✅ Complete | ✅ VERIFIED | lumikb-postgres-data |
| Task 3.2: Redis volume | ✅ Complete | ✅ VERIFIED | lumikb-redis-data |
| Task 3.3: MinIO volume | ✅ Complete | ✅ VERIFIED | lumikb-minio-data |
| Task 3.4: Qdrant volume | ✅ Complete | ✅ VERIFIED | lumikb-qdrant-data |
| Task 4: Create environment configuration | ✅ Complete | ✅ VERIFIED | [.env.example:1-86](infrastructure/docker/.env.example#L1-L86) |
| Task 4.1: Create .env.example | ✅ Complete | ✅ VERIFIED | File exists at infrastructure/docker/.env.example |
| Task 4.2: Document each variable with comments | ✅ Complete | ✅ VERIFIED | Comprehensive comments for all sections |
| Task 4.3: Include default development values | ✅ Complete | ✅ VERIFIED | Default values provided for all services |
| Task 4.4: Add instructions for copying to .env | ✅ Complete | ✅ VERIFIED | Lines 4-9 include usage instructions |
| Task 5: Configure LiteLLM Proxy | ✅ Complete | ✅ VERIFIED | [litellm_config.yaml:1-119](infrastructure/docker/litellm_config.yaml#L1-L119) |
| Task 5.1: Create litellm_config.yaml | ✅ Complete | ✅ VERIFIED | File exists with model definitions |
| Task 5.2: Configure model routing and fallback | ✅ Complete | ✅ VERIFIED | Lines 79-88 define routing and fallbacks |
| Task 5.3: Set up health check endpoint | ✅ Complete | ✅ VERIFIED | Health check configured in docker-compose.yml |
| Task 6: Verify services and health checks | ✅ Complete | ✅ VERIFIED | All services running healthy, 7 integration tests pass |
| Task 6.1: Run docker compose up -d | ✅ Complete | ✅ VERIFIED | Services running: `docker compose ps` shows all healthy |
| Task 6.2: Verify health checks | ✅ Complete | ✅ VERIFIED | All 5 services show "(healthy)" status |
| Task 6.3: Test PostgreSQL connectivity | ✅ Complete | ✅ VERIFIED | [test_service_connectivity.py:22-35](backend/tests/integration/test_service_connectivity.py#L22-L35) |
| Task 6.4: Test Redis connectivity | ✅ Complete | ✅ VERIFIED | [test_service_connectivity.py:37-58](backend/tests/integration/test_service_connectivity.py#L37-L58) |
| Task 6.5: Test MinIO connectivity | ✅ Complete | ✅ VERIFIED | [test_service_connectivity.py:60-97](backend/tests/integration/test_service_connectivity.py#L60-L97) |
| Task 6.6: Test Qdrant connectivity | ✅ Complete | ✅ VERIFIED | [test_service_connectivity.py:99-132](backend/tests/integration/test_service_connectivity.py#L99-L132) |
| Task 6.7: Test LiteLLM connectivity | ✅ Complete | ✅ VERIFIED | [test_service_connectivity.py:134-145](backend/tests/integration/test_service_connectivity.py#L134-L145) |
| Task 7: Document startup and usage | ✅ Complete | ✅ VERIFIED | Comments in docker-compose.yml and .env.example |
| Task 7.1: Add comments in docker-compose.yml | ✅ Complete | ✅ VERIFIED | Section headers and service descriptions throughout |
| Task 7.2: Documentation in .env.example | ✅ Complete | ✅ VERIFIED | Comprehensive comments and instructions |
| Task 7.3: Service-specific comments | ✅ Complete | ✅ VERIFIED | Each service section has purpose comments |

**Summary: 37 of 37 completed tasks/subtasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

**Tests Present:**
- 7 integration tests in `test_service_connectivity.py` covering:
  - PostgreSQL connectivity
  - Redis connectivity (ping + set/get)
  - MinIO connectivity (bucket creation, upload/download)
  - Qdrant connectivity (collection creation)
  - LiteLLM health endpoint
  - PostgreSQL data persistence
  - Redis AOF persistence

**Test Quality:** Tests are well-structured with proper cleanup, using contextlib.suppress for error handling, async patterns, and clear assertions.

**No gaps identified** - All acceptance criteria have corresponding test coverage.

### Architectural Alignment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PostgreSQL 16 | ✅ Aligned | [docker-compose.yml:12](infrastructure/docker/docker-compose.yml#L12) - `postgres:16` |
| Redis >=7.0.0 | ✅ Aligned | [docker-compose.yml:37](infrastructure/docker/docker-compose.yml#L37) - `redis:7-alpine` |
| MinIO latest | ✅ Aligned | [docker-compose.yml:59](infrastructure/docker/docker-compose.yml#L59) - `minio/minio:latest` |
| Qdrant >=1.10.0 | ✅ Aligned | [docker-compose.yml:85](infrastructure/docker/docker-compose.yml#L85) - `qdrant/qdrant:latest` |
| LiteLLM latest | ✅ Aligned | [docker-compose.yml:107](infrastructure/docker/docker-compose.yml#L107) - `ghcr.io/berriai/litellm:main-latest` |
| LUMIKB_ env prefix | ✅ Aligned | [config.py:12](backend/app/core/config.py#L12) - `env_prefix="LUMIKB_"` |
| pydantic-settings | ✅ Aligned | [config.py:3](backend/app/core/config.py#L3) - Uses pydantic_settings.BaseSettings |

### Security Notes

- Passwords are development defaults - appropriate for local dev environment
- `.env.example` correctly warns not to commit `.env` to version control
- Redis AOF persistence enabled for data durability
- No sensitive data exposed in docker-compose.yml (uses environment variables)

### Best-Practices and References

- [Docker Compose best practices](https://docs.docker.com/compose/compose-file/)
- [LiteLLM configuration docs](https://docs.litellm.ai/docs/proxy/configs)
- [Qdrant Docker deployment](https://qdrant.tech/documentation/guides/installation/)
- [MinIO Docker deployment](https://min.io/docs/minio/container/index.html)

### Action Items

**Code Changes Required:**
- None required

**Advisory Notes:**
- Note: Consider pinning LiteLLM to a specific version tag for production stability
- Note: The Qdrant health check uses bash TCP which works but could be simplified if Qdrant adds curl to their image
- Note: Redis password is optional for dev but should be enabled for any shared environments
