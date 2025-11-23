# Epic Technical Specification: Foundation & Authentication

Date: 2025-11-23
Author: Tung Vu
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational infrastructure for LumiKB, an enterprise RAG-powered knowledge management platform. This epic creates the project scaffolding, database schema, development environment, authentication system, and basic UI shell. It delivers the minimum viable infrastructure needed for subsequent epics to build upon, while also providing a demo Knowledge Base that allows users to immediately experience the platform's value proposition.

The epic addresses functional requirements FR1-8 (User Account & Access), FR53 (Audit Infrastructure), and FR56-57 (User Management Audit) from the PRD, establishing the security and compliance foundation required for the Banking & Financial Services domain.

## Objectives and Scope

### In Scope

- **Project Infrastructure**: Initialize monorepo structure with Next.js 15 frontend and FastAPI backend
- **Database Layer**: PostgreSQL schema with users, knowledge_bases, documents, permissions, outbox, and audit tables
- **Development Environment**: Docker Compose setup for PostgreSQL, Redis, MinIO, Qdrant, and LiteLLM
- **Authentication System**: User registration, login, logout, password reset using FastAPI-Users + JWT
- **User Management**: Admin capabilities to create, modify, and deactivate user accounts
- **Audit Infrastructure**: Immutable audit logging with INSERT-only permissions
- **Frontend Authentication**: Login, registration, and logout UI with shadcn/ui components
- **Dashboard Shell**: Three-panel responsive layout with navigation placeholders
- **Demo Data**: Sample Knowledge Base with pre-indexed demo documents

### Out of Scope

- Knowledge Base CRUD operations (Epic 2)
- Document upload and processing (Epic 2)
- Semantic search functionality (Epic 3)
- Chat interface (Epic 4)
- Document generation (Epic 4)
- Full admin dashboard (Epic 5)

## System Architecture Alignment

This epic implements components from the following architecture layers:

| Layer | Components | Reference |
|-------|------------|-----------|
| **Frontend** | Next.js App Router, shadcn/ui, Zustand auth store | `frontend/src/app/(auth)/*`, `frontend/src/app/(dashboard)/*` |
| **API Gateway** | Auth Router, Users Router | `backend/app/api/v1/auth.py`, `backend/app/api/v1/users.py` |
| **Service Layer** | Auth Service, Audit Service | `backend/app/services/auth_service.py`, `backend/app/services/audit_service.py` |
| **Data Layer** | PostgreSQL (users, audit schema) | `backend/app/models/user.py`, `backend/app/models/audit.py` |
| **Infrastructure** | PostgreSQL, Redis, MinIO, Qdrant, LiteLLM | `infrastructure/docker/docker-compose.yml` |

**Architectural Constraints:**
- Python 3.11 required for redis-py >=7.1.0 compatibility
- FastAPI-Users[sqlalchemy] (NOT sqlalchemy2 - deprecated extra)
- pydantic_settings.BaseSettings (NOT pydantic.BaseSettings)
- tw-animate-css (NOT tailwindcss-animate - deprecated)
- Next.js 15 App Router (NOT Pages Router)

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| **Auth Router** | HTTP endpoints for registration, login, logout, password reset | HTTP requests | JWT tokens (httpOnly cookies), session data | `api/v1/auth.py` |
| **Users Router** | Profile management endpoints | HTTP requests + JWT | User profile data | `api/v1/users.py` |
| **Admin Router** | User management for administrators | HTTP requests + Admin JWT | User list, user operations | `api/v1/admin.py` |
| **Auth Service** | Business logic for authentication flows | User credentials | Validated user, session tokens | `services/auth_service.py` |
| **Audit Service** | Async audit event logging | Audit event data | Logged event (fire-and-forget) | `services/audit_service.py` |
| **User Repository** | Data access for user table | Query parameters | User models | `repositories/user_repo.py` |

### Data Models and Contracts

#### PostgreSQL Schema

