# LumiKB - Product Requirements Document

**Author:** Tung Vu
**Date:** 2025-11-22
**Version:** 1.0

---

## Executive Summary

LumiKB is an enterprise RAG-powered knowledge management platform that transforms how technical and business teams access, synthesize, and create knowledge artifacts. The platform addresses a fundamental enterprise problem: **organizational knowledge is fragmented, inaccessible, and walks out the door when people leave.**

The solution follows a unique **MATCH → MERGE → MAKE** pattern:
- **MATCH**: Intelligent semantic retrieval finds relevant past knowledge
- **MERGE**: Synthesizes knowledge with current context and requirements
- **MAKE**: Assists in creating new artifacts (proposals, documents, solutions) with citations

Starting as an internal tool for Sales, Pre-sales, Business Consulting, and Engineering teams, LumiKB will evolve into a productized platform for Banking & Financial Services organizations facing similar knowledge fragmentation challenges.

### What Makes This Special

**Knowledge that never walks out the door, combined with AI-assisted quality improvement.**

LumiKB isn't just document storage with search - it's an AI-powered work environment that:
1. **Preserves institutional memory** - Knowledge survives staff turnover
2. **Elevates output quality** - AI assists humans to produce better work, faster
3. **Creates an advanced work environment** - Users feel empowered, not overwhelmed

The magic moment: *"It drafted 80% of my RFP response in minutes using our past wins - and I trust it because every claim traces back to source documents."*

---

## Project Classification

**Technical Type:** SaaS B2B Platform
**Domain:** FinTech / Banking & Financial Services
**Complexity:** HIGH

This is an enterprise B2B platform targeting the Banking & Financial Services sector. The domain demands:
- Rigorous compliance frameworks (SOC 2, GDPR, PCI-DSS, ISO 27001)
- Strong security and audit capabilities
- On-premises deployment option for data sovereignty
- Role-based access control for sensitive knowledge

The high-complexity classification triggers additional requirements around compliance matrices, security architecture, audit logging, and data protection - all of which are already embedded in the product vision.

### Domain Context

**Banking & Financial Services Implications:**

| Aspect | Requirement |
|--------|-------------|
| **Data Sensitivity** | Client proposals, pricing, technical solutions are highly confidential |
| **Compliance** | SOC 2 Type II, GDPR, PCI-DSS awareness, ISO 27001 alignment |
| **Deployment** | On-premises capability required; some clients need air-gapped operation |
| **Audit** | Every action logged with user, timestamp, resource for compliance |
| **Access Control** | KB-level isolation, no data leakage between business units or clients |

---

## Success Criteria

### MVP 1 Success: Prove Core Value

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Retrieval Relevance** | 80%+ relevant results in top 5 | Users must trust the answers or they'll abandon the system |
| **Draft Usability** | 70%+ of generated content usable without major edits | Time savings must be real and tangible |
| **Active Adoption** | 5+ pilot users engaged weekly | Proves it solves real pain, not just nice-to-have |
| **Time Savings** | 50%+ reduction in document creation time | Quantifiable ROI for business case |
| **Knowledge Retention** | Zero critical knowledge lost during staff transition | The "never walks out" promise delivered |

### Qualitative Success Indicators

- **Trust**: Users cite LumiKB outputs in client deliverables without manual verification of every claim
- **Habit Formation**: Users check LumiKB *first* when starting a new proposal or document
- **Knowledge Contribution**: Users actively upload documents because they see value in doing so
- **Quality Improvement**: Deliverable quality scores increase compared to pre-LumiKB baseline

### Business Metrics (Post-MVP 1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deal Win Rate** | Improvement in proposals using LumiKB assistance | Track win/loss on LumiKB-assisted vs manual proposals |
| **Onboarding Speed** | New staff productive faster with knowledge access | Time-to-first-deliverable for new hires |
| **Knowledge Coverage** | % of reusable knowledge captured in system | Audit of knowledge base completeness by domain |

---

## Product Scope

### MVP - Minimum Viable Product

**Validation Statement:** *"If users can upload their knowledge documents and get intelligent answers with citations, AND the system can help draft artifacts (RFP responses, questionnaires, checklists), we've validated the core value proposition."*

