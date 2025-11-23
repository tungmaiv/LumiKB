# LumiKB Documentation Index

> Auto-generated index of all project documentation, ordered by creation date.

**Last Updated:** 2025-11-23

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

### UX & Design
- [ux-design-specification.md](ux-design-specification.md) - Complete UX specification with wireframes, component library, user flows

### Discovery & Strategy
- [04-brainstorming-session-results-2025-11-22.md](04-brainstorming-session-results-2025-11-22.md) - Complete brainstorming session with MVP roadmap

---

## Sprint Artifacts

| # | Artifact | Description | Created | Status |
|---|----------|-------------|---------|--------|
| 1 | [sprint-artifacts/sprint-status.yaml](sprint-artifacts/sprint-status.yaml) | Sprint Status Tracking - All epics and stories with status | 2025-11-23 | Active |
| 2 | [sprint-artifacts/tech-spec-epic-1.md](sprint-artifacts/tech-spec-epic-1.md) | Epic 1 Tech Spec - Foundation & Authentication detailed design | 2025-11-23 | Active |
| 3 | [sprint-artifacts/1-1-project-initialization-and-repository-setup.md](sprint-artifacts/1-1-project-initialization-and-repository-setup.md) | Story 1.1 - Project Initialization (ready-for-dev) | 2025-11-23 | Ready |
| 4 | [sprint-artifacts/1-1-project-initialization-and-repository-setup.context.xml](sprint-artifacts/1-1-project-initialization-and-repository-setup.context.xml) | Story 1.1 Context - Technical context for dev agent | 2025-11-23 | Ready |
| 5 | [sprint-artifacts/validation-report-1-1-2025-11-23.md](sprint-artifacts/validation-report-1-1-2025-11-23.md) | Story 1.1 Validation - Quality validation report | 2025-11-23 | Complete |

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

## Folders

| Folder | Purpose | Contents |
|--------|---------|----------|
| [sprint-artifacts/](sprint-artifacts/) | Sprint deliverables and artifacts | Sprint status, tech specs, stories, contexts |

---

## Current Sprint Status

| Epic | Status | Stories Ready | Stories Done |
|------|--------|---------------|--------------|
| Epic 1: Foundation & Authentication | **contexted** | 1 | 0 |
| Epic 2: Knowledge Base & Document Management | backlog | 0 | 0 |
| Epic 3: Semantic Search & Citations | backlog | 0 | 0 |
| Epic 4: Chat & Document Generation | backlog | 0 | 0 |
| Epic 5: Administration & Polish | backlog | 0 | 0 |

**Next Action:** Story 1.1 (Project Initialization) is ready-for-dev

---

*This index is maintained to track all project documentation for LumiKB.*