```sql
-- Users table (FastAPI-Users compatible)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge Bases table (placeholder for Epic 2)
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- KB Permissions table
CREATE TABLE kb_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    kb_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL, -- READ, WRITE, ADMIN
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, kb_id)
);

-- Documents table (placeholder for Epic 2)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending', -- PENDING, PROCESSING, READY, FAILED, ARCHIVED
    chunk_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outbox table (for transactional consistency)
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
CREATE INDEX idx_outbox_unprocessed ON outbox (created_at) WHERE processed_at IS NULL;

-- Audit schema (INSERT-only)
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

CREATE INDEX idx_audit_user ON audit.events (user_id);
CREATE INDEX idx_audit_timestamp ON audit.events (timestamp);
CREATE INDEX idx_audit_resource ON audit.events (resource_type, resource_id);

-- Audit role with INSERT-only permissions
CREATE ROLE audit_writer;
GRANT USAGE ON SCHEMA audit TO audit_writer;
GRANT INSERT ON audit.events TO audit_writer;
```

#### SQLAlchemy Models

```python
# backend/app/models/user.py
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.sql import func

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### Pydantic Schemas

```python
# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str  # Min 8 characters, validated by FastAPI-Users

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
```

### APIs and Interfaces

| Method | Path | Request Body | Response | Error Codes |
|--------|------|--------------|----------|-------------|
| POST | `/api/v1/auth/register` | `{ email, password }` | `UserRead` | 400 (validation), 409 (email exists) |
| POST | `/api/v1/auth/login` | `{ email, password }` | Set-Cookie: JWT | 400 (invalid credentials), 429 (rate limited) |
| POST | `/api/v1/auth/logout` | - | 200 OK | 401 (not authenticated) |
| POST | `/api/v1/auth/forgot-password` | `{ email }` | 202 Accepted | - |
| POST | `/api/v1/auth/reset-password` | `{ token, password }` | 200 OK | 400 (invalid token) |
| GET | `/api/v1/users/me` | - | `UserRead` | 401 (not authenticated) |
| PATCH | `/api/v1/users/me` | `UserUpdate` | `UserRead` | 401, 400 (validation) |
| GET | `/api/v1/admin/users` | Query: skip, limit | `{ data: UserRead[], meta: pagination }` | 401, 403 (not admin) |
| POST | `/api/v1/admin/users` | `UserCreate` | `UserRead` | 401, 403, 400, 409 |
| PATCH | `/api/v1/admin/users/{id}` | `{ is_active }` | `UserRead` | 401, 403, 404 |

### Workflows and Sequencing

#### User Registration Flow

```
1. User submits email + password → POST /api/v1/auth/register
2. FastAPI-Users validates input (email format, password length)
3. Check email uniqueness in users table
4. Hash password with argon2
5. INSERT user record
6. Audit: LOG "user.registered" event (async)
7. Return UserRead response
```

#### User Login Flow

```
1. User submits credentials → POST /api/v1/auth/login
2. FastAPI-Users validates credentials
3. On success:
   a. Generate JWT token (60 min expiry)
   b. Store session metadata in Redis (user_id, login_time, ip)
   c. Set httpOnly cookie with JWT
   d. Audit: LOG "user.login" event (async)
   e. Return 200 OK
4. On failure:
   a. Increment failed attempts in Redis
   b. If attempts > 5 in 15 min: rate limit (429)
   c. Audit: LOG "user.login_failed" event (async)
   d. Return 400 Invalid credentials
```

#### Password Reset Flow

```
1. User submits email → POST /api/v1/auth/forgot-password
2. Generate reset token (1 hour expiry)
3. Store token hash in Redis
4. Log reset token to console (mock email for MVP)
5. Audit: LOG "user.password_reset_requested" (async)
6. Return 202 Accepted

