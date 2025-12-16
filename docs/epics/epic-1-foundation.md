# Epic 1: Foundation & Authentication

**Goal:** Establish project infrastructure, authentication system, and basic UI shell so users can login and explore the application with a demo Knowledge Base.

**User Value:** "I can login securely and immediately explore sample knowledge to understand what LumiKB does."

**FRs Covered:** FR1-8, FR53 (infrastructure), FR56-57 (infrastructure)

**Technical Foundation:**
- Next.js 15 + shadcn/ui frontend
- FastAPI + FastAPI-Users backend
- PostgreSQL database with audit schema
- Redis for sessions and cache
- Docker Compose for local development

---

## Story 1.1: Project Initialization and Repository Setup

As a **developer**,
I want **the project repository initialized with proper structure**,
So that **I have a consistent foundation for all subsequent development**.

**Acceptance Criteria:**

**Given** a new development environment
**When** I clone the repository and run setup commands
**Then** both frontend and backend start successfully

**And** the project structure matches the architecture specification:
- `frontend/` - Next.js 15 with App Router
- `backend/` - FastAPI with proper module structure
- `infrastructure/` - Docker Compose files
- `docs/` - Project documentation

**And** all required tools are configured:
- TypeScript strict mode enabled
- ESLint + Prettier configured
- Python linting (ruff) configured
- Git hooks for pre-commit checks

**Prerequisites:** None (first story)

**Technical Notes:**
- Use `npx create-next-app@latest` with flags from architecture doc
- Use `npx shadcn@latest init` for component library
- Python 3.11 required (redis-py compatibility)
- Reference: [architecture.md](../architecture.md) Project Initialization section

---

## Story 1.2: Database Schema and Migration Setup

As a **developer**,
I want **the PostgreSQL database schema established with migrations**,
So that **data models are versioned and reproducible**.

**Acceptance Criteria:**

**Given** PostgreSQL is running via Docker Compose
**When** I run `alembic upgrade head`
**Then** all tables are created successfully

**And** the following tables exist:
- `users` (id, email, hashed_password, is_active, is_superuser, created_at, updated_at)
- `knowledge_bases` (id, name, description, owner_id, status, created_at, updated_at)
- `kb_permissions` (id, user_id, kb_id, permission_level, created_at)
- `documents` (id, kb_id, name, file_path, status, chunk_count, created_at, updated_at)
- `outbox` (id, event_type, aggregate_id, payload, created_at, processed_at, attempts, last_error)
- `audit.events` (id, timestamp, user_id, action, resource_type, resource_id, details, ip_address)

**And** audit schema has INSERT-only permissions for application role

**Prerequisites:** Story 1.1

**Technical Notes:**
- Use SQLAlchemy 2.0 async models
- Document status enum: PENDING, PROCESSING, READY, FAILED, ARCHIVED
- KB permission levels: READ, WRITE, ADMIN
- Reference: [architecture.md](../architecture.md) Data Architecture section

---

## Story 1.3: Docker Compose Development Environment

As a **developer**,
I want **a complete local development environment via Docker Compose**,
So that **all services can be started with a single command**.

**Acceptance Criteria:**

**Given** Docker and Docker Compose are installed
**When** I run `docker compose up -d`
**Then** all required services start successfully:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Qdrant (ports 6333, 6334)
- LiteLLM Proxy (port 4000)

**And** health checks pass for all services
**And** services persist data in named volumes
**And** `.env.example` documents all required environment variables

**Prerequisites:** Story 1.1

**Technical Notes:**
- Use official images with pinned versions
- Configure health checks for each service
- Network isolation between services
- Reference: [architecture.md](../architecture.md) Deployment Architecture section

---

## Story 1.4: User Registration and Authentication Backend

As a **user**,
I want **to create an account and log in securely**,
So that **I can access the LumiKB application**.

**Acceptance Criteria:**