| Feature | Description | Value Proof |
|---------|-------------|-------------|
| **Knowledge Ingestion** | Upload documents (PDF, DOCX, MD) into organized Knowledge Bases | Foundation - knowledge must get in |
| **Semantic Search** | Ask questions, get answers from your documents with citations | Core MATCH capability |
| **Chat Interface** | Conversational Q&A with document context | Natural interaction model |
| **Document Generation Assist** | Help create drafts: questionnaires, checklists, RFP responses | Core MAKE capability - the magic moment |
| **Citation Tracking** | Every answer traces back to source documents | Trust & compliance requirement |
| **Basic RBAC** | Admin/User roles, KB-level access control | Security foundation |

**MVP 1 Philosophy:** Ruthlessly minimal. Only 6 core features. Prove value before adding complexity.

### Growth Features (Post-MVP)

**MVP 2: Advanced Knowledge Base** - Add when MVP 1 users request it

| Feature | Trigger to Add |
|---------|----------------|
| Hybrid Retrieval (Vector + BM25) | When semantic search alone isn't sufficient |
| Document Sync (OneDrive/SharePoint) | When manual upload becomes friction point |
| Advanced Parsing (OCR, layout-aware) | When scanned docs or complex layouts are common |
| Quality Scoring | When users need confidence indicators |
| Template Engine | When simple prompts aren't flexible enough |

### Vision Features (Future)

**MVP 3: Configurable AI Workflow Engine** - Platform capabilities

| Feature | Purpose |
|---------|---------|
| Visual Workflow Builder | Non-technical users create custom AI workflows |
| Persona Agents | Domain-expert AI personalities (Legal, Technical, Sales) |
| Custom Commands | `/draft-proposal`, `/analyze-rfp`, `/generate-checklist` |
| Quality Gates | Automated review with learning from feedback |
| Graph RAG | Relationship-aware knowledge retrieval |

### Explicitly Out of Scope (MVP 1)

| Deferred | Why | Target |
|----------|-----|--------|
| Graph RAG (Neo4j) | Adds complexity, vector search proves value first | MVP 2+ |
| BM25 Hybrid Search | Vector-only is simpler, iterate based on feedback | MVP 2 |
| Cloud Sync | Manual upload sufficient for pilot | MVP 2 |
| Advanced Workflows | Focus on core Q&A + generation | MVP 3 |
| Multi-language Support | English-first for pilot | Future |

---

## Domain-Specific Requirements

### FinTech/Banking Compliance Matrix

| Framework | Relevance | LumiKB Implications |
|-----------|-----------|---------------------|
| **SOC 2 Type II** | Required for B2B in finance | Audit logging, access controls, encryption at rest/transit |
| **GDPR** | EU clients/employees | Data residency, right to deletion, consent management |
| **PCI-DSS** | If payment card data in docs | Data isolation, encryption, access logging |
| **ISO 27001** | Common in banking | Information security management alignment |
| **BSA** | US banking regulation | Audit trails, data retention policies |

### Security Architecture Requirements

**Built into MVP 1 - Non-Negotiable:**

| Requirement | Implementation |
|-------------|----------------|
| **Audit Logging** | Every action logged: user, timestamp, resource, action type |
| **Encryption at Rest** | All documents and vector embeddings encrypted (AES-256) |
| **Encryption in Transit** | TLS 1.3 for all communications |
| **Role-Based Access** | KB-level isolation, no data leakage between tenants/teams |
| **Data Residency** | On-prem deployment ensures data stays in jurisdiction |
| **Session Management** | Secure session handling, timeout policies |

### Audit Requirements

| Audit Event | Data Captured |
|-------------|---------------|
| Document Upload | User, timestamp, file metadata, KB destination |
| Document Access | User, timestamp, document ID, access type |
| Search Query | User, timestamp, query text, results returned |
| Generation Request | User, timestamp, prompt, sources used, output generated |
| User Management | Admin user, timestamp, action (create/modify/delete), target user |
| Permission Changes | Admin user, timestamp, resource, old/new permissions |

### Data Protection

| Aspect | Approach |
|--------|----------|
| **Sensitive Data Detection** | Flag documents containing PII, financial data, client info |
| **Retention Policies** | Configurable per KB (regulatory minimums enforced) |
| **Right to Deletion** | Complete removal from storage + vector DB + backups |
| **Data Export** | Users can export their data in standard formats |
| **Access Logs** | Immutable audit trail for compliance reporting |

This domain context shapes all functional and non-functional requirements below.

---

## SaaS B2B Platform Requirements

### Multi-Tenancy Model

| Aspect | MVP 1 Approach |
|--------|----------------|
| **Tenant Isolation** | Knowledge Base level isolation (not full multi-tenant) |
| **Data Separation** | Each KB has isolated storage, vectors, and access |
| **Cross-KB Access** | Users can access multiple KBs based on permissions |
| **Admin Scope** | System Admin (all KBs) vs KB Admin (single KB) |

**Note:** Full multi-tenant SaaS architecture deferred to productization phase. MVP 1 is internal deployment with KB-level isolation.

### Permission Matrix (RBAC)

**MVP 1 - Simple Two-Role Model:**

| Role | Capabilities |
|------|--------------|
| **Admin** | Create/manage KBs, manage users, assign KB access, view audit logs, system configuration |
| **User** | Access assigned KBs, upload documents (if permitted), search, chat, generate documents |

**KB-Level Permissions:**

| Permission | Description |
|------------|-------------|
| **Read** | Search and view documents in KB |
| **Write** | Upload and modify documents in KB |
| **Generate** | Use AI generation features with KB content |
| **Admin** | Manage KB settings and user access |

### Integration Requirements (MVP 1)

| Integration | Status | Notes |
|-------------|--------|-------|
| **LLM Provider** | Required | LiteLLM for provider flexibility (OpenAI, Azure, local) |
| **Document Storage** | Required | MinIO (S3-compatible, self-hosted) |
| **Vector Database** | Required | Qdrant (self-hosted) |
| **Authentication** | MVP 1: Local | Future: SSO/SAML |
| **Cloud Storage Sync** | Deferred | MVP 2: OneDrive, SharePoint, Google Drive |

---

## User Experience Principles

### Visual Personality

| Aspect | Direction |
|--------|-----------|
| **Tone** | Professional, trustworthy, efficient |
| **Aesthetic** | Clean, minimal, enterprise-appropriate |
| **Feel** | "Advanced environment" - sophisticated but not intimidating |
| **Trust Signals** | Citations visible, sources clear, AI assistance transparent |

### Design Philosophy

**"Makes my life easier" - not "makes me learn a new system"**

- **Familiar Patterns**: Chat interface feels natural (like Slack/Teams AI)
- **Progressive Disclosure**: Simple by default, power features discoverable
- **Immediate Value**: First interaction should deliver useful result
- **Transparent AI**: Always clear what AI generated vs what came from documents

### Key Interactions

| Interaction | UX Goal |
|-------------|---------|
| **Upload Documents** | Drag-drop simple, progress visible, success confirmation |
| **Ask Questions** | Chat-like, natural language, no query syntax needed |
| **Quick Search** | Simple lookups without full conversation, direct results |
| **View Results** | Answer with inline citations, expandable source preview |
| **Generate Documents** | Clear prompt input, structured output, easy editing |
| **Browse KB** | Intuitive folder/tag navigation, powerful search |
| **Focus Mode** | Collapsed sidebar, expanded workspace for urgent tasks |
| **Compare Mode** | Split-screen view of draft vs source for verification |

### Critical User Flows

1. **First-Time User**
   - Login → See assigned KBs → Pick one → Ask first question → Get useful answer with citations
   - *Goal: Value in under 2 minutes*

2. **Knowledge Contributor**
   - Select KB → Upload document(s) → See processing status → Confirm indexed
   - *Goal: Frictionless contribution*

3. **RFP Response (Magic Moment)**
   - Paste RFP question → Select relevant KBs → Get draft response → See cited sources → Edit and export
   - *Goal: "I can't go back to the old way"*

4. **Admin Setup**
   - Create KB → Set permissions → Invite users → Monitor usage
   - *Goal: Self-service administration*

---

## Functional Requirements

> **This section is THE CAPABILITY CONTRACT.** UX designers will design what's listed here. Architects will support what's listed here. Epic breakdown will implement what's listed here. If a capability is missing, it will NOT exist in the final product.

### User Account & Access

