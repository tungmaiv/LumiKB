# Story 1.2: Database Schema and Migration Setup

Status: done

## Story

As a **developer**,
I want **the PostgreSQL database schema established with migrations**,
so that **data models are versioned and reproducible**.

## Acceptance Criteria

1. **Given** PostgreSQL is running via Docker Compose **When** I run `alembic upgrade head` **Then** all tables are created successfully

2. **Given** the database migrations have run **When** I inspect the database **Then** the following tables exist with correct schemas:
   - `users` (id, email, hashed_password, is_active, is_superuser, is_verified, created_at, updated_at)
   - `knowledge_bases` (id, name, description, owner_id, status, created_at, updated_at)
   - `kb_permissions` (id, user_id, kb_id, permission_level, created_at)
   - `documents` (id, kb_id, name, file_path, status, chunk_count, last_error, created_at, updated_at)
   - `outbox` (id, event_type, aggregate_id, payload, created_at, processed_at, attempts, last_error)
   - `audit.events` (id, timestamp, user_id, action, resource_type, resource_id, details, ip_address)

3. **Given** the audit schema exists **When** I check role permissions **Then** the `audit_writer` role has INSERT-only permissions on `audit.events`

4. **Given** I need to modify the schema **When** I create a new migration **Then** `alembic revision --autogenerate` creates a valid migration file

5. **Given** I want to roll back changes **When** I run `alembic downgrade -1` **Then** the previous migration is reverted cleanly

## Tasks / Subtasks

- [x] **Task 1: Install and configure Alembic** (AC: 4, 5)
  - [x] Add alembic to backend dependencies in pyproject.toml
  - [x] Run `alembic init alembic` to create migration directory
  - [x] Configure alembic.ini with async PostgreSQL connection
  - [x] Configure alembic/env.py for async SQLAlchemy with target_metadata

- [x] **Task 2: Create SQLAlchemy base and models** (AC: 2)
  - [x] Create `backend/app/models/base.py` with Base declarative class
  - [x] Create `backend/app/models/user.py` with User model (FastAPI-Users compatible)
  - [x] Create `backend/app/models/knowledge_base.py` with KnowledgeBase model
  - [x] Create `backend/app/models/permission.py` with KBPermission model
  - [x] Create `backend/app/models/document.py` with Document model
  - [x] Create `backend/app/models/outbox.py` with Outbox model
  - [x] Create `backend/app/models/audit.py` with AuditEvent model
  - [x] Update `backend/app/models/__init__.py` to export all models

- [x] **Task 3: Create initial migration** (AC: 1, 2)
  - [x] Generate migration: `alembic revision --autogenerate -m "initial_schema"`
  - [x] Review generated migration for correctness
  - [x] Add enum types for document_status and permission_level
  - [x] Add foreign key constraints with ON DELETE CASCADE where appropriate
  - [x] Add indexes: outbox_unprocessed, audit_user, audit_timestamp, audit_resource

- [x] **Task 4: Create audit schema and role** (AC: 3)
  - [x] Create separate migration for audit schema
  - [x] Create `audit` schema: `CREATE SCHEMA audit`
  - [x] Create `audit_writer` role with INSERT-only permissions
  - [x] Grant appropriate permissions to application role

- [x] **Task 5: Configure database connection** (AC: 1)
  - [x] Update `backend/app/core/config.py` with DATABASE_URL setting
  - [x] Create `backend/app/core/database.py` with async engine and session factory
  - [x] Create async session dependency for FastAPI

- [x] **Task 6: Verify migrations** (AC: 1, 2, 3, 4, 5)
  - [x] Start PostgreSQL via Docker Compose
  - [x] Run `alembic upgrade head` and verify success
  - [x] Verify all tables exist with correct columns
  - [x] Verify audit.events table has INSERT-only constraint
  - [x] Test rollback with `alembic downgrade -1`
  - [x] Test re-upgrade with `alembic upgrade head`

- [x] **Task 7: Create test fixtures** (AC: 1)
  - [x] Create test database configuration
  - [x] Update conftest.py with database fixtures
  - [x] Create migration test to verify upgrade/downgrade cycle

## Dev Notes

### Learnings from Previous Story

**From Story 1-1-project-initialization-and-repository-setup (Status: done)**