**Given** I am on the registration endpoint
**When** I submit valid email and password
**Then** my account is created with hashed password (argon2)
**And** I receive a success response

**Given** I have an account
**When** I submit correct credentials to login endpoint
**Then** I receive a JWT token in an httpOnly cookie
**And** the session is stored in Redis

**Given** I am logged in
**When** I access a protected endpoint
**Then** my JWT is validated and request proceeds

**Given** I am logged in
**When** I call the logout endpoint
**Then** my session is invalidated in Redis
**And** the JWT cookie is cleared

**And** all authentication events are logged to audit.events (FR56)
**And** failed login attempts are rate-limited

**Prerequisites:** Story 1.2, Story 1.3

**Technical Notes:**
- Use FastAPI-Users with SQLAlchemy backend
- JWT expiry: 60 minutes (configurable)
- Password requirements: minimum 8 characters
- Reference: [architecture.md](../architecture.md) Security Architecture section

---

## Story 1.5: User Profile and Password Management Backend

As a **user**,
I want **to update my profile and reset my password**,
So that **I can manage my account information**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I call GET /api/v1/users/me
**Then** I receive my profile information (email, name, created_at)

**Given** I am logged in
**When** I call PATCH /api/v1/users/me with valid data
**Then** my profile is updated
**And** the change is logged to audit.events

**Given** I forgot my password
**When** I submit my email to password reset endpoint
**Then** a reset token is generated (expires in 1 hour)
**And** (mock) email would be sent with reset link

**Given** I have a valid reset token
**When** I submit a new password
**Then** my password is updated
**And** all existing sessions are invalidated
**And** the change is logged to audit.events

**Prerequisites:** Story 1.4

**Technical Notes:**
- Use FastAPI-Users built-in password reset flow
- Email sending is mocked for MVP (log to console)
- Reference: FR3, FR4

---

## Story 1.6: Admin User Management Backend

As an **administrator**,
I want **to manage user accounts**,
So that **I can control who has access to the system**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I call GET /api/v1/admin/users
**Then** I receive a paginated list of all users

**Given** I am logged in as an admin
**When** I call POST /api/v1/admin/users with valid data
**Then** a new user account is created
**And** the action is logged to audit.events

**Given** I am logged in as an admin
**When** I call PATCH /api/v1/admin/users/{id} to deactivate
**Then** the user's is_active flag is set to false
**And** the user cannot log in
**And** the action is logged to audit.events

**Given** I am NOT an admin
**When** I try to access admin endpoints
**Then** I receive 403 Forbidden

**Prerequisites:** Story 1.4

**Technical Notes:**
- Admin check via is_superuser flag
- Pagination: default 20 per page
- Reference: FR5, FR56

---

## Story 1.7: Audit Logging Infrastructure

As a **compliance officer**,
I want **all significant actions logged immutably**,
So that **we can demonstrate compliance and investigate issues**.

**Acceptance Criteria:**

**Given** any auditable action occurs (login, logout, user change, etc.)
**When** the action completes
**Then** an audit event is written to audit.events table

**And** each audit event contains:
- timestamp (UTC)
- user_id (if authenticated)
- action (e.g., "user.login", "user.created")
- resource_type and resource_id (if applicable)
- details (JSON with context)
- ip_address

**And** the audit_writer role can only INSERT (no UPDATE, DELETE)
**And** audit events are written via a dedicated AuditService

**Given** high request volume
**When** audit logging occurs
**Then** it does not significantly impact request latency (async write)

**Prerequisites:** Story 1.2

**Technical Notes:**
- Use structlog for structured logging
- Audit writes should be async (background task)
- Reference: FR53, FR56, FR57
- Reference: [architecture.md](../architecture.md) Audit Schema section

---

## Story 1.8: Frontend Authentication UI

As a **user**,
I want **a clean login and registration interface**,
So that **I can access LumiKB easily**.

**Acceptance Criteria:**