- **FR1**: Users can create accounts with email and password
- **FR2**: Users can log in securely and maintain sessions
- **FR3**: Users can reset passwords via email verification
- **FR4**: Users can update their profile information
- **FR5**: Administrators can create, modify, and deactivate user accounts
- **FR6**: Administrators can assign users to Knowledge Bases with specific permissions
- **FR7**: Users can only access Knowledge Bases they have been granted permission to
- **FR8**: System enforces session timeout and secure logout
- **FR8a**: First-time users see an onboarding tutorial emphasizing citation verification and trust features
- **FR8b**: First-time users see a Getting Started wizard: create KB → upload docs → ask first question
- **FR8c**: System provides a sample Knowledge Base with demo documents for immediate value demonstration

### Knowledge Base Management

- **FR9**: Administrators can create new Knowledge Bases with name and description
- **FR10**: Administrators can configure KB-level settings (retention policy, access defaults)
- **FR10a**: Administrators can configure document processing settings per Knowledge Base (embedding model, generation model, text splitting parameters)
- **FR11**: Administrators can archive or delete Knowledge Bases
- **FR12**: Users can view list of Knowledge Bases they have access to
- **FR12a**: Users can view KB summary information (document count, total size, last updated)
- **FR12b**: Administrators can view detailed KB statistics (document count, chunk count, vector count, storage usage)
- **FR12c**: System suggests relevant Knowledge Bases based on pasted content or query context (Smart KB Suggestions)
- **FR12d**: Users can view recently accessed Knowledge Bases for quick navigation
- **FR13**: Users can switch between Knowledge Bases within a session
- **FR14**: Each Knowledge Base maintains isolated storage and vector indices

### Document Ingestion (MATCH Foundation)

- **FR15**: Users with write permission can upload documents to a Knowledge Base
- **FR16**: System accepts PDF, DOCX, and Markdown file formats
- **FR17**: System processes uploaded documents: extraction, chunking, embedding
- **FR18**: Users can see upload progress and processing status
- **FR19**: System notifies users when document processing completes
- **FR20**: Users can view list of documents in a Knowledge Base
- **FR21**: Users can view document metadata (name, upload date, size, uploader)
- **FR22**: Users with write permission can delete documents from a Knowledge Base
- **FR23**: System removes deleted documents from storage and vector index completely
- **FR23a**: Users with write permission can re-upload/update existing documents in a Knowledge Base
- **FR23b**: System supports incremental vector updates when documents are modified (re-chunk and re-embed only changed content, or full refresh based on configuration)
- **FR23c**: System maintains document version awareness to detect changes and trigger appropriate reprocessing

### Semantic Search & Q&A (MATCH Capability)

- **FR24**: Users can ask natural language questions against a Knowledge Base
- **FR24a**: Users can perform Quick Search for simple lookups without entering full chat conversation mode
- **FR24b**: Quick Search is accessible via always-visible search bar at top of screen
- **FR24c**: Quick Search is accessible via keyboard shortcut (Cmd/Ctrl+K)
- **FR24d**: Users can set preference for default search mode (Quick Search vs Chat)
- **FR25**: System performs semantic search to find relevant document chunks
- **FR26**: System returns answers synthesized from retrieved content
- **FR27**: Every answer includes citations linking to source documents
- **FR27a**: Citations are displayed INLINE with answers (always visible), not hidden in separate panel
- **FR28**: Users can click citations to view source document context
- **FR28a**: Users can access and view the original source document from search results or citations
- **FR28b**: System highlights the relevant paragraph/section within the original document that was used for the answer
- **FR29**: Users can search across multiple Knowledge Bases simultaneously (if permitted)
- **FR29a**: Cross-KB search is the DEFAULT behavior; users filter by KB after viewing results
- **FR30**: System displays confidence/relevance indicators for search results
- **FR30a**: System explains WHY each result is relevant (e.g., "Relevant because: mentions authentication, banking client, similar scope") not just a numeric score
- **FR30b**: Users can perform quick actions on search results: "Use in draft" | "View source" | "Save for later"
- **FR30c**: Confidence indicators are ALWAYS shown for AI-generated content (never hidden)
- **FR30d**: Users can click "Verify All" to see all citations for a generated response at once
- **FR30e**: Users can filter results to "Search within current KB" as a quick filter option
- **FR30f**: System displays citation accuracy score indicating how closely generated text matches source

### Chat Interface (Conversational Experience)

