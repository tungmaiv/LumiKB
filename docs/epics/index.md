# LumiKB - Epic Breakdown

**Author:** Tung Vu
**Date:** 2025-11-23
**Project Level:** Enterprise SaaS B2B Platform
**Target Scale:** MVP 1 - Internal Pilot (20+ users, 5000 documents)

---

## Overview

This document provides the complete epic and story breakdown for LumiKB, decomposing the requirements from the [PRD](../prd.md) into implementable stories.

**Living Document Notice:** This is the initial version. Stories will be updated after implementation begins to incorporate technical discoveries and refinements.

**Design Principles Applied:**
- **Citation-first**: Every search/generate story includes citation acceptance criteria
- **User value per epic**: Each epic delivers demo-able capability
- **Risk front-loading**: Auth, audit, consistency patterns early
- **Journey alignment**: Epics map to user journeys (Sarah's RFP flow, David's contribution flow)
- **KISS**: 5 focused epics, combining related capabilities
- **Single-session stories**: Each story completable in one dev agent session

**Epic Summary:**

| Epic | Name | User Value | Story Count | Link |
|------|------|------------|-------------|------|
| 1 | Foundation & Authentication | Login, explore sample KB with demo docs | 10 | [epic-1-foundation.md](epic-1-foundation.md) |
| 2 | Knowledge Base & Document Management | Create KBs, upload and process documents | 12 | [epic-2-kb-documents.md](epic-2-kb-documents.md) |
| 3 | Semantic Search & Citations | Search and get answers WITH citations | 11 | [epic-3-search.md](epic-3-search.md) |
| 4 | Chat & Document Generation | Chat, generate drafts with citations, export | 10 | [epic-4-chat-generation.md](epic-4-chat-generation.md) |
| 5 | Administration & Polish | Full admin dashboard, onboarding wizard | 26 | [epic-5-admin.md](epic-5-admin.md) |
| 6 | Document Lifecycle Management | Archive, restore, purge, duplicate detection | 9 | [epic-6-lifecycle.md](epic-6-lifecycle.md) |
| 7 | Infrastructure & DevOps | CI/CD, monitoring, model registry, KB lifecycle | 26 | [epic-7-infrastructure.md](epic-7-infrastructure.md) |
| 8 | GraphRAG Integration | Domain-driven knowledge graphs, hybrid search | 18 | [epic-8-graphrag.md](epic-8-graphrag.md) |
| 9 | Hybrid Observability Platform | Distributed tracing, chat history, LLM cost tracking | 14 | [epic-9-observability.md](epic-9-observability.md) |

**Total Stories:** 128+ (including technical debt)

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
| **Epic 6: Document Lifecycle** | FR59-77 | Archive, restore, purge, duplicate detection |
| **Epic 7: Infrastructure & DevOps** | Infrastructure (supports all FRs) | CI/CD, monitoring, model registry |
| **Epic 8: GraphRAG** | FR78-92, FR126-135 | Domain-driven knowledge graphs, history-aware query rewriting, hybrid BM25+vector search |
| **Epic 9: Observability** | FR111-125 | Distributed tracing, chat persistence, LLM cost tracking |

---

## Summary

This epic breakdown transforms the LumiKB PRD into 128+ implementable stories across 9 epics:

| Epic | Stories | Key Deliverables |
|------|---------|------------------|
| **1. Foundation** | 10 | Auth, audit infrastructure, dashboard shell, demo KB |
| **2. KB & Docs** | 12 | KB management, document upload/processing pipeline |
| **3. Search & Citations** | 11 | Semantic search, citation system, cross-KB search |
| **4. Chat & Generation** | 10 | Chat interface, draft generation, export |
| **5. Admin & Polish** | 26 | Admin dashboard, integration, Docker E2E, User/Group management, Document tags/processing/filtering, Chunk Viewer, onboarding |
| **6. Document Lifecycle** | 9 | Archive, restore, purge, clear failed, duplicate detection, replace documents |
| **7. Infrastructure & DevOps** | 26 | Docker E2E, CI/CD, monitoring, model registry, KB model configuration, KB lifecycle management |
| **8. GraphRAG Integration** | 18 | Neo4j, domain schemas, entity extraction, graph-augmented retrieval, history-aware query rewriting, hybrid BM25+vector search |
| **9. Observability** | 14 | Distributed tracing, chat persistence, LLM cost tracking, admin observability dashboard |

**Design Principles Applied:**
- **Citation-first**: Every AI output story includes citation AC
- **User value per epic**: Each epic has demo-able capability
- **Single-session stories**: Each story completable in one dev session
- **100% FR coverage**: All requirements mapped to stories

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._

_This document will be updated during implementation to incorporate technical discoveries and refinements._