**Given** I navigate to /login
**When** the page loads
**Then** I see a login form with email and password fields
**And** the design follows the Trust Blue color theme

**Given** I enter valid credentials and submit
**When** authentication succeeds
**Then** I am redirected to the dashboard
**And** my session is established

**Given** I enter invalid credentials
**When** authentication fails
**Then** I see a clear error message
**And** the form is not cleared

**Given** I click "Create Account"
**When** the registration form loads
**Then** I can enter email and password
**And** validation shows password requirements

**Given** I am logged in
**When** I click logout
**Then** I am logged out and redirected to login page

**Prerequisites:** Story 1.4, Story 1.1

**Technical Notes:**
- Use shadcn/ui form components
- Client-side validation with react-hook-form
- Store auth state in Zustand
- Reference: [ux-design-specification.md](../ux-design-specification.md) Visual Foundation section

---

## Story 1.9: Three-Panel Dashboard Shell

As a **user**,
I want **to see the main application layout after login**,
So that **I understand how to navigate LumiKB**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I navigate to the dashboard
**Then** I see a three-panel layout:
- Left sidebar (260px): KB navigation area (placeholder)
- Center panel (flexible): Main content area with welcome message
- Right panel (320px): Citations panel (placeholder, collapsible)

**And** the header contains:
- LumiKB logo
- Search bar placeholder (disabled until Epic 3)
- User menu with profile and logout options

**And** the layout is responsive:
- Desktop (1280px+): Full three-panel
- Laptop (1024-1279px): Citations become tab
- Tablet (768-1023px): Sidebar in drawer
- Mobile (<768px): Single column with bottom nav

**And** dark mode toggle is available in user menu

**Prerequisites:** Story 1.8

**Technical Notes:**
- Use Tailwind CSS for responsive breakpoints
- Collapsible panels using Radix UI Collapsible
- Reference: [ux-design-specification.md](../ux-design-specification.md) Section 4 - Design Direction

---

## Story 1.10: Demo Knowledge Base Seeding

As a **first-time user**,
I want **to explore a sample Knowledge Base immediately**,
So that **I can understand LumiKB's value before uploading my own documents**.

**Acceptance Criteria:**

**Given** the system is freshly deployed
**When** the seed script runs
**Then** a "Sample Knowledge Base" is created
**And** it contains 3-5 demo documents (markdown files about LumiKB features)
**And** documents are processed and indexed in Qdrant

**Given** a new user logs in for the first time
**When** they view the KB list
**Then** they see "Sample Knowledge Base" with READ permission
**And** they can explore it immediately

**Given** the demo KB exists
**When** a user searches within it (after Epic 3)
**Then** they get meaningful results demonstrating the citation system

**Prerequisites:** Story 1.2, Story 1.3

**Technical Notes:**
- Seed script in `infrastructure/scripts/seed-data.sh`
- Demo docs stored in `infrastructure/seed/demo-docs/`
- Creates demo user if none exists (demo@lumikb.local / demo123)
- **Seeding Mechanism:** Uses direct Qdrant API to insert pre-computed embeddings (not the full processing pipeline from Epic 2). This allows demo data to exist before document processing is implemented.
- Pre-computed embeddings stored in `infrastructure/seed/demo-embeddings.json`
- This story sets up data; search functionality comes in Epic 3

---

## Summary

Epic 1 establishes the foundational infrastructure for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 1.1 | - | Project structure and tooling |
| 1.2 | - | Database schema and migrations |
| 1.3 | - | Docker Compose environment |
| 1.4 | - | User authentication backend |
| 1.5 | - | Profile and password management |
| 1.6 | - | Admin user management |
| 1.7 | - | Audit logging infrastructure |
| 1.8 | - | Authentication UI |
| 1.9 | - | Three-panel dashboard shell |
| 1.10 | - | Demo KB seeding |

**Total Stories:** 10

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
