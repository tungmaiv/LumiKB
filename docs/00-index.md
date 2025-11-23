# LumiKB Documentation Index

> Auto-generated index of all project documentation, ordered by creation date.

**Last Updated:** 2025-11-23
**Repository:** https://github.com/tungmaiv/LumiKB

---

## Project Status

| Metric | Value |
|--------|-------|
| Current Epic | Epic 1: Foundation & Authentication |
| Epic 1 Status | **COMPLETED** (10/10 stories) |
| Epic 1 Retrospective | Completed |
| Next Epic | Epic 2: Knowledge Base & Document Management |
| Total Progress | 10/52 stories (19%) |

---

## Documents

| # | Document | Description | Created | Status |
|---|----------|-------------|---------|--------|
| 1 | [01-solution-idea.md](01-solution-idea.md) | Initial RAG Solution Requirements - Core requirements and technology preferences | 2025-11-22 | Reference |
| 2 | [02-first-commend.md](02-first-commend.md) | First Architecture Blueprint - "Headless Neural Mesh" concept with modular monolith design | 2025-11-22 | Reference |
| 3 | [03-second-commend.md](03-second-commend.md) | Refined Solution Blueprint - Detailed architecture layers and agent definitions | 2025-11-22 | Reference |
| 4 | [04-brainstorming-session-results-2025-11-22.md](04-brainstorming-session-results-2025-11-22.md) | Comprehensive Brainstorming Session - 25 capabilities, 3 MVPs, final architecture decisions | 2025-11-22 | Active |
| 5 | [product-brief-LumiKB-2025-11-22.md](product-brief-LumiKB-2025-11-22.md) | Product Brief - Vision, target users, MVP scope, development philosophy (KISS/DRY/YAGNI) | 2025-11-22 | Active |
| 6 | [prd.md](prd.md) | Product Requirements Document - 66 FRs, 7 NFR categories, FinTech/Banking compliance | 2025-11-22 | Active |
| 7 | [ux-design-specification.md](ux-design-specification.md) | UX Design Specification - Three-panel NotebookLM style, Trust Blue theme, shadcn/ui, WCAG AA | 2025-11-22 | Active |
| 8 | [architecture.md](architecture.md) | System Architecture - Python monolith, citation-first, transactional outbox pattern | 2025-11-22 | Active |
| 9 | [epics.md](epics.md) | Epic Breakdown - 5 epics, 52 stories, FR traceability | 2025-11-22 | Active |
| 10 | [coding-standards.md](coding-standards.md) | Coding Standards - Python/TypeScript conventions, API patterns, testing | 2025-11-22 | Active |
| 11 | [bmm-workflow-status.yaml](bmm-workflow-status.yaml) | BMM Workflow Status - Project progress tracking through BMad Method phases | 2025-11-22 | Active |
| 12 | [test-framework-specification.md](test-framework-specification.md) | Test Framework Specification - pytest, testcontainers, markers, CI/CD | 2025-11-23 | Active |
| 13 | [handover-tea-test-framework.md](handover-tea-test-framework.md) | TEA Handover - Test framework implementation guide | 2025-11-23 | Complete |

---

## Document Categories

### Planning Artifacts (BMad Method)
- [product-brief-LumiKB-2025-11-22.md](product-brief-LumiKB-2025-11-22.md) - Product vision and scope
- [prd.md](prd.md) - **Product Requirements Document** (66 FRs, 7 NFR categories)
- [ux-design-specification.md](ux-design-specification.md) - **UX Design Specification** (Three-panel layout, Trust Blue theme)
- [bmm-workflow-status.yaml](bmm-workflow-status.yaml) - Workflow progress tracker

### Requirements & Ideas
- [01-solution-idea.md](01-solution-idea.md) - Initial project requirements

### Architecture
- [02-first-commend.md](02-first-commend.md) - First architecture proposal
- [03-second-commend.md](03-second-commend.md) - Refined architecture with full tech stack
- [architecture.md](architecture.md) - **Final Architecture Document** (ADRs, patterns, data models)

### Epic & Story Breakdown
- [epics.md](epics.md) - **Epic Breakdown** (5 epics, 52 stories with acceptance criteria)

### Standards & Guidelines
- [coding-standards.md](coding-standards.md) - **Coding Standards** (Python, TypeScript, API, Database, Git)
- [test-framework-specification.md](test-framework-specification.md) - **Test Framework Specification** (markers, fixtures, CI/CD)