- **Project Structure Created**: Backend structure at `backend/app/` with api/, core/, models/, schemas/, services/, repositories/, workers/, integrations/ directories
- **Python Environment**: Python 3.13 used (compatible with >=3.11 requirement), virtual environment at `backend/.venv`
- **Configuration Pattern**: `pydantic_settings.BaseSettings` used with `LUMIKB_` prefix for environment variables
- **Existing Config**: `backend/app/core/config.py` exists with Settings class - extend this for DATABASE_URL
- **Testing Setup**: pytest-asyncio configured with `asyncio_mode = "auto"`, fixtures in `backend/tests/conftest.py`

[Source: docs/sprint-artifacts/1-1-project-initialization-and-repository-setup.md#Dev-Agent-Record]

### Architecture Constraints

- **Database**: PostgreSQL 16 via Docker Compose (from Story 1.3, but can use external for now)
- **ORM**: SQLAlchemy 2.0.44 with async support (asyncpg driver)
- **Migrations**: Alembic >=1.14.0
- **Models**: Use UUID primary keys with `gen_random_uuid()`
- **Timestamps**: All tables should have `created_at` and `updated_at` with TIMESTAMPTZ

### Schema Design from Tech Spec

The schema follows the Epic 1 Technical Specification:

```sql
-- Document status enum values
PENDING, PROCESSING, READY, FAILED, ARCHIVED

-- Permission level enum values
READ, WRITE, ADMIN
```

### Key Indexes to Create

```sql
-- Outbox: for finding unprocessed events
CREATE INDEX idx_outbox_unprocessed ON outbox (created_at) WHERE processed_at IS NULL;

-- Audit: for common query patterns
CREATE INDEX idx_audit_user ON audit.events (user_id);
CREATE INDEX idx_audit_timestamp ON audit.events (timestamp);
CREATE INDEX idx_audit_resource ON audit.events (resource_type, resource_id);
```

### Audit Schema Security

The audit schema uses INSERT-only permissions to ensure immutability:

```sql
CREATE ROLE audit_writer;
GRANT USAGE ON SCHEMA audit TO audit_writer;
GRANT INSERT ON audit.events TO audit_writer;
-- No UPDATE or DELETE permissions
```

### Project Structure Notes

- All models go in `backend/app/models/`
- Use SQLAlchemy 2.0 style with `mapped_column()` and type annotations
- Models must be imported in `env.py` for autogenerate to work
- Database session management follows async patterns per architecture.md

### References

- [Source: docs/architecture.md#Data-Architecture] - Entity relationships and table design
- [Source: docs/architecture.md#PostgreSQL-Tables] - Table purposes and key columns
- [Source: docs/architecture.md#Audit-Schema] - Audit table and INSERT-only permissions
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#PostgreSQL-Schema] - Complete SQL schema definitions
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md#SQLAlchemy-Models] - Model examples
- [Source: docs/epics.md#Story-1.2] - Original story definition

## Dev Agent Record

### Context Reference

- [1-2-database-schema-and-migration-setup.context.xml](1-2-database-schema-and-migration-setup.context.xml)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- Initialized Alembic with async template (`alembic init -t async alembic`)
- DATABASE_URL already present in config.py from Story 1.1
- Created models following SQLAlchemy 2.0 patterns with Mapped[] and mapped_column()
- User model extends FastAPI-Users SQLAlchemyBaseUserTableUUID
- Migrations split into two: 001_initial_schema (tables) and 002_audit_schema_and_role (audit)
- Added PostgreSQL to docker-compose.yml for Story 1.3 prerequisite

### Completion Notes List

- All 7 tasks completed successfully
- All 5 acceptance criteria verified:
  - AC1: `alembic upgrade head` creates all tables successfully
  - AC2: All 6 tables exist with correct columns (verified via psql inspection)
  - AC3: `audit_writer` role has INSERT-only permissions (verified)
  - AC4: `alembic revision` creates valid migration files
  - AC5: `alembic downgrade -1` reverts cleanly, re-upgrade restores schema
- 16 tests passing (14 integration + 2 unit)
- Models use SQLAlchemy 2.0 style with type annotations
- All enum types (DocumentStatus, PermissionLevel) defined as Python Enum classes
- Relationships configured with proper back_populates and cascade settings

### File List

**New Files:**
- backend/alembic.ini
- backend/alembic/README
- backend/alembic/env.py
- backend/alembic/script.py.mako
- backend/alembic/versions/001_initial_schema.py
- backend/alembic/versions/002_audit_schema_and_role.py
- backend/app/models/base.py
- backend/app/models/user.py
- backend/app/models/knowledge_base.py
- backend/app/models/permission.py
- backend/app/models/document.py
- backend/app/models/outbox.py
- backend/app/models/audit.py
- backend/app/core/database.py
- backend/tests/integration/__init__.py
- backend/tests/integration/test_database.py

**Modified Files:**
- backend/app/models/__init__.py
- backend/tests/conftest.py
- infrastructure/docker/docker-compose.yml

## Senior Developer Review (AI)

**Review Date:** 2025-11-23
**Reviewer:** Senior Developer Agent (AI Code Review)
**Story Status at Review:** review

### Acceptance Criteria Validation

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | `alembic upgrade head` creates all tables | ✅ PASS | Migrations 001 and 002 execute successfully, verified via test suite |
| AC2 | All 6 tables exist with correct schemas | ✅ PASS | Integration tests validate all columns in users, knowledge_bases, kb_permissions, documents, outbox, audit.events |
| AC3 | audit_writer role has INSERT-only permissions | ✅ PASS | Migration 002 creates role with only INSERT grant, no UPDATE/DELETE |
| AC4 | `alembic revision --autogenerate` creates valid migration | ✅ PASS | Alembic properly configured with target_metadata from models |
| AC5 | `alembic downgrade -1` reverts cleanly | ✅ PASS | Downgrade functions properly drop tables/indexes/enums in reverse order |

### Task Completion Verification

| Task | Description | Status | Notes |
|------|-------------|--------|-------|
| Task 1 | Install and configure Alembic | ✅ Complete | Async template used, env.py properly configured |
| Task 2 | Create SQLAlchemy base and models | ✅ Complete | 7 models with SQLAlchemy 2.0 patterns |
| Task 3 | Create initial migration | ✅ Complete | 001_initial_schema.py with all tables |
| Task 4 | Create audit schema and role | ✅ Complete | 002_audit_schema_and_role.py with proper permissions |
| Task 5 | Configure database connection | ✅ Complete | database.py with async session factory |
| Task 6 | Verify migrations | ✅ Complete | Manual and automated verification |
| Task 7 | Create test fixtures | ✅ Complete | 14 integration tests passing |

### Code Quality Assessment

**Strengths:**
- SQLAlchemy 2.0 style consistently used with `Mapped[]` and `mapped_column()` type annotations
- User model properly extends `SQLAlchemyBaseUserTableUUID` for FastAPI-Users compatibility
- Relationships configured with appropriate `back_populates` and cascade settings
- Enums defined as Python Enum classes mapped to PostgreSQL ENUM types
- Proper use of UUID primary keys with `gen_random_uuid()` server default
- Timestamps use TIMESTAMPTZ for timezone awareness
- Partial index on outbox for efficient unprocessed event queries
- Comprehensive integration tests covering schema and CRUD operations

**Architecture Alignment:**
- Follows architecture.md data model specifications
- Implements tech-spec-epic-1.md schema requirements
- Async patterns align with FastAPI async architecture

**Security Considerations:**
- audit_writer role correctly restricted to INSERT-only
- Foreign keys use appropriate CASCADE/SET NULL behaviors
- No sensitive data exposed in migration scripts

### Issues Found

**Critical:** None

**Major:** None

**Minor:**
1. **audit.events indexes**: The tech spec mentions `idx_audit_user`, `idx_audit_timestamp`, and `idx_audit_resource` indexes, which are implemented in migration 002. All present.

### Recommendations

1. Consider adding a migration test that explicitly verifies the upgrade/downgrade cycle in CI pipeline
2. Document the audit_writer role usage in deployment runbook for production setup

### Review Outcome

**APPROVED** ✅

All acceptance criteria are met. All tasks are verified complete. Code follows established patterns and architecture guidelines. No blocking issues found.

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-23 | Initial draft created from epics.md and tech-spec-epic-1.md | SM Agent (Bob) |
| 2025-11-23 | Implementation complete - all tasks done, all ACs verified | Dev Agent (Amelia) |
| 2025-11-23 | Code review completed - APPROVED | Senior Developer Agent (AI) |
| 2025-11-23 | Story marked DONE - DoD complete | Dev Agent (Amelia) |

### Completion Notes
**Completed:** 2025-11-23
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing
