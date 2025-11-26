# LumiKB - Epic Breakdown

**Author:** Tung Vu
**Date:** 2025-11-23
**Project Level:** Enterprise SaaS B2B Platform
**Target Scale:** MVP 1 - Internal Pilot (20+ users, 5000 documents)

---

## Overview

This document provides the complete epic and story breakdown for LumiKB, decomposing the requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version. Stories will be updated after implementation begins to incorporate technical discoveries and refinements.

**Design Principles Applied:**
- **Citation-first**: Every search/generate story includes citation acceptance criteria
- **User value per epic**: Each epic delivers demo-able capability
- **Risk front-loading**: Auth, audit, consistency patterns early
- **Journey alignment**: Epics map to user journeys (Sarah's RFP flow, David's contribution flow)
- **KISS**: 5 focused epics, combining related capabilities
- **Single-session stories**: Each story completable in one dev agent session

**Epic Summary:**

| Epic | Name | User Value | Story Count |
|------|------|------------|-------------|
| 1 | Foundation & Authentication | Login, explore sample KB with demo docs | 10 |
| 2 | Knowledge Base & Document Management | Create KBs, upload and process documents | 12 |
| 3 | Semantic Search & Citations | Search and get answers WITH citations | 11 |
| 4 | Chat & Document Generation | Chat, generate drafts with citations, export | 10 |
| 5 | Administration & Polish | Full admin dashboard, onboarding wizard | 11 (includes 2 technical debt) |

**Total Stories:** 54 (52 features + 2 technical debt)

---

## Functional Requirements Inventory

### User Account & Access (FR1-FR8)
- **FR1**: Users can create accounts with email and password
- **FR2**: Users can log in securely and maintain sessions
- **FR3**: Users can reset passwords via email verification
- **FR4**: Users can update their profile information
- **FR5**: Administrators can create, modify, and deactivate user accounts
- **FR6**: Administrators can assign users to Knowledge Bases with specific permissions
- **FR7**: Users can only access Knowledge Bases they have been granted permission to
- **FR8**: System enforces session timeout and secure logout
- **FR8a**: First-time users see an onboarding tutorial emphasizing citation verification
- **FR8b**: First-time users see a Getting Started wizard
- **FR8c**: System provides a sample Knowledge Base with demo documents

### Knowledge Base Management (FR9-FR14)
- **FR9**: Administrators can create new Knowledge Bases with name and description
- **FR10**: Administrators can configure KB-level settings (retention policy, access defaults)
- **FR10a**: Administrators can configure document processing settings per KB
- **FR11**: Administrators can archive or delete Knowledge Bases
- **FR12**: Users can view list of Knowledge Bases they have access to
- **FR12a**: Users can view KB summary information (document count, total size, last updated)
- **FR12b**: Administrators can view detailed KB statistics
- **FR12c**: System suggests relevant Knowledge Bases based on pasted content (Smart KB Suggestions)
- **FR12d**: Users can view recently accessed Knowledge Bases
- **FR13**: Users can switch between Knowledge Bases within a session
- **FR14**: Each Knowledge Base maintains isolated storage and vector indices

### Document Ingestion (FR15-FR23)
- **FR15**: Users with write permission can upload documents to a Knowledge Base
- **FR16**: System accepts PDF, DOCX, and Markdown file formats
- **FR17**: System processes uploaded documents: extraction, chunking, embedding
- **FR18**: Users can see upload progress and processing status
- **FR19**: System notifies users when document processing completes
- **FR20**: Users can view list of documents in a Knowledge Base
- **FR21**: Users can view document metadata (name, upload date, size, uploader)
- **FR22**: Users with write permission can delete documents from a Knowledge Base
- **FR23**: System removes deleted documents from storage and vector index completely
- **FR23a**: Users with write permission can re-upload/update existing documents
- **FR23b**: System supports incremental vector updates when documents are modified
- **FR23c**: System maintains document version awareness

### Semantic Search & Q&A (FR24-FR30)
- **FR24**: Users can ask natural language questions against a Knowledge Base
- **FR24a**: Users can perform Quick Search for simple lookups
- **FR24b**: Quick Search is accessible via always-visible search bar
- **FR24c**: Quick Search is accessible via keyboard shortcut (Cmd/Ctrl+K)
- **FR24d**: Users can set preference for default search mode
- **FR25**: System performs semantic search to find relevant document chunks
- **FR26**: System returns answers synthesized from retrieved content
- **FR27**: Every answer includes citations linking to source documents
- **FR27a**: Citations are displayed INLINE with answers (always visible)
- **FR28**: Users can click citations to view source document context
- **FR28a**: Users can access and view the original source document
- **FR28b**: System highlights the relevant paragraph/section in source
- **FR29**: Users can search across multiple Knowledge Bases simultaneously
- **FR29a**: Cross-KB search is the DEFAULT behavior
- **FR30**: System displays confidence/relevance indicators for search results
- **FR30a**: System explains WHY each result is relevant
- **FR30b**: Users can perform quick actions on search results
- **FR30c**: Confidence indicators are ALWAYS shown for AI-generated content
- **FR30d**: Users can click "Verify All" to see all citations at once
- **FR30e**: Users can filter results to "Search within current KB"
- **FR30f**: System displays citation accuracy score

### Chat Interface (FR31-FR35)
- **FR31**: Users can engage in multi-turn conversations with the system
- **FR32**: System maintains conversation context within a session
- **FR33**: Users can start new conversation threads
- **FR34**: Users can view conversation history within current session
- **FR35**: System clearly distinguishes AI-generated content from quoted sources
- **FR35a**: System streams AI responses in real-time (word-by-word)
- **FR35b**: Users can see typing/thinking indicators

### Document Generation Assist (FR36-FR42)
- **FR36**: Users can request AI assistance to generate document drafts
- **FR37**: System supports generation of: RFP/RFI responses, questionnaires, checklists, gap analysis
- **FR38**: Generated content includes citations to source documents used
- **FR39**: Users can edit generated content before exporting
- **FR40**: Users can export generated documents in common formats (DOCX, PDF, MD)
- **FR40a**: Exported documents preserve citations and formatting accurately
- **FR40b**: System prompts "Have you verified the sources?" before export
- **FR41**: System allows users to provide context/instructions for generation
- **FR42**: Users can regenerate content with modified instructions
- **FR42a**: System displays generation progress and streams draft content
- **FR42b**: Upon completion, system shows summary of sources used
- **FR42c**: Users can provide feedback on generation quality
- **FR42d**: System offers alternative approaches when generation fails
- **FR42e**: System highlights low-confidence sections

### Citation & Provenance (FR43-FR46)
- **FR43**: Every AI-generated statement traces back to source document(s)
- **FR44**: Citations include document name, section, and page/location reference
- **FR45**: Users can preview cited source content without leaving current view
- **FR46**: System logs all sources used in each generation request

### Administration & Configuration (FR47-FR52)
- **FR47**: Administrators can view system-wide usage statistics
- **FR48**: Administrators can view audit logs with filters (user, action, date range)
- **FR49**: Administrators can export audit logs for compliance reporting
- **FR50**: Administrators can configure LLM provider settings
- **FR51**: Administrators can configure system-wide defaults
- **FR52**: Administrators can view and manage processing queue status

### Audit & Compliance (FR53-FR58)
- **FR53**: System logs every document upload with user, timestamp, and metadata
- **FR54**: System logs every search query with user, timestamp, and results summary
- **FR55**: System logs every generation request with user, timestamp, prompt, and sources
- **FR56**: System logs every user management action
- **FR57**: Audit logs are immutable and tamper-evident
- **FR58**: System supports configurable data retention policies per Knowledge Base

---

## FR Coverage Map

| Epic | FRs Covered | Coverage Summary |
|------|-------------|------------------|
| **Epic 1: Foundation & Authentication** | FR1-8, FR53 (infra), FR56-57 (infra) | Auth, sessions, audit infrastructure, demo KB |
| **Epic 2: KB & Document Management** | FR9-14, FR15-23, FR23a-c, FR53 | KB CRUD, document upload/processing pipeline |
| **Epic 3: Semantic Search & Citations** | FR24-30, FR24a-d, FR27a, FR28a-b, FR29a, FR30a-f, FR43-46, FR54 | Search, retrieval, citation system |
| **Epic 4: Chat & Document Generation** | FR31-35, FR35a-b, FR36-42, FR42a-e, FR55 | Chat interface, generation, export |
| **Epic 5: Administration & Polish** | FR47-52, FR58, FR8a-c, FR12b, FR12c-d | Admin dashboard, onboarding, audit UI |

---

## Epic 1: Foundation & Authentication

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

### Story 1.1: Project Initialization and Repository Setup

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
- Reference: [architecture.md](./architecture.md) Project Initialization section

---

### Story 1.2: Database Schema and Migration Setup

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
- Reference: [architecture.md](./architecture.md) Data Architecture section

---

### Story 1.3: Docker Compose Development Environment

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
- Reference: [architecture.md](./architecture.md) Deployment Architecture section

---

### Story 1.4: User Registration and Authentication Backend

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
- Reference: [architecture.md](./architecture.md) Security Architecture section

---

### Story 1.5: User Profile and Password Management Backend

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

### Story 1.6: Admin User Management Backend

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

### Story 1.7: Audit Logging Infrastructure

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
- Reference: [architecture.md](./architecture.md) Audit Schema section

---

### Story 1.8: Frontend Authentication UI

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
- Reference: [ux-design-specification.md](./ux-design-specification.md) Visual Foundation section

---

### Story 1.9: Three-Panel Dashboard Shell

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
- Reference: [ux-design-specification.md](./ux-design-specification.md) Section 4 - Design Direction

---

### Story 1.10: Demo Knowledge Base Seeding

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

## Epic 2: Knowledge Base & Document Management

**Goal:** Enable users to create Knowledge Bases and upload documents that are processed, chunked, and indexed for semantic search.

**User Value:** "I can create my own Knowledge Base, upload my documents, and see them processed and ready for search."

**FRs Covered:** FR9-14, FR15-23, FR23a-c, FR53

**Technical Foundation:**
- MinIO for document storage
- Celery workers for async processing
- unstructured for document parsing
- LangChain for chunking
- Qdrant for vector storage
- Outbox pattern for consistency

---

### Story 2.1: Knowledge Base CRUD Backend

As an **administrator**,
I want **to create and manage Knowledge Bases**,
So that **I can organize documents into logical collections**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I call POST /api/v1/knowledge-bases with name and description
**Then** a new Knowledge Base is created
**And** a corresponding Qdrant collection is created (kb_{id})
**And** I am assigned ADMIN permission on the KB
**And** the action is logged to audit.events

**Given** a KB exists
**When** I call GET /api/v1/knowledge-bases/{id}
**Then** I receive KB details including document count and status

**Given** I have ADMIN permission on a KB
**When** I call PATCH /api/v1/knowledge-bases/{id}
**Then** the KB name/description is updated

**Given** I have ADMIN permission on a KB
**When** I call DELETE /api/v1/knowledge-bases/{id}
**Then** the KB status is set to ARCHIVED
**And** it no longer appears in normal listings
**And** the Qdrant collection is deleted

**Prerequisites:** Story 1.2, Story 1.7

**Technical Notes:**
- Soft delete (ARCHIVED status) for audit trail
- Collection naming: `kb_{uuid}`
- Reference: FR9, FR10, FR11, FR14

---

### Story 2.2: Knowledge Base Permissions Backend

As an **administrator**,
I want **to assign users to Knowledge Bases with specific permissions**,
So that **I can control who can read, write, or manage each KB**.

**Acceptance Criteria:**

**Given** I have ADMIN permission on a KB
**When** I call POST /api/v1/knowledge-bases/{id}/permissions
**Then** the specified user is granted the specified permission level
**And** the action is logged to audit.events

**Given** a user has READ permission on a KB
**When** they try to upload a document
**Then** they receive 403 Forbidden

**Given** a user has WRITE permission on a KB
**When** they try to delete the KB
**Then** they receive 403 Forbidden

**Given** a user has no permission on a KB
**When** they try to access it
**Then** they receive 404 Not Found (not 403, to avoid leaking existence)

**And** permission levels are: READ, WRITE, ADMIN
**And** ADMIN includes WRITE includes READ

**Prerequisites:** Story 2.1

**Technical Notes:**
- Permission check middleware on all KB endpoints
- Use 404 for unauthorized access (security through obscurity)
- Reference: FR6, FR7

---

### Story 2.3: Knowledge Base List and Selection Frontend

As a **user**,
I want **to see and switch between Knowledge Bases I have access to**,
So that **I can work with different document collections**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I view the sidebar
**Then** I see a list of Knowledge Bases I have access to
**And** each shows name, document count, and my permission level icon

**Given** multiple KBs exist
**When** I click on a different KB
**Then** it becomes the active KB
**And** the center panel updates to show that KB's context

**Given** I have ADMIN permission
**When** I click "Create Knowledge Base"
**Then** a modal appears with name and description fields
**And** I can create a new KB

**And** the sidebar shows my permission level for each KB:
- 👁 READ
- ✏️ WRITE
- ⚙️ ADMIN

**Prerequisites:** Story 2.1, Story 1.9

**Technical Notes:**
- Use KBSelectorItem component from UX spec
- Store active KB in Zustand
- Reference: FR12, FR12a, FR13

---

### Story 2.4: Document Upload API and Storage

As a **user with WRITE permission**,
I want **to upload documents to a Knowledge Base**,
So that **they can be processed and made searchable**.

**Acceptance Criteria:**

**Given** I have WRITE permission on a KB
**When** I call POST /api/v1/knowledge-bases/{id}/documents with a file
**Then** the file is uploaded to MinIO (bucket: kb-{id})
**And** a document record is created with status PENDING
**And** an outbox event is created for processing
**And** I receive 202 Accepted with document ID

**And** supported formats are: PDF, DOCX, MD (FR16)
**And** maximum file size is 50MB
**And** the upload is logged to audit.events (FR53)

**Given** I upload an unsupported file type
**When** validation runs
**Then** I receive 400 Bad Request with clear error message

**Prerequisites:** Story 2.2, Story 1.3 (MinIO)

**Technical Notes:**
- Use MinIO Python client
- Chunked upload for large files
- File stored as: `{kb_id}/{doc_id}/{original_filename}`
- Reference: FR15, FR16, FR53

---

### Story 2.5: Document Processing Worker - Parsing

As a **system**,
I want **to parse uploaded documents and extract text**,
So that **content can be chunked and embedded**.

**Acceptance Criteria:**

**Given** a document is in PENDING status
**When** the Celery worker picks up the processing event
**Then** the document status is updated to PROCESSING
**And** the file is downloaded from MinIO
**And** text is extracted using unstructured library

**Given** a PDF document
**When** parsing completes
**Then** text content and page numbers are extracted

**Given** a DOCX document
**When** parsing completes
**Then** text content and section headers are extracted

**Given** a Markdown document
**When** parsing completes
**Then** text content and heading structure are extracted

**Given** parsing fails
**When** max retries (3) are exhausted
**Then** document status is set to FAILED
**And** last_error contains the failure reason

**Prerequisites:** Story 2.4

**Technical Notes:**
- Use unstructured library with appropriate loaders
- Extract metadata: page_number, section_header where available
- Store parsed content temporarily for chunking step
- Reference: FR17

---

### Story 2.6: Document Processing Worker - Chunking and Embedding

As a **system**,
I want **to chunk parsed documents and generate embeddings**,
So that **content can be searched semantically**.

**Acceptance Criteria:**

**Given** a document has been parsed successfully
**When** the chunking step runs
**Then** text is split into semantic chunks (target: 500 tokens, overlap: 50)
**And** each chunk retains metadata (document_id, page, section, char_start, char_end)

**Given** chunks are created
**When** the embedding step runs
**Then** embeddings are generated via LiteLLM
**And** vectors are stored in Qdrant collection (kb_{kb_id})

**And** each Qdrant point includes payload:
- document_id
- document_name
- page_number (if available)
- section_header (if available)
- chunk_text
- char_start, char_end

**Given** all steps complete successfully
**When** the worker finishes
**Then** document status is set to READY
**And** chunk_count is updated on the document record

**Prerequisites:** Story 2.5

**Technical Notes:**
- Use LangChain RecursiveCharacterTextSplitter
- Embedding model configured via LiteLLM (default: text-embedding-ada-002)
- Rich metadata is CRITICAL for citation system
- Reference: FR17, FR43, FR44

---

### Story 2.7: Document Processing Status and Notifications

As a **user**,
I want **to see the status of my uploaded documents**,
So that **I know when they're ready for search**.

**Acceptance Criteria:**

**Given** I uploaded a document
**When** I view the KB document list
**Then** I see the document with its current status:
- PENDING: "Queued for processing"
- PROCESSING: "Processing..." with spinner
- READY: "Ready" with green checkmark
- FAILED: "Failed" with error icon and retry option

**Given** a document finishes processing
**When** status changes to READY or FAILED
**Then** a toast notification appears (if user is on the page)

**Given** a document is READY
**When** I view it in the list
**Then** I see chunk count (e.g., "47 chunks indexed")

**Prerequisites:** Story 2.6, Story 2.3

**Technical Notes:**
- Poll for status updates every 5 seconds while PROCESSING
- Use toast component from shadcn/ui
- Reference: FR18, FR19

---

### Story 2.8: Document List and Metadata View

As a **user**,
I want **to view all documents in a Knowledge Base**,
So that **I can see what content is available**.

**Acceptance Criteria:**

**Given** I have access to a KB
**When** I view the KB detail page
**Then** I see a list of all documents with:
- Document name
- Upload date (relative: "2 hours ago")
- File size
- Uploader name
- Status badge
- Chunk count (if READY)

**And** the list is paginated (20 per page)
**And** I can sort by name, date, or size

**Given** I click on a document
**When** the detail view opens
**Then** I see full metadata including:
- Original filename
- MIME type
- Processing duration
- Last error (if FAILED)

**Prerequisites:** Story 2.7

**Technical Notes:**
- Use date-fns formatDistanceToNow for relative dates
- Reference: FR20, FR21

---

### Story 2.9: Document Upload Frontend

As a **user with WRITE permission**,
I want **to upload documents via drag-and-drop or file picker**,
So that **I can easily add content to a Knowledge Base**.

**Acceptance Criteria:**

**Given** I have WRITE permission on the active KB
**When** I drag a file onto the upload zone
**Then** the zone highlights to indicate drop target
**And** releasing the file starts the upload

**Given** I click the upload zone
**When** the file picker opens
**Then** I can select one or more files
**And** only supported formats are selectable

**Given** upload is in progress
**When** I view the upload zone
**Then** I see a progress bar for each file
**And** I can cancel pending uploads

**Given** upload completes
**When** the response returns
**Then** the document appears in the list with PENDING status
**And** I see a success toast

**Prerequisites:** Story 2.4, Story 2.8

**Technical Notes:**
- Use react-dropzone for drag-and-drop
- Chunked upload for files > 5MB
- Reference: FR15, FR18

---

### Story 2.10: Document Deletion

As a **user with WRITE permission**,
I want **to delete documents from a Knowledge Base**,
So that **I can remove outdated or incorrect content**.

**Acceptance Criteria:**

**Given** I have WRITE permission on a KB
**When** I click delete on a document
**Then** a confirmation dialog appears

**Given** I confirm deletion
**When** the delete request completes
**Then** the document status is set to ARCHIVED
**And** an outbox event is created for cleanup
**And** the action is logged to audit.events

**Given** a document is deleted
**When** the cleanup worker runs
**Then** vectors are removed from Qdrant
**And** file is removed from MinIO
**And** document no longer appears in listings or search results

**Prerequisites:** Story 2.6, Story 2.8

**Technical Notes:**
- Soft delete first (status = ARCHIVED), then async cleanup
- Outbox ensures cleanup completes even if initial request fails
- Reference: FR22, FR23

---

### Story 2.11: Outbox Processing and Reconciliation

As a **system**,
I want **reliable cross-service operations via the outbox pattern**,
So that **document state remains consistent across PostgreSQL, MinIO, and Qdrant**.

**Acceptance Criteria:**

**Given** events exist in the outbox table
**When** the outbox worker runs (every 10 seconds)
**Then** unprocessed events are picked up and executed
**And** processed_at is set on successful completion
**And** attempts is incremented on failure

**Given** an event fails repeatedly
**When** attempts reaches 5
**Then** the event is marked as failed
**And** an alert is logged

**Given** the reconciliation job runs (hourly)
**When** it detects inconsistencies:
- Documents in READY status without vectors
- Vectors without corresponding document records
- Files in MinIO without document records
**Then** it logs the inconsistency and creates correction events

**Prerequisites:** Story 2.6

**Technical Notes:**
- Use Celery Beat for scheduled jobs
- Reconciliation is defensive - logs and alerts, doesn't auto-fix
- Reference: [architecture.md](./architecture.md) Transactional Outbox section

---

### Story 2.12: Document Re-upload and Version Awareness

As a **user with WRITE permission**,
I want **to re-upload an updated version of a document**,
So that **the Knowledge Base stays current**.

**Acceptance Criteria:**

**Given** a document exists in the KB
**When** I upload a file with the same name
**Then** I am prompted: "Replace existing document?"

**Given** I confirm replacement
**When** the upload completes
**Then** the old vectors are removed from Qdrant
**And** the new file replaces the old in MinIO
**And** the document is reprocessed
**And** updated_at timestamp is set

**Given** the replacement is in progress
**When** someone searches
**Then** search uses the old vectors until new processing completes
**And** then atomically switches to new vectors

**Prerequisites:** Story 2.9, Story 2.6

**Technical Notes:**
- Atomic switch: process new vectors, then delete old in single operation
- Consider using versioned point IDs in Qdrant
- Reference: FR23a, FR23b, FR23c

---

## Epic 3: Semantic Search & Citations

**Goal:** Enable users to search their Knowledge Bases with natural language and receive answers with inline citations linking to source documents.

**User Value:** "I can ask questions and get answers with citations I can trust - this is THE magic moment."

**FRs Covered:** FR24-30, FR24a-d, FR27a, FR28a-b, FR29a, FR30a-f, FR43-46, FR54

**Technical Foundation:**
- Qdrant semantic search
- LiteLLM for answer synthesis
- CitationService for source tracking
- SSE for streaming responses

---

### Story 3.1: Semantic Search Backend

As a **user**,
I want **to search my Knowledge Base with natural language**,
So that **I can find relevant information quickly**.

**Acceptance Criteria:**

**Given** I have access to a KB with documents
**When** I call POST /api/v1/search with a query and kb_id
**Then** the query is embedded using the same model as documents
**And** semantic search is performed against Qdrant
**And** top-k results (default: 10) are returned

**And** each result includes:
- document_id, document_name
- chunk_text (the relevant passage)
- page_number, section_header (if available)
- relevance_score (0-1)

**And** the search is logged to audit.events (FR54)

**Given** no relevant results exist
**When** search completes
**Then** empty results array is returned with helpful message

**Prerequisites:** Story 2.6

**Technical Notes:**
- Use langchain-qdrant QdrantVectorStore
- Relevance score from Qdrant distance metric
- Reference: FR24, FR25, FR54

---

### Story 3.2: Answer Synthesis with Citations Backend

As a **user**,
I want **search results synthesized into a coherent answer with citations**,
So that **I get direct answers rather than just document links**.

**Acceptance Criteria:**

**Given** search returns relevant chunks
**When** answer synthesis is requested
**Then** chunks are passed to LLM with citation instructions
**And** LLM generates an answer using [1], [2], etc. markers
**And** CitationService extracts markers and maps to source chunks

**And** the response includes:
- answer_text (with inline citation markers)
- citations array with full metadata per marker
- confidence_score (based on retrieval relevance)

**Given** the LLM response contains [1]
**When** citation extraction runs
**Then** citation 1 maps to the first source chunk used
**And** includes: document_name, page, section, excerpt, char_start, char_end

**And** confidence indicators are calculated based on:
- Retrieval relevance scores
- Number of supporting sources
- Query-answer semantic similarity

**Prerequisites:** Story 3.1

**Technical Notes:**
- System prompt instructs LLM to cite every claim
- CitationService is THE core differentiator - test thoroughly
- Reference: FR26, FR27, FR43, FR44, FR30c

---

### Story 3.3: Search API Streaming Response

As a **user**,
I want **search results to stream in real-time**,
So that **I see answers faster and feel the system is responsive**.

**Acceptance Criteria:**

**Given** I call the search endpoint with stream=true
**When** processing begins
**Then** SSE connection is established
**And** events stream as they're generated:
- `{"type": "status", "content": "Searching..."}`
- `{"type": "token", "content": "OAuth"}` (answer tokens)
- `{"type": "citation", "data": {...}}` (when citation marker parsed)
- `{"type": "done", "confidence": 0.85}`

**Given** streaming is in progress
**When** a citation marker [n] is detected
**Then** a citation event is immediately sent with full metadata
**And** the frontend can display the citation inline

**Given** an error occurs during streaming
**When** the error is caught
**Then** an error event is sent
**And** the connection is closed gracefully

**Prerequisites:** Story 3.2

**Technical Notes:**
- Use FastAPI StreamingResponse with SSE
- Parse tokens as they stream to detect [n] patterns
- Reference: FR35a (applies to search too)

---

### Story 3.4: Search Results UI with Inline Citations

As a **user**,
I want **to see search results with visible inline citations**,
So that **I can trust and verify the answers**.

**Acceptance Criteria:**

**Given** I submit a search query
**When** results stream in
**Then** the answer appears word-by-word in the center panel
**And** citation markers [1], [2] appear inline as blue clickable badges

**Given** an answer is displayed
**When** I view the citations panel (right side)
**Then** I see a card for each citation with:
- Citation number
- Document name
- Page/section reference
- Excerpt preview (truncated)
- "Preview" and "Open" buttons

**And** the confidence indicator shows:
- Green bar (80-100%): High confidence
- Amber bar (50-79%): Medium confidence
- Red bar (0-49%): Low confidence

**And** confidence is ALWAYS shown (FR30c)

**Prerequisites:** Story 3.3, Story 1.9

**Technical Notes:**
- Use CitationMarker and CitationCard components from UX spec
- Use ConfidenceIndicator component
- Reference: FR27a, FR30, FR30c

---

### Story 3.5: Citation Preview and Source Navigation

As a **user**,
I want **to preview and navigate to cited sources**,
So that **I can verify the information without losing context**.

**Acceptance Criteria:**

**Given** an answer has citations displayed
**When** I hover over a citation marker [1]
**Then** a tooltip shows the source title and excerpt snippet

**Given** I click a citation marker
**When** the citation panel scrolls
**Then** the corresponding CitationCard is highlighted

**Given** I click "Preview" on a CitationCard
**When** the preview opens
**Then** I see the cited passage with the relevant text highlighted
**And** I can scroll to see surrounding context

**Given** I click "Open Document"
**When** the document viewer opens
**Then** the full document is shown
**And** it scrolls to and highlights the cited passage (FR28b)

**Prerequisites:** Story 3.4

**Technical Notes:**
- Preview in modal/sheet, document in new tab or full panel
- Use char_start/char_end from citation metadata for highlighting
- Reference: FR28, FR28a, FR28b, FR45

---

### Story 3.6: Cross-KB Search

As a **user**,
I want **to search across all my Knowledge Bases at once**,
So that **I can find information regardless of where it's stored**.

**Acceptance Criteria:**

**Given** I have access to multiple KBs
**When** I search without specifying a KB (default)
**Then** search runs against ALL my permitted KBs
**And** results are merged and ranked by relevance

**And** each result shows which KB it came from
**And** I can filter results by KB after viewing

**Given** I want to search a specific KB
**When** I use the "Search within current KB" filter
**Then** only that KB is searched

**And** cross-KB search is the DEFAULT (FR29a)

**Prerequisites:** Story 3.1, Story 2.2

**Technical Notes:**
- Query multiple Qdrant collections in parallel
- Permission check per collection
- Merge and re-rank results by score
- Reference: FR29, FR29a, FR30e

---

### Story 3.7: Quick Search and Command Palette

As a **user**,
I want **to quickly search via keyboard shortcut**,
So that **I can find information without leaving my current context**.

**Acceptance Criteria:**

**Given** I am anywhere in the application
**When** I press Cmd/Ctrl+K
**Then** a command palette overlay appears
**And** focus is in the search input

**Given** the command palette is open
**When** I type a query and press Enter
**Then** quick search results appear in the palette
**And** I can select a result with arrow keys

**Given** I select a result
**When** I press Enter
**Then** the full search view opens with that result highlighted

**Given** I press Escape
**When** the palette is open
**Then** it closes and focus returns to previous element

**Prerequisites:** Story 3.4

**Technical Notes:**
- Use shadcn/ui Command component (Radix Dialog + cmdk)
- Quick search uses same backend, limited to top 5 results
- Reference: FR24a, FR24b, FR24c

---

### Story 3.8: Search Result Actions

As a **user**,
I want **quick actions on search results**,
So that **I can efficiently work with found information**.

**Acceptance Criteria:**

**Given** a search result is displayed
**When** I view the result card
**Then** I see action buttons:
- "Use in Draft" (prepares for generation)
- "View" (opens document)
- "Similar" (finds similar content)

**Given** I click "Use in Draft"
**When** the action completes
**Then** the result is marked for use in document generation
**And** a badge appears showing "Selected for draft"

**Given** I click "Similar"
**When** the search runs
**Then** results similar to that chunk are displayed
**And** the original query is replaced with "Similar to: [title]"

**Prerequisites:** Story 3.4

**Technical Notes:**
- "Similar" uses the chunk embedding for similarity search
- "Use in Draft" stores selection in session state
- Reference: FR30b

---

### Story 3.9: Relevance Explanation

As a **user**,
I want **to understand WHY a result is relevant**,
So that **I can trust the search quality**.

**Acceptance Criteria:**

**Given** search results are displayed
**When** I view a result card
**Then** I see a "Relevant because:" section explaining:
- Key matching terms/concepts
- Semantic similarity factors
- Source document context

**Given** I want more detail
**When** I expand the explanation
**Then** I see:
- Matching keywords highlighted
- Semantic distance score
- Other documents this relates to

**Prerequisites:** Story 3.4

**Technical Notes:**
- Generate explanation via LLM based on query + chunk
- Cache explanations to avoid repeated LLM calls
- Reference: FR30a

---

### Story 3.10: Verify All Citations

As a **skeptical user**,
I want **to verify all citations in sequence**,
So that **I can systematically check the AI's sources**.

**Acceptance Criteria:**

**Given** an answer has multiple citations
**When** I click "Verify All" button
**Then** verification mode activates
**And** the first citation is highlighted in both answer and panel

**Given** verification mode is active
**When** I click "Next" or press arrow key
**Then** the next citation is highlighted
**And** the preview automatically shows that citation's source

**Given** I verify a citation
**When** I click the checkmark
**Then** a green "Verified" badge appears on that citation
**And** verification progress shows (e.g., "3/7 verified")

**Given** I've verified all citations
**When** I complete the sequence
**Then** "All sources verified" message appears
**And** a summary badge shows on the answer

**Prerequisites:** Story 3.5

**Technical Notes:**
- Track verification state in component state
- Persist verified state for session duration
- Reference: FR30d

---

## Epic 4: Chat & Document Generation

**Goal:** Enable users to have multi-turn conversations and generate document drafts with citations that can be exported.

**User Value:** "I can chat with my knowledge, generate drafts for RFP responses, and export them with citations - the 80% draft in 30 seconds magic moment."

**FRs Covered:** FR31-35, FR35a-b, FR36-42, FR42a-e, FR55

**Technical Foundation:**
- Conversation context management
- LLM streaming with citation tracking
- Document export (DOCX, PDF, MD)
- Generation templates

---

### Story 4.1: Chat Conversation Backend

As a **user**,
I want **to have multi-turn conversations with my Knowledge Base**,
So that **I can explore topics in depth**.

**Acceptance Criteria:**

**Given** I have an active KB
**When** I call POST /api/v1/chat with a message
**Then** the system performs RAG (retrieval + generation)
**And** response includes answer with citations
**And** conversation context is stored in Redis

**Given** I send a follow-up message
**When** the chat endpoint processes it
**Then** previous messages are included as context
**And** the response is contextually aware

**And** conversation context includes:
- Previous messages (up to token limit)
- Retrieved chunks from each turn
- Generated responses