- **FR31**: Users can engage in multi-turn conversations with the system
- **FR32**: System maintains conversation context within a session
- **FR33**: Users can start new conversation threads
- **FR34**: Users can view conversation history within current session
- **FR35**: System clearly distinguishes AI-generated content from quoted sources
- **FR35a**: System streams AI responses in real-time (word-by-word) for perceived speed and engagement
- **FR35b**: Users can see typing/thinking indicators while the system processes their request

### Document Generation Assist (MAKE Capability)

- **FR36**: Users can request AI assistance to generate document drafts
- **FR37**: System supports generation of: RFP/RFI responses, questionnaires, checklists, gap analysis
- **FR38**: Generated content includes citations to source documents used
- **FR39**: Users can edit generated content before exporting
- **FR40**: Users can export generated documents in common formats (DOCX, PDF, MD)
- **FR40a**: Exported documents preserve citations and formatting accurately
- **FR40b**: System prompts "Have you verified the sources?" before export for high-stakes documents
- **FR41**: System allows users to provide context/instructions for generation
- **FR42**: Users can regenerate content with modified instructions
- **FR42a**: System displays generation progress and streams draft content in real-time
- **FR42b**: Upon completion, system shows summary: "Draft ready! Based on X sources from Y documents"
- **FR42c**: Users can provide feedback on generation quality via "This doesn't look right" button
- **FR42d**: System offers alternative approaches when generation fails: "Try different approach" | "Start from template" | "Search for examples"
- **FR42e**: System highlights low-confidence sections with "Consider manual editing" indicator

### Citation & Provenance (Trust & Compliance)

- **FR43**: Every AI-generated statement traces back to source document(s)
- **FR44**: Citations include document name, section, and page/location reference
- **FR45**: Users can preview cited source content without leaving current view
- **FR46**: System logs all sources used in each generation request

### Administration & Configuration

- **FR47**: Administrators can view system-wide usage statistics
- **FR48**: Administrators can view audit logs with filters (user, action, date range)
- **FR49**: Administrators can export audit logs for compliance reporting
- **FR50**: Administrators can configure LLM provider settings
- **FR51**: Administrators can configure system-wide defaults (session timeout, file size limits)
- **FR52**: Administrators can view and manage processing queue status

### Audit & Compliance (Domain-Driven)

- **FR53**: System logs every document upload with user, timestamp, and metadata
- **FR54**: System logs every search query with user, timestamp, and results summary
- **FR55**: System logs every generation request with user, timestamp, prompt, and sources used
- **FR56**: System logs every user management action (create, modify, delete, permission change)
- **FR57**: Audit logs are immutable and tamper-evident
- **FR58**: System supports configurable data retention policies per Knowledge Base

---

## Non-Functional Requirements

### Performance

| Requirement | Target | Why It Matters |
|-------------|--------|----------------|
| **Search Response Time** | < 3 seconds for semantic search results | Users expect near-instant answers |
| **Document Processing** | < 2 minutes for typical document (10-50 pages) | Contributors shouldn't wait |
| **Chat Response** | < 5 seconds for conversational responses | Maintains conversation flow |
| **Generation Response** | < 30 seconds for document draft generation | Acceptable for complex operations |
| **Concurrent Users** | Support 20+ simultaneous users | Pilot team size |
| **Upload Size** | Support documents up to 50MB | Handles large proposals/specs |

### Security

| Requirement | Implementation | Compliance Driver |
|-------------|----------------|-------------------|
| **Authentication** | Secure password hashing (bcrypt/argon2), session tokens | SOC 2 |
| **Authorization** | KB-level permission enforcement on every request | Data isolation |
| **Encryption at Rest** | AES-256 for documents, vectors, and database | SOC 2, ISO 27001 |
| **Encryption in Transit** | TLS 1.3 for all API and UI communications | PCI-DSS, SOC 2 |
| **Input Validation** | Sanitize all user inputs, prevent injection attacks | OWASP Top 10 |
| **Rate Limiting** | Prevent brute force and DoS on authentication endpoints | Security best practice |
| **Secret Management** | No hardcoded secrets, environment-based configuration | Security best practice |

### Reliability