7. User submits token + new password → POST /api/v1/auth/reset-password
8. Validate token from Redis
9. Update user password (argon2 hash)
10. Invalidate all user sessions in Redis
11. Audit: LOG "user.password_reset_completed" (async)
12. Return 200 OK
```

## Non-Functional Requirements

### Performance

| Metric | Target | Implementation |
|--------|--------|----------------|
| Login response time | < 500ms | Direct DB query, async audit logging |
| Registration response time | < 1s | Password hashing is CPU-bound (argon2 configured for ~500ms) |
| Protected endpoint auth check | < 50ms | JWT validation (no DB hit), Redis session check |
| Concurrent auth requests | 100 req/s | FastAPI async + connection pooling |

### Security

| Requirement | Implementation | Source |
|-------------|----------------|--------|
| Password hashing | argon2-cffi (memory-hard, configurable cost) | SOC 2 |
| Session tokens | JWT with 60 min expiry, httpOnly + Secure + SameSite cookies | SOC 2, OWASP |
| CSRF protection | SameSite=Strict cookies | OWASP |
| Rate limiting | Redis-based, 5 failed logins per 15 min per IP | OWASP, SOC 2 |
| Password requirements | Minimum 8 characters (enforced by FastAPI-Users) | ISO 27001 |
| Encryption in transit | TLS 1.3 required (nginx/reverse proxy) | PCI-DSS, SOC 2 |
| Secret management | Environment variables via pydantic-settings | Security best practice |

### Reliability/Availability

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Auth service availability | 99% during business hours | Health checks, graceful degradation |
| Session persistence | Zero session loss on backend restart | Redis session storage |
| Audit log durability | Zero audit events lost | Async write with retry, separate audit role |

### Observability

| Signal | Implementation |
|--------|----------------|
| Structured logging | structlog with JSON output, request_id correlation |
| Auth metrics | `auth_login_total`, `auth_login_failures`, `auth_registration_total` (Prometheus) |
| Health endpoint | `/health` returns database connectivity, Redis connectivity |
| Request tracing | X-Request-ID header propagation |

## Dependencies and Integrations

### Backend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115.0,<1.0.0 | Web framework |
| uvicorn[standard] | >=0.32.0,<1.0.0 | ASGI server |
| pydantic | >=2.7.0,<3.0.0 | Data validation |
| pydantic-settings | >=2.0.0,<3.0.0 | Configuration management |
| sqlalchemy[asyncio] | >=2.0.44,<3.0.0 | ORM |
| asyncpg | >=0.30.0,<1.0.0 | PostgreSQL async driver |
| alembic | >=1.14.0,<2.0.0 | Database migrations |
| fastapi-users[sqlalchemy] | >=14.0.0,<15.0.0 | Auth framework |
| argon2-cffi | >=23.1.0,<24.0.0 | Password hashing |
| redis | >=7.1.0,<8.0.0 | Session/cache (requires Python >=3.10) |
| structlog | >=25.5.0,<26.0.0 | Structured logging |
| pytest | >=7.0.0 | Testing |
| pytest-asyncio | >=0.23.0 | Async test support |
| ruff | latest | Linting |

### Frontend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | 15.x | React framework |
| react | 19.x | UI library |
| typescript | latest | Type safety |
| tailwindcss | 4.x | Styling |
| tw-animate-css | latest | Animations |
| zustand | >=5.0.0 | State management |
| react-hook-form | latest | Form handling |
| @hookform/resolvers | latest | Form validation |
| zod | latest | Schema validation |
| eslint | latest | Linting |
| prettier | latest | Formatting |

### Infrastructure Dependencies

| Service | Version | Port | Purpose |
|---------|---------|------|---------|
| PostgreSQL | 16 | 5432 | Primary database |
| Redis | >=7.0.0 | 6379 | Sessions, cache, rate limiting |
| MinIO | latest | 9000, 9001 | Object storage (prepared for Epic 2) |
| Qdrant | >=1.10.0 | 6333, 6334 | Vector database (prepared for Epic 3) |
| LiteLLM | latest | 4000 | LLM gateway (prepared for Epic 3) |

## Acceptance Criteria (Authoritative)

### Epic-Level Acceptance Criteria

| ID | Criteria |
|----|----------|
| E1-AC1 | User can create account, login, logout, and reset password |
| E1-AC2 | Admin can create, list, and deactivate users |
| E1-AC3 | All auth events are logged to immutable audit table |
| E1-AC4 | Docker Compose starts all infrastructure services |
| E1-AC5 | Frontend displays login/register pages with proper styling |
| E1-AC6 | Dashboard shell renders three-panel layout after login |
| E1-AC7 | Demo Knowledge Base is seeded and visible to users |

### Story-Level Acceptance Criteria Summary

| Story | Key Acceptance Criteria |
|-------|------------------------|
| 1.1 | Repo structure matches architecture; both frontend and backend start; tooling configured |
| 1.2 | All tables created via migrations; audit schema has INSERT-only permissions |
| 1.3 | `docker compose up -d` starts all services with health checks passing |
| 1.4 | Registration creates user; login returns JWT cookie; logout invalidates session |
| 1.5 | GET/PATCH /users/me works; password reset flow functional |
| 1.6 | Admin can list/create/deactivate users; non-admin gets 403 |
| 1.7 | All auth actions logged; audit_writer role is INSERT-only |
| 1.8 | Login/register UI renders; successful login redirects to dashboard |
| 1.9 | Three-panel responsive layout; header with logo and user menu |
| 1.10 | Demo KB seeded with documents; visible to all users |

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component(s) | Test Idea |
|---------------------|--------------|--------------|-----------|
| E1-AC1 | APIs and Interfaces | Auth Router, Auth Service | Test registration, login, logout, password reset endpoints |
| E1-AC2 | APIs and Interfaces | Admin Router | Test admin user CRUD with permission checks |
| E1-AC3 | Data Models, NFR Security | Audit Service, audit.events table | Verify audit events exist after each action; verify INSERT-only |
| E1-AC4 | Dependencies | docker-compose.yml | `docker compose up` passes health checks |
| E1-AC5 | - | `frontend/src/app/(auth)/*` | Visual regression test on login/register pages |
| E1-AC6 | - | `frontend/src/app/(dashboard)/*` | Test responsive breakpoints; verify three panels render |
| E1-AC7 | Story 1.10 | seed-data.sh, demo-docs | Verify demo KB exists after seeding; verify user can see it |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **FastAPI-Users version compatibility** | High - auth system depends on it | Pin to >=14.0.0,<15.0.0; test upgrade path before v15 adoption |
| **Redis connection failures** | Medium - sessions unavailable | Implement graceful degradation; allow stateless JWT-only mode |
| **Audit logging performance** | Low - could impact latency | Async background task; batch writes if volume is high |

### Assumptions

| Assumption | Dependency |
|------------|------------|
| Email sending is mocked (console logging) for MVP | No external email service required |
| Python 3.11 is available in all deployment environments | Container-based deployment uses Python 3.11 image |
| Single-instance deployment for MVP (no clustering) | Horizontal scaling deferred to post-MVP |
| Demo KB uses pre-computed embeddings | Full processing pipeline not available until Epic 2 |

### Open Questions

| Question | Resolution Path |
|----------|-----------------|
| Should we implement email verification for MVP? | Defer to post-MVP; use is_verified flag but don't enforce |
| What password complexity rules beyond length? | Start with 8 chars minimum; add complexity rules based on feedback |
| Should rate limiting be per-IP or per-email? | Start with per-IP; add per-email if needed |

## Test Strategy Summary

### Test Levels

| Level | Scope | Framework | Coverage |
|-------|-------|-----------|----------|
| Unit | Services, utilities | pytest | Business logic isolation |
| Integration | API endpoints with DB | pytest + httpx | Full request/response cycle |
| E2E | User flows | Playwright | Login, registration, navigation |

### Test Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| Auth Service | 90% | Critical security component |
| Audit Service | 80% | Compliance requirement |
| API Routes | 80% | User-facing contracts |
| Frontend Auth | 70% | User-critical flows |

### Key Test Scenarios

| Scenario | Type | Priority |
|----------|------|----------|
| User registration with valid/invalid data | Integration | P0 |
| Login success and failure paths | Integration | P0 |
| Rate limiting after failed logins | Integration | P1 |
| Audit events created for all actions | Integration | P0 |
| JWT validation and session management | Unit | P0 |
| Admin permission enforcement | Integration | P0 |
| Responsive layout breakpoints | E2E | P2 |
| Demo KB visibility after login | E2E | P1 |

### Test Commands

```bash
# Backend
cd backend
pytest                           # All tests
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests
pytest -k "auth"                # Auth-related tests
pytest --cov=app --cov-report=html

# Frontend
cd frontend
npm test                        # All tests
npm test -- --watch            # Watch mode
npm run test:e2e               # Playwright E2E
```