**Prerequisites:** Story 3.2

**Technical Notes:**
- Store conversation in Redis with session key
- Token limit: ~4000 for context, reserve rest for response
- Reference: FR31, FR32

---

### Story 4.2: Chat Streaming UI

As a **user**,
I want **to see chat responses stream in real-time**,
So that **the conversation feels natural and responsive**.

**Acceptance Criteria:**

**Given** I am in the chat interface
**When** I send a message
**Then** my message appears immediately on the right
**And** a "thinking" indicator appears for the AI

**Given** the AI is responding
**When** tokens stream in
**Then** they appear word-by-word in the chat bubble
**And** citation markers appear inline as they're generated
**And** citations populate in the right panel in real-time

**And** user messages have:
- Primary color background
- Right alignment
- Timestamp

**And** AI messages have:
- Surface color background
- Left alignment
- Inline citations
- Confidence indicator

**Prerequisites:** Story 4.1, Story 3.4

**Technical Notes:**
- Use ChatMessage component from UX spec
- SSE for streaming
- Reference: FR35, FR35a, FR35b

---

### Story 4.3: Conversation Management

As a **user**,
I want **to manage my conversation threads**,
So that **I can start fresh or continue previous work**.

**Acceptance Criteria:**

**Given** I am in the chat interface
**When** I click "New Chat"
**Then** a new conversation starts
**And** previous context is cleared

**Given** I have an active conversation
**When** I view the conversation history
**Then** I see all messages from the current session
**And** I can scroll through previous exchanges

**Given** I want to clear history
**When** I click "Clear Chat"
**Then** a confirmation appears
**And** confirming clears all messages
**And** undo is available for 30 seconds

**Prerequisites:** Story 4.2

**Technical Notes:**
- Conversations are session-scoped (not persisted to DB for MVP)
- Reference: FR33, FR34

---

### Story 4.4: Document Generation Request

As a **user**,
I want **to request AI-generated document drafts**,
So that **I can quickly create RFP responses and other artifacts**.

**Acceptance Criteria:**

**Given** I have search results or chat context
**When** I click "Generate Draft"
**Then** a generation modal appears with options:
- Document type dropdown (RFP Response, Checklist, Gap Analysis, Custom)
- Context/instructions textarea
- Source selection (use current results or specify)

**Given** I select document type and add context
**When** I click "Generate"
**Then** generation begins with progress indicator
**And** progress shows which sources are being used
**And** draft streams in with inline citations

**And** the request is logged to audit.events (FR55)

**Prerequisites:** Story 4.1, Story 3.8

**Technical Notes:**
- Document type determines prompt template
- Use selected results from Story 3.8 if available
- Reference: FR36, FR37, FR41, FR55

---

### Story 4.5: Draft Generation Streaming

As a **user**,
I want **to see my draft generate in real-time**,
So that **I can see progress and the draft feels responsive**.

**Acceptance Criteria:**

**Given** generation is in progress
**When** content streams
**Then** the draft appears in an editor panel
**And** citation markers [1], [2] appear inline
**And** a progress bar shows estimated completion

**Given** a section has low confidence
**When** it's generated
**Then** it's highlighted with amber background
**And** a note appears: "Review suggested - lower confidence"

**Given** generation completes
**When** the final token arrives
**Then** "Done" event fires
**And** summary appears: "Draft ready! Based on 5 sources from 3 documents"
**And** all citations are populated in the panel

**Prerequisites:** Story 4.4

**Technical Notes:**
- Use DraftSection component from UX spec
- Confidence calculated per section based on source coverage
- Reference: FR42a, FR42b, FR42e

---

### Story 4.6: Draft Editing

As a **user**,
I want **to edit the generated draft before exporting**,
So that **I can refine and customize the content**.

**Acceptance Criteria:**

**Given** a draft is generated
**When** I click in the draft area
**Then** I can edit the text directly
**And** citation markers remain intact unless deleted

**Given** I'm editing
**When** I delete a citation marker
**Then** it's removed from the text
**And** the citation panel updates accordingly

**Given** I want to regenerate a section
**When** I select text and click "Regenerate"
**Then** that section is regenerated
**And** the rest of the draft is preserved

**Prerequisites:** Story 4.5

**Technical Notes:**
- Use contenteditable or lightweight editor
- Track citation markers as special spans
- Reference: FR39, FR42

---

### Story 4.7: Document Export

As a **user**,
I want **to export my draft in common formats**,
So that **I can use it in my workflow**.

**Acceptance Criteria:**

**Given** a draft exists
**When** I click "Export"
**Then** I see format options: DOCX, PDF, Markdown

**Given** I select DOCX
**When** export completes
**Then** the document downloads
**And** citations appear as footnotes or inline references
**And** formatting is preserved (headers, lists, etc.)

**Given** I select PDF
**When** export completes
**Then** the PDF downloads with proper formatting
**And** citations are rendered appropriately

**Given** I select Markdown
**When** export completes
**Then** the .md file downloads
**And** citations are formatted as [^1] footnotes

**And** before any export, a prompt appears: "Have you verified the sources?" (FR40b)

**Prerequisites:** Story 4.6

**Technical Notes:**
- Use python-docx for DOCX
- Use weasyprint or reportlab for PDF
- Reference: FR40, FR40a, FR40b

---

### Story 4.8: Generation Feedback and Recovery

As a **user**,
I want **to provide feedback when generation doesn't meet my needs**,
So that **I can get better results**.

**Acceptance Criteria:**

**Given** a draft is generated
**When** I'm not satisfied
**Then** I can click "This doesn't look right"
**And** a feedback modal appears

**Given** I provide feedback
**When** I submit
**Then** alternative approaches are offered:
- "Try different sources" (searches again)
- "Use template" (starts from structured template)
- "Regenerate with feedback" (includes my feedback as instruction)

**Given** generation fails
**When** error is detected
**Then** user sees friendly error message
**And** recovery options are presented
**And** they can try again or fall back to template

**Prerequisites:** Story 4.5

**Technical Notes:**
- Log feedback for future improvements
- Reference: FR42c, FR42d

---

### Story 4.9: Generation Templates

As a **user**,
I want **pre-built templates for common document types**,
So that **I can generate consistent, well-structured drafts**.

**Acceptance Criteria:**

**Given** I select a document type
**When** generation starts
**Then** the appropriate template structures the output:

**RFP Response:**
- Executive Summary
- Technical Approach
- Relevant Experience
- Pricing (placeholder)

**Checklist:**
- Numbered requirements
- Status column
- Notes column

**Gap Analysis:**
- Requirement
- Current State
- Gap Identified
- Recommendation

**And** each template section includes citations from relevant sources

**Prerequisites:** Story 4.4

**Technical Notes:**
- Templates as prompt engineering
- Reference: FR37

---

### Story 4.10: Generation Audit Logging

As a **compliance officer**,
I want **all generation requests logged with full context**,
So that **we can audit AI-assisted content creation**.

**Acceptance Criteria:**

**Given** a generation request is made
**When** generation completes (or fails)
**Then** an audit event is logged with:
- user_id
- document_type
- prompt/instructions provided
- source_documents used (list of doc IDs)
- citation_count
- generation_time_ms
- success/failure status

**And** the full generated content is NOT stored in audit (privacy)
**And** source document references ARE stored (provenance)

**Prerequisites:** Story 4.4, Story 1.7

**Technical Notes:**
- Log sources, not content
- Reference: FR55, FR46

---

## Epic 5: Administration & Polish

**Goal:** Provide administrators with system management capabilities and polish the user experience with onboarding and refinements.

**User Value:** "Administrators can fully manage the system, and new users have a delightful onboarding experience."

**FRs Covered:** FR47-52, FR58, FR8a-c, FR12b, FR12c-d

**Technical Foundation:**
- Admin dashboard
- Audit log viewer
- Onboarding wizard
- UX polish items

---

### Story 5.1: Admin Dashboard Overview

As an **administrator**,
I want **to see system-wide statistics at a glance**,
So that **I can monitor system health and usage**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to /admin
**Then** I see a dashboard with:
- Total users (active/inactive)
- Total Knowledge Bases
- Total documents (by status)
- Storage usage
- Search queries (last 24h, 7d, 30d)
- Generation requests (last 24h, 7d, 30d)