### UX & Design
- [ux-design-specification.md](ux-design-specification.md) - Complete UX specification with wireframes, component library, user flows

### Discovery & Strategy
- [04-brainstorming-session-results-2025-11-22.md](04-brainstorming-session-results-2025-11-22.md) - Complete brainstorming session with MVP roadmap

---

## Sprint Artifacts

| # | Artifact | Description | Status |
|---|----------|-------------|--------|
| 1 | [sprint-artifacts/sprint-status.yaml](sprint-artifacts/sprint-status.yaml) | Sprint Status Tracking - All epics and stories with status | Active |
| 2 | [sprint-artifacts/tech-spec-epic-1.md](sprint-artifacts/tech-spec-epic-1.md) | Epic 1 Tech Spec - Foundation & Authentication detailed design | Complete |
| 3 | [sprint-artifacts/epic-1-retrospective.md](sprint-artifacts/epic-1-retrospective.md) | Epic 1 Retrospective - What went well, challenges, action items | Complete |

### Epic 1 Stories (All Complete)

| Story | Title | Status |
|-------|-------|--------|
| 1-1 | Project Initialization and Repository Setup | Done |
| 1-2 | Database Schema and Migration Setup | Done |
| 1-3 | Docker Compose Development Environment | Done |
| 1-4 | User Registration and Authentication Backend | Done |
| 1-5 | User Profile and Password Management Backend | Done |
| 1-6 | Admin User Management Backend | Done |
| 1-7 | Audit Logging Infrastructure | Done |
| 1-8 | Frontend Authentication UI | Done |
| 1-9 | Three-Panel Dashboard Shell | Done |
| 1-10 | Demo Knowledge Base Seeding | Done |

---

## Key Decisions Summary

| Decision | Source | Details |
|----------|--------|---------|
| Architecture | Architecture Doc (ADR-001) | Python + FastAPI monolith (not Go + Python microservices) |
| Vector DB | Architecture Doc (ADR-002) | Qdrant with collection-per-KB isolation |
| Consistency | Architecture Doc (ADR-003) | Transactional outbox pattern |
| Audit Logging | Architecture Doc (ADR-004) | PostgreSQL audit table (INSERT-only) |
| Core Differentiator | Architecture Doc (ADR-005) | Citation-first architecture |
| Frontend | All Documents | Next.js 15 + shadcn/ui + Zustand |
| Storage | All Documents | MinIO (blob) + PostgreSQL (metadata) |
| MVP Approach | Brainstorming Session | 5 epics: Foundation → KB → Search → Chat → Admin |

---

## Technical Stack

### Backend
- **Framework:** FastAPI + Pydantic v2
- **ORM:** SQLAlchemy 2.0 async
- **Auth:** FastAPI-Users with JWT cookies
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Migrations:** Alembic

### Frontend
- **Framework:** Next.js 15 (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **State:** Zustand
- **Forms:** React Hook Form + Zod

### Infrastructure
- **Container:** Docker Compose
- **Object Storage:** MinIO
- **Vector DB:** Qdrant
- **LLM Proxy:** LiteLLM

### Testing
- **Backend:** pytest, pytest-asyncio, testcontainers
- **Frontend:** Vitest, React Testing Library
- **E2E:** Playwright

---

## Folders

| Folder | Purpose | Contents |
|--------|---------|----------|
| [sprint-artifacts/](sprint-artifacts/) | Sprint deliverables and artifacts | Sprint status, tech specs, stories, retrospectives |

---

## Current Sprint Status

| Epic | Status | Stories Done | Total |
|------|--------|--------------|-------|
| Epic 1: Foundation & Authentication | **COMPLETED** | 10 | 10 |
| Epic 2: Knowledge Base & Document Management | backlog | 0 | 12 |
| Epic 3: Semantic Search & Citations | backlog | 0 | 11 |
| Epic 4: Chat & Document Generation | backlog | 0 | 10 |
| Epic 5: Administration & Polish | backlog | 0 | 9 |

**Next Action:** Context Epic 2, then begin Story 2-1 (Knowledge Base CRUD Backend)

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/tungmaiv/LumiKB.git
cd LumiKB

# Start infrastructure
make dev

# Run backend (in separate terminal)
make dev-backend

# Run frontend (in separate terminal)
make dev-frontend

# Run tests
make test-all
```

---

*This index is maintained to track all project documentation for LumiKB.*