| Requirement | Target | Notes |
|-------------|--------|-------|
| **Availability** | 99% uptime during business hours | Internal deployment, not 24/7 SLA |
| **Data Durability** | Zero data loss for committed documents | Critical for knowledge retention |
| **Graceful Degradation** | System remains usable if LLM provider is slow/unavailable | Search still works, generation queued |
| **Backup & Recovery** | Daily backups with tested recovery procedure | Compliance requirement |

### Data Consistency (Cross-Service Integrity)

| Requirement | Description |
|-------------|-------------|
| **KB Lifecycle Consistency** | When a Knowledge Base is created, updated, archived, or deleted, all dependent components (PostgreSQL metadata, MinIO storage, Qdrant vectors) must be updated atomically or with eventual consistency guarantees |
| **Document Lifecycle Consistency** | When a document is uploaded, updated, or deleted, all representations (file storage, metadata, vector embeddings) must be synchronized |
| **Document Update Strategy** | System must support two update modes: (1) Full Refresh - delete all vectors for document, re-chunk, re-embed entirely; (2) Incremental - detect changed sections, update only affected vectors. Default to full refresh for MVP 1 simplicity |
| **Orphan Prevention** | System must prevent orphaned data (vectors without documents, storage without metadata) |
| **Rollback on Failure** | If any component update fails during KB/document operations, system must rollback to consistent state or mark for cleanup |
| **Consistency Verification** | System should support consistency checks to detect and repair drift between components |

**Implementation Guidance for Architecture:**
- Use transactional outbox pattern or saga pattern for cross-service operations
- Implement background reconciliation jobs to detect/fix inconsistencies
- Log all component state changes for audit and debugging
- Consider soft-delete with cleanup jobs rather than immediate hard-delete

### Scalability (MVP 1 Baseline)

| Aspect | MVP 1 Target | Growth Path |
|--------|--------------|-------------|
| **Knowledge Bases** | 10-20 KBs | Horizontal scaling of vector indices |
| **Documents** | 1,000-5,000 documents total | Partitioned storage |
| **Users** | 50-100 users | Stateless API scales horizontally |
| **Concurrent Requests** | 50 requests/second | Load balancer + replicas |

### Deployment & Operations

| Requirement | Approach |
|-------------|----------|
| **Containerization** | All services run in Docker containers |
| **Orchestration** | Docker Compose for dev, Kubernetes-ready for production |
| **Configuration** | Environment-based, no code changes for deployment |
| **Logging** | Structured JSON logs, centralized collection ready |
| **Monitoring** | Health endpoints, metrics exposure (Prometheus-compatible) |
| **Air-Gap Capable** | Can run without external network (local LLM option) |

### Observability

| Capability | Implementation |
|------------|----------------|
| **Health Checks** | `/health` endpoint for each service |
| **Metrics** | Request latency, error rates, queue depth, LLM usage |
| **Logging** | Structured logs with correlation IDs across services |
| **Alerting** | Configurable thresholds for key metrics |

---

## PRD Summary

| Aspect | Count/Detail |
|--------|--------------|
| **Functional Requirements** | 66 FRs across 8 capability areas |
| **Non-Functional Requirements** | Performance, Security, Reliability, Scalability, Deployment, Observability, Data Consistency |
| **MVP Features** | 6 core features (Knowledge Ingestion, Semantic Search, Chat, Generation, Citations, RBAC) |
| **Project Type** | SaaS B2B Platform |
| **Domain** | FinTech/Banking (HIGH complexity) |
| **Compliance Frameworks** | SOC 2, GDPR, PCI-DSS awareness, ISO 27001 |

### Product Value Summary

**LumiKB delivers knowledge that never walks out the door.**

An AI-powered knowledge platform for Banking & Financial Services teams that:
- **MATCHES** relevant past knowledge through semantic search
- **MERGES** knowledge with current context intelligently
- **MAKES** new artifacts (proposals, documents, solutions) with full citations

The core promise: *"It drafted 80% of my RFP response in minutes using our past wins - and I trust it because every claim traces back to source documents."*

---

## Source Documents

| Document | Purpose |
|----------|---------|
| Product Brief | `docs/product-brief-LumiKB-2025-11-22.md` |
| Brainstorming Results | `docs/04-brainstorming-session-results-2025-11-22.md` |

---

*This PRD captures the essence of LumiKB - knowledge that never walks out the door, with AI-assisted quality improvement in an advanced work environment.*

*Created through collaborative discovery between Tung Vu and AI facilitator.*