**And** key metrics have sparkline charts showing trends
**And** I can click any metric to see details

**Prerequisites:** Story 1.6

**Technical Notes:**
- Aggregate queries with caching (refresh every 5 min)
- Reference: FR47

---

### Story 5.2: Audit Log Viewer

As an **administrator**,
I want **to view and filter audit logs**,
So that **I can investigate issues and demonstrate compliance**.

**Acceptance Criteria:**

**Given** I am on the admin audit page
**When** I view the audit log table
**Then** I see events with:
- Timestamp
- User (email)
- Action
- Resource type/ID
- IP address

**And** I can filter by:
- Date range (picker)
- User (autocomplete)
- Action type (dropdown)
- Resource type (dropdown)

**And** results are paginated (50 per page)
**And** I can sort by timestamp (default: newest first)

**Prerequisites:** Story 5.1, Story 1.7

**Technical Notes:**
- Use indexed queries on audit.events
- Reference: FR48

---

### Story 5.3: Audit Log Export

As an **administrator**,
I want **to export audit logs for compliance reporting**,
So that **I can provide evidence to auditors**.

**Acceptance Criteria:**

**Given** I have filtered audit logs
**When** I click "Export"
**Then** I can choose format: CSV or JSON

**Given** I select CSV
**When** export completes
**Then** a CSV file downloads with all filtered records
**And** columns match the table display

**Given** I select JSON
**When** export completes
**Then** a JSON file downloads with full audit event details
**And** includes nested details object

**And** export is limited to 10,000 records (paginate for more)
**And** export action is itself logged to audit

**Prerequisites:** Story 5.2

**Technical Notes:**
- Stream large exports to avoid memory issues
- Reference: FR49

---

### Story 5.4: Processing Queue Status

As an **administrator**,
I want **to monitor the document processing queue**,
So that **I can identify and resolve bottlenecks**.

**Acceptance Criteria:**

**Given** I am on the admin page
**When** I view the queue status section
**Then** I see:
- Queue depth (pending events)
- Currently processing count
- Failed events (last 24h)
- Average processing time

**And** I can see list of failed events with error details
**And** I can manually retry failed events
**And** I can purge completed events older than X days

**Prerequisites:** Story 5.1, Story 2.11

**Technical Notes:**
- Query outbox table for metrics
- Use Celery inspection for worker status
- Reference: FR52

---

### Story 5.5: System Configuration

As an **administrator**,
I want **to configure system-wide settings**,
So that **I can tune the system for our needs**.

**Acceptance Criteria:**

**Given** I am on the admin settings page
**When** I view configuration options
**Then** I can configure:
- Default session timeout
- Maximum upload file size
- Default chunk size for processing
- Rate limits

**Given** I save configuration changes
**When** the save completes
**Then** settings are persisted
**And** affected services pick up new values
**And** the change is logged to audit

**Prerequisites:** Story 5.1

**Technical Notes:**
- Store in database, cache in Redis
- Require service restart for some settings (document)
- Reference: FR50, FR51

---

### Story 5.6: KB Statistics (Admin View)

As an **administrator**,
I want **detailed statistics for each Knowledge Base**,
So that **I can optimize storage and identify issues**.

**Acceptance Criteria:**

**Given** I am viewing a KB as admin
**When** I click "Statistics"
**Then** I see detailed metrics:
- Document count by status
- Total storage size (files + vectors)
- Vector count
- Average chunk size
- Search queries (last 30d)
- Top searchers (users)
- Processing success rate

**And** I can see trends over time (chart)

**Prerequisites:** Story 5.1, Story 2.1

**Technical Notes:**
- Aggregate from PostgreSQL + Qdrant + MinIO
- Reference: FR12b

---

### Story 5.7: Onboarding Wizard

As a **first-time user**,
I want **a guided introduction to LumiKB**,
So that **I understand the value and how to use it**.

**Acceptance Criteria:**

**Given** I login for the first time
**When** the dashboard loads
**Then** the onboarding wizard modal appears

**And** the wizard has steps:
1. "Welcome to LumiKB!" - value proposition
2. "Explore the Sample KB" - guided tour of demo KB
3. "Try a Search" - search the demo KB with suggested query
4. "See the Magic" - highlight citations in results
5. "You're Ready!" - next steps and close

**Given** I complete a step
**When** I click "Next"
**Then** I progress to the next step
**And** progress dots show my position

**Given** I want to skip
**When** I click "Skip Tutorial"
**Then** the wizard closes
**And** my preference is saved (don't show again)

**Prerequisites:** Story 1.10, Story 3.4

**Technical Notes:**
- Use Dialog with step state
- Store onboarding_complete flag on user
- Reference: FR8a, FR8b

---

### Story 5.8: Smart KB Suggestions

As a **user**,
I want **the system to suggest relevant KBs based on my content**,
So that **I can quickly find where to search**.

**Acceptance Criteria:**

**Given** I paste text into the search bar
**When** the system analyzes the content
**Then** it suggests 1-3 most relevant KBs
**And** shows why each is suggested (matching keywords)

**Given** I select a suggested KB
**When** I press Enter
**Then** search runs against that KB

**Given** no strong match exists
**When** analysis completes
**Then** suggestion shows "Search all KBs" as default

**Prerequisites:** Story 3.6

**Technical Notes:**
- Analyze pasted content against KB descriptions + sample docs
- Use lightweight embedding comparison
- Reference: FR12c

---

### Story 5.9: Recent KBs and Polish Items

As a **user**,
I want **quick access to recently used KBs and a polished UI**,
So that **my daily workflow is efficient**.

**Acceptance Criteria:**

**Given** I open the KB sidebar
**When** I view the list
**Then** "Recent" section shows my last 5 accessed KBs
**And** they're ordered by most recent first

**And** additional polish items:
- Loading skeletons on all data-fetching views
- Empty states with helpful messages and CTAs
- Error boundaries with friendly recovery options
- Keyboard navigation throughout (Tab, Enter, Escape)
- Tooltips on icon-only buttons

**Prerequisites:** Story 2.3

**Technical Notes:**
- Track recent KBs in localStorage
- Reference: FR12d
- Reference: UX spec Section 7 - Pattern Decisions

---

### Story 5.10: Command Palette Test Coverage Improvement (Technical Debt)

As a **developer**,
I want **to achieve 100% test coverage for the command palette component**,
So that **we have comprehensive test validation for the quick search feature**.

**Acceptance Criteria:**

**Given** the command palette tests currently have 70% pass rate (7/10)
**When** I investigate the test failures
**Then** I identify the root cause (Command component filtering with mocked data)

**And When** I implement a fix
**Then** all 10 command palette tests pass consistently
**And** tests properly validate:
- Result fetching after debounce
- Result display with metadata
- Error state handling on API failure

**And** I document the chosen approach in test file comments

**Prerequisites:** Story 3.7 (completed)

**Technical Notes:**
- **Current Status:** 7/10 tests passing, 3 tests timeout due to shadcn/ui Command component's internal filtering not working with mocked fetch responses
- **Production Impact:** None - production code is verified correct through passing tests and manual validation
- **Priority:** Low - polish item, not blocking
- **Effort:** 1-2 hours
- **Possible Solutions:**
  1. Mock at component level rather than fetch level
  2. Use real Command component behavior with test data
  3. Convert to E2E tests instead of unit tests
  4. Investigate Command/cmdk library test utilities
- **Reference:** Story 3.7 code review, validation-report-3-7-2025-11-26.md
- **Type:** Technical Debt - Test Infrastructure

---

### Story 5.11: Epic 3 Search Hardening (Technical Debt)

As a **developer**,
I want **to complete deferred test coverage and accessibility work from Epic 3**,
So that **search features have comprehensive test coverage and full WCAG 2.1 AA compliance**.

**Acceptance Criteria:**

**Given** Epic 3 deferred work tracked in epic-3-tech-debt.md
**When** I implement the hardening tasks
**Then** all deferred items are completed:

1. **Backend Unit Tests (TD-3.8-1):**
   - Add `test_similar_search_uses_chunk_embedding()` to test_search_service.py
   - Add `test_similar_search_excludes_original()` to test_search_service.py
   - Add `test_similar_search_checks_permissions()` to test_search_service.py
   - All 3 tests pass

2. **Hook Unit Tests (TD-3.8-2):**
   - Create `frontend/src/lib/stores/__tests__/draft-store.test.ts`
   - Add `test_addToDraft__adds_result_to_store()`
   - Add `test_removeFromDraft__removes_by_id()`
   - Add `test_clearAll__empties_selections()`
   - Add `test_isInDraft__returns_true_when_exists()`
   - Add `test_persistence__survives_page_reload()`
   - All 5 tests pass

3. **Screen Reader Verification (TD-3.8-3):**
   - Manually test with NVDA or JAWS screen reader
   - Verify action buttons announce labels correctly
   - Verify draft selection panel announces count changes
   - Verify similar search flow is navigable
   - Document findings in validation-report-3-8-accessibility.md

4. **Command Palette Dialog Accessibility (TD-3.7-1) - NEW:**
   - Add DialogTitle to command-palette.tsx (wrap with VisuallyHidden)
   - Add DialogDescription with "Search across your knowledge bases"
   - Verify Radix UI accessibility warnings eliminated
   - Test with screen reader to confirm announcements

5. **Command Palette Test Fixes (TD-3.7-2) - OPTIONAL:**
   - Debug and fix 3 failing tests (debounce, metadata, error state)
   - Investigate msw mock handler registration
   - Verify React Query cache state in tests
   - All command palette tests passing (10/10)

6. **Desktop Hover Reveal (TD-3.8-4) - OPTIONAL:**
   - Implement hover reveal for action buttons on desktop (≥1024px)
   - Buttons hidden by default, appear on card hover
   - Mobile/tablet behavior unchanged (always visible)

7. **TODO Cleanup (TD-3.8-5):**
   - Scan search components for TODO comments
   - Resolve or convert to tracked issues
   - Verify 0 TODO comments in search/ directory

**And** all existing tests continue to pass (regression protection)

**Prerequisites:** Story 3.8, 3.7, 3.10 (completed)

**Technical Notes:**
- **Source:** Stories 3-7, 3-8, 3-10 code review deferred items
- **Priority:** Medium (improves quality, not blocking production)
- **Effort:** ~6-7 hours (original 4.5h + 0.5h dialog a11y + 1-2h optional tests)
- **Test Pyramid Goal:** Unit tests strengthen isolation, reduce integration test dependency
- **Accessibility Goal:** WCAG 2.1 AA compliance verification (manual + automated)
- **Reference:** docs/sprint-artifacts/epic-3-tech-debt.md
- **Type:** Technical Debt - Test Coverage & Accessibility
- **Updated:** 2025-11-26 (added TD-3.7-1, TD-3.7-2)

**Task Breakdown:**
- Task 1: Backend unit tests (2h)
- Task 2: Hook unit tests (1.5h)
- Task 3: Screen reader testing (1h)
- Task 4: Dialog accessibility (0.5h) - **NEW**
- Task 5: Command palette tests (1-2h) - OPTIONAL
- Task 6: Desktop hover reveal (0.5h) - OPTIONAL
- Task 7: TODO cleanup (0.5h)

**Note:** TD-3.10-1 (VerifyAllButton test harness issue) deferred to Epic 6 due to low priority (test-only issue, component works in production).

---

### Story 5.12: ATDD Integration Tests Transition to GREEN (Technical Debt)

As a **developer**,
I want **to transition 31 ATDD integration tests from RED phase to GREEN**,
So that **search feature integration tests validate against real indexed data in Qdrant**.

**Acceptance Criteria:**

**Given** 31 integration tests are in ATDD RED phase (intentionally failing)
**When** I implement the test infrastructure improvements
**Then** all 31 tests transition to GREEN:

1. **Test Fixture Helper:**
   - Create `backend/tests/helpers/indexing.py`
   - Implement `wait_for_document_indexed(doc_id, timeout=30)` helper
   - Helper polls Qdrant until document chunks indexed
   - Raises TimeoutError if indexing not complete within timeout

2. **Update Test Fixtures:**
   - Update `test_cross_kb_search.py` (9 tests) - use wait_for_document_indexed()
   - Update `test_llm_synthesis.py` (6 tests) - use wait_for_document_indexed()
   - Update `test_quick_search.py` (5 tests) - use wait_for_document_indexed()
   - Update `test_sse_streaming.py` (6 tests) - use wait_for_document_indexed()
   - Update `test_similar_search.py` (5 tests) - use wait_for_document_indexed()

3. **Test Execution:**
   - Run `make test-backend` - 0 failures, 0 errors
   - All 31 previously RED tests now GREEN
   - Existing 496 passing tests still pass (no regressions)

4. **Documentation:**
   - Update epic-3-tech-debt.md TD-ATDD section with RESOLVED status
   - Document wait_for_document_indexed() usage in testing-framework-guideline.md

**And** tests validate against real Qdrant/LiteLLM integration (not mocks)

**Prerequisites:**
- Epic 2 complete (document processing pipeline functional)
- Story 3.10 complete (all search features implemented)

**Technical Notes:**
- **Source:** TD-ATDD in epic-3-tech-debt.md (lines 186-285)
- **Root Cause:** Tests written before implementation (ATDD), expect indexed documents
- **Current Status:** 26 failed + 5 errors = 31 tests in RED phase
- **Error Pattern:** `assert 500 == 200` (empty Qdrant collections → 500 errors)
- **Priority:** Medium (blocks test confidence, not production)
- **Effort:** 3-4 hours
- **Type:** Technical Debt - Test Infrastructure

**Implementation Strategy:**
1. Create polling helper that checks Qdrant for chunk count > 0
2. Use helper in test setup after document upload
3. Ensure tests use same document fixtures consistently
4. Consider adding test-specific Qdrant collection cleanup

**Affected Tests by Story:**
- Story 3.6 (Cross-KB Search): 9 tests
- Story 3.2 (LLM Synthesis): 6 tests
- Story 3.7 (Quick Search): 5 tests
- Story 3.3 (SSE Streaming): 6 tests
- Story 3.8 (Similar Search): 5 tests

**Validation:**
```bash
make test-backend
# Expected: 527 passed, 9 skipped, 0 failed, 0 errors
```

**Reference:**
- docs/sprint-artifacts/epic-3-tech-debt.md (TD-ATDD section)
- Test design checklist: docs/atdd-checklist-3.*.md

**Note:** This resolves the ATDD RED phase deliberately created during Epic 3 story implementation.

---

### Story 5.13: Celery Beat Filesystem Fix (Technical Debt)

As a **developer**,
I want **to fix the celery-beat read-only filesystem error**,
So that **scheduled tasks (like outbox reconciliation) run reliably**.

**Acceptance Criteria:**

**Given** celery-beat service is restarting with error:
```
OSError: [Errno 30] Read-only file system: 'celerybeat-schedule'
```

**When** I investigate the issue
**Then** I identify the root cause (celerybeat-schedule file location)

**And When** I implement the fix
**Then** celery-beat service runs without restarts:
- `docker compose ps` shows lumikb-celery-beat status as "Up" (not "Restarting")
- No OSError in `docker compose logs celery-beat --tail 50`
- Scheduled tasks execute correctly (verify via logs)

**And** the fix persists across:
- Container restarts
- `docker compose down && docker compose up`
- Full environment rebuild

**Acceptance Validation:**
1. Start services: `docker compose up -d`
2. Wait 2 minutes
3. Check status: `docker compose ps celery-beat` → STATUS = "Up"
4. Check logs: `docker compose logs celery-beat --tail 50` → No "Read-only file system" errors
5. Verify scheduled tasks: Check for outbox processing task executions in logs

**Prerequisites:** Epic 2 complete (celery workers functional)

**Technical Notes:**
- **Root Cause:** celerybeat-schedule file written to read-only container path
- **Current Impact:** Scheduled tasks (e.g., outbox reconciliation every 5 min) may not run
- **Priority:** Medium (doesn't block features, but affects background jobs)
- **Effort:** 1 hour
- **Type:** Technical Debt - Infrastructure

**Possible Solutions:**
1. Configure CELERY_BEAT_SCHEDULE_FILENAME to writable volume
2. Mount /app/celerybeat-schedule as Docker volume
3. Set celery beat to use persistent database backend (Django DB scheduler)
4. Write schedule file to /tmp (ephemeral but functional)

**Recommended Approach:**
Option 1 - Configure persistent volume in docker-compose.yml:
```yaml
celery-beat:
  volumes:
    - celery-beat-schedule:/app/celery-schedule
volumes:
  celery-beat-schedule:
```

**And** update celery config:
```python
# backend/app/workers/celery_app.py
app.conf.beat_schedule_filename = '/app/celery-schedule/celerybeat-schedule'
```

**Validation Files:**
- infrastructure/docker/docker-compose.yml (volume mount)
- backend/app/workers/celery_app.py (config change)

**Reference:**
- Discovered during Epic 3 test analysis (2025-11-26)
- Related to Story 2.11 (outbox reconciliation scheduling)

**Note:** While this doesn't block MVP, it should be fixed before production to ensure reliable background job execution.

---

### Story 5.14: Search Audit Logging (moved from Epic 3)

As a **compliance officer**,
I want **all search queries logged**,
So that **we can audit information access**.

**Acceptance Criteria:**

**Given** a user performs a search
**When** results are returned
**Then** an audit event is logged with:
- user_id
- query text
- kb_ids searched
- result_count
- timestamp
- response_time_ms

**Given** audit logs exist
**When** an admin queries them
**Then** they can filter by user, date, and KB

**And** audit write is async (doesn't block search response)

**Prerequisites:**
- Story 3.1 (Semantic Search Backend) - ✅ Complete
- Story 1.7 (Audit Logging Infrastructure) - ✅ Complete
- Story 5.2 (Audit Log Viewer) - Provides UI to view these logs

**Technical Notes:**
- Reuse audit infrastructure from Story 1.7
- Log to `audit.events` table with action_type = 'search'
- Include search metadata in details JSON column
- Async write via background task (don't block search response)
- **Reference:** FR54
- **Type:** Feature - Compliance & Audit
- **Effort:** 1-2 hours
- **Originally:** Story 3.11 in Epic 3, moved to Epic 5 for thematic fit

**Story Relationship:**
- Provides search audit data that Story 5.2 (Audit Log Viewer) will display
- Complements Story 4.10 (Generation Audit Logging) for complete audit coverage
- Together with Stories 5.2 and 5.3, completes the full audit workflow:
  1. Log search queries (5.14)
  2. Log generation requests (4.10)
  3. View all audit logs (5.2)
  4. Export audit logs (5.3)

---

## FR Coverage Matrix

| FR | Epic | Story | Status |
|----|------|-------|--------|
| FR1 | 1 | 1.4 | Covered |
| FR2 | 1 | 1.4 | Covered |
| FR3 | 1 | 1.5 | Covered |
| FR4 | 1 | 1.5 | Covered |
| FR5 | 1 | 1.6 | Covered |
| FR6 | 2 | 2.2 | Covered |
| FR7 | 2 | 2.2 | Covered |
| FR8 | 1 | 1.4 | Covered |
| FR8a | 5 | 5.7 | Covered |
| FR8b | 5 | 5.7 | Covered |
| FR8c | 1 | 1.10 | Covered |
| FR9 | 2 | 2.1 | Covered |
| FR10 | 2 | 2.1 | Covered |
| FR10a | 2 | 2.1 | Covered |
| FR11 | 2 | 2.1 | Covered |
| FR12 | 2 | 2.3 | Covered |
| FR12a | 2 | 2.3 | Covered |
| FR12b | 5 | 5.6 | Covered |
| FR12c | 5 | 5.8 | Covered |
| FR12d | 5 | 5.9 | Covered |
| FR13 | 2 | 2.3 | Covered |
| FR14 | 2 | 2.1 | Covered |
| FR15 | 2 | 2.4 | Covered |
| FR16 | 2 | 2.4 | Covered |
| FR17 | 2 | 2.5, 2.6 | Covered |
| FR18 | 2 | 2.7 | Covered |
| FR19 | 2 | 2.7 | Covered |
| FR20 | 2 | 2.8 | Covered |
| FR21 | 2 | 2.8 | Covered |
| FR22 | 2 | 2.10 | Covered |
| FR23 | 2 | 2.10 | Covered |
| FR23a | 2 | 2.12 | Covered |
| FR23b | 2 | 2.12 | Covered |
| FR23c | 2 | 2.12 | Covered |
| FR24 | 3 | 3.1 | Covered |
| FR24a | 3 | 3.7 | Covered |
| FR24b | 3 | 3.7 | Covered |
| FR24c | 3 | 3.7 | Covered |
| FR24d | 3 | 3.7 | Covered |
| FR25 | 3 | 3.1 | Covered |
| FR26 | 3 | 3.2 | Covered |
| FR27 | 3 | 3.2 | Covered |
| FR27a | 3 | 3.4 | Covered |
| FR28 | 3 | 3.5 | Covered |
| FR28a | 3 | 3.5 | Covered |
| FR28b | 3 | 3.5 | Covered |
| FR29 | 3 | 3.6 | Covered |
| FR29a | 3 | 3.6 | Covered |
| FR30 | 3 | 3.4 | Covered |
| FR30a | 3 | 3.9 | Covered |
| FR30b | 3 | 3.8 | Covered |
| FR30c | 3 | 3.4 | Covered |
| FR30d | 3 | 3.10 | Covered |
| FR30e | 3 | 3.6 | Covered |
| FR30f | 3 | 3.4 | Covered |
| FR31 | 4 | 4.1 | Covered |
| FR32 | 4 | 4.1 | Covered |
| FR33 | 4 | 4.3 | Covered |
| FR34 | 4 | 4.3 | Covered |
| FR35 | 4 | 4.2 | Covered |
| FR35a | 4 | 4.2 | Covered |
| FR35b | 4 | 4.2 | Covered |
| FR36 | 4 | 4.4 | Covered |
| FR37 | 4 | 4.9 | Covered |
| FR38 | 4 | 4.5 | Covered |
| FR39 | 4 | 4.6 | Covered |
| FR40 | 4 | 4.7 | Covered |
| FR40a | 4 | 4.7 | Covered |
| FR40b | 4 | 4.7 | Covered |
| FR41 | 4 | 4.4 | Covered |
| FR42 | 4 | 4.6 | Covered |
| FR42a | 4 | 4.5 | Covered |
| FR42b | 4 | 4.5 | Covered |
| FR42c | 4 | 4.8 | Covered |
| FR42d | 4 | 4.8 | Covered |
| FR42e | 4 | 4.5 | Covered |
| FR43 | 3 | 3.2 | Covered |
| FR44 | 3 | 3.2 | Covered |
| FR45 | 3 | 3.5 | Covered |
| FR46 | 4 | 4.10 | Covered |
| FR47 | 5 | 5.1 | Covered |
| FR48 | 5 | 5.2 | Covered |
| FR49 | 5 | 5.3 | Covered |
| FR50 | 5 | 5.5 | Covered |
| FR51 | 5 | 5.5 | Covered |
| FR52 | 5 | 5.4 | Covered |
| FR53 | 2 | 2.4 | Covered |
| FR54 | 3 | 3.11 | Covered |
| FR55 | 4 | 4.10 | Covered |
| FR56 | 1 | 1.4, 1.5, 1.6 | Covered |
| FR57 | 1 | 1.7 | Covered |
| FR58 | 5 | 5.5 | Covered |

**Coverage:** 66/66 FRs (100%)

---

## Summary

This epic breakdown transforms the LumiKB PRD into 52 implementable stories across 5 epics:

| Epic | Stories | Key Deliverables |
|------|---------|------------------|
| **1. Foundation** | 10 | Auth, audit infrastructure, dashboard shell, demo KB |
| **2. KB & Docs** | 12 | KB management, document upload/processing pipeline |
| **3. Search & Citations** | 11 | Semantic search, citation system, cross-KB search |
| **4. Chat & Generation** | 10 | Chat interface, draft generation, export |
| **5. Admin & Polish** | 9 | Admin dashboard, onboarding wizard, UX polish |

**Design Principles Applied:**
- **Citation-first**: Every AI output story includes citation AC
- **User value per epic**: Each epic has demo-able capability
- **Single-session stories**: Each story completable in one dev session
- **100% FR coverage**: All 66 requirements mapped to stories

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._

_This document will be updated during implementation to incorporate technical discoveries and refinements._
