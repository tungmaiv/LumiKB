# Product Brief: LumiKB

**Date:** 2025-11-22
**Author:** Tung Vu
**Context:** Enterprise Platform (Internal-first, then Productize)

---

## Executive Summary

LumiKB is an enterprise RAG-powered knowledge management platform that transforms how technical and business teams access, synthesize, and create knowledge artifacts. Starting as an internal tool to solve knowledge fragmentation across Sales, Pre-sales, Business Consulting, and Engineering teams, LumiKB will evolve into a productized platform for other organizations facing similar challenges.

The platform follows a unique **MATCH → MERGE → MAKE** pattern - intelligently retrieving relevant knowledge, synthesizing it with context, and assisting in creating new artifacts like proposals, technical documents, and solutions.

---

## Core Vision

### Problem Statement

**There is no single source of truth for organizational knowledge.**

Valuable information from previous projects - winning proposals, technical solutions, lessons learned, client-specific configurations - is scattered, lost, or locked in people's heads. When someone needs this knowledge, they either can't find it, don't know it exists, or waste hours hunting through disconnected systems.

**Where Knowledge Lives Today (The Fragmentation Problem):**

| Location | Problem |
|----------|---------|
| **Personal Drives** | Invisible to others, leaves when people leave |
| **Email Attachments** | Unsearchable, version chaos, buried in threads |
| **People's Heads** | Single point of failure, doesn't scale, lost on departure |
| **SharePoint Folders** | Folder maze, poor search, outdated versions mixed with current |

**The Real Scenario:**

A Sales rep receives an RFP. They know the company did a similar project 18 months ago - but who worked on it? Where's the proposal? The technical approach? They spend hours asking around, searching folders, digging through email. Maybe they find pieces. Maybe they recreate from scratch what already existed. Meanwhile, the deadline looms.

### Problem Impact

| Impact Area | Consequence |
|-------------|-------------|
| **Lost Deals** | Proposals that could have been stronger with past winning patterns |
| **Delayed Projects** | Time wasted hunting for information that should be at fingertips |
| **Repeated Mistakes** | Lessons learned never learned - same errors across projects |
| **Junior Staff Spinning** | New team members have no way to access institutional knowledge |
| **Knowledge Drain** | When experienced staff leave, their knowledge walks out the door |

### Why Existing Solutions Fall Short

- **SharePoint/Confluence**: Great for storage, terrible for intelligent retrieval. You need to know WHERE to look and WHAT to search for
- **Basic Search**: Keyword matching doesn't understand context - searching "authentication" doesn't find "SSO implementation guide"
- **Asking Around**: Doesn't scale, interrupts experts, knowledge still not captured
- **Manual Documentation**: Always outdated, rarely maintained, not contextual

### Proposed Solution

**LumiKB: Intelligent Knowledge That Works For You**

An AI-powered knowledge platform that doesn't just store documents - it **understands** them, **connects** them, and **uses** them to help teams work smarter.

**The MATCH → MERGE → MAKE Pattern:**

| Stage | What Happens | Example |
|-------|--------------|---------|
| **MATCH** | Intelligent retrieval finds relevant past knowledge | "Find proposals similar to this RFP" → Returns 5 relevant past wins |
| **MERGE** | Synthesizes knowledge with current context | Combines past approach + client requirements + current capabilities |
| **MAKE** | Assists creating new artifacts | Drafts proposal sections with citations to source documents |

**Key Differentiators:**

1. **Semantic Understanding** - Knows what documents MEAN, not just what words they contain
2. **Context Awareness** - Understands WHO is asking and WHY (Sales vs Engineer need different answers)
3. **Active Assistance** - Doesn't just find docs, helps CREATE new artifacts from existing knowledge
4. **Citation & Provenance** - Every generated piece traces back to source documents
5. **Role-Based Access** - Right people see right knowledge (client-sensitive, internal-only)

---

## Development Philosophy

> **All implementation steps, workflows, and architectural decisions MUST follow these principles.**

### KISS - Keep It Simple, Stupid

| Principle | Application to LumiKB |
|-----------|----------------------|
| **Simple over clever** | Choose boring, proven technologies over cutting-edge complexity |
| **Minimal moving parts** | MVP 1 uses 7 core components, not 12 |
| **Easy to understand** | Any developer should grok the architecture in 30 minutes |
| **Straightforward flows** | Request → Process → Response. No Byzantine orchestration |

**Examples:**
- ✅ Vector search only (simple) vs ❌ Hybrid + Graph + BM25 (complex)
- ✅ Redis for queues (proven) vs ❌ Custom event system (clever)
- ✅ PostgreSQL for metadata (boring) vs ❌ Multi-database polyglot (fancy)

### DRY - Don't Repeat Yourself

| Principle | Application to LumiKB |
|-----------|----------------------|
| **Single source of truth** | One place for each piece of logic, config, or data |
| **Reusable components** | Build once, use everywhere |
| **Shared libraries** | Common utilities across backend services and workers |
| **Centralized config** | Environment-driven configuration, not scattered constants |

**Examples:**
- ✅ One auth middleware (shared) vs ❌ Auth logic in every endpoint
- ✅ Common chunking strategy (configurable) vs ❌ Different chunkers per doc type
- ✅ Unified error handling vs ❌ Custom error patterns per service

### YAGNI - You Ain't Gonna Need It

| Principle | Application to LumiKB |
|-----------|----------------------|
| **Build for today** | Implement what's needed NOW, not what MIGHT be needed |
| **No speculative features** | If users haven't asked for it, don't build it |
| **Defer complexity** | Add capabilities when validated, not anticipated |
| **Delete dead code** | If it's not used, remove it |

**Examples:**
- ✅ Basic RBAC (Admin/User) vs ❌ Full hierarchical permissions (MVP 1)
- ✅ Manual upload vs ❌ OneDrive/SharePoint sync (MVP 1)
- ✅ Simple parsers vs ❌ OCR + layout-aware extraction (MVP 1)
- ✅ Vector search vs ❌ Graph RAG (MVP 1)

### Philosophy Enforcement Checklist

Before implementing ANY feature, ask:

```
┌─────────────────────────────────────────────────────────────┐
│ KISS: Is this the simplest solution that could work?       │
│       Can a junior developer understand this in 10 min?    │
│                                                            │
│ DRY:  Does this duplicate existing code/logic?             │
│       Can this be extracted into a shared component?       │
│                                                            │
│ YAGNI: Is a user asking for this RIGHT NOW?                │
│        Will MVP 1 fail without this?                       │
│        Can this wait until we have user feedback?          │
└─────────────────────────────────────────────────────────────┘
```

### What This Means for Each MVP

| MVP | Philosophy Application |
|-----|----------------------|
| **MVP 1** | Ruthlessly minimal. Only 6 features. Prove core value before anything else. |
| **MVP 2** | Add complexity ONLY after MVP 1 users request it. Each feature must justify itself. |
| **MVP 3** | Platform capabilities added incrementally based on real usage patterns. |

### Anti-Patterns to Avoid

| Anti-Pattern | Why It's Dangerous | Instead Do |
|--------------|-------------------|------------|
| **"Future-proofing"** | Builds for imaginary requirements | Build for today's validated needs |
| **"Just in case"** | Adds unused complexity | Add when actually needed |
| **"Enterprise-ready"** | Over-engineers before product-market fit | Start simple, scale when required |
| **"Best practices"** | Blindly follows patterns without context | Apply patterns that solve YOUR problems |
| **"Microservices from day 1"** | Distributed complexity without scale needs | Start modular monolith, extract when needed |

---

## Target Users

### Primary Users (Pilot Group)

| Role | Current Pain | What They Need | Magic Moment |
|------|--------------|----------------|--------------|
| **Sales** | RFI/RFP response is time-consuming and quality inconsistent | Share product docs, specs, past wins → get draft responses | "It drafted 80% of the RFP response in minutes, not days" |
| **Pre-sales** | RFI/RFP response quality varies, missing key differentiators | Access to winning patterns, capability mapping | "It found exactly how we solved this before and suggested the approach" |
| **Business Consultant** | Gap analysis may miss aspects of customer requirements; BRD/BSD creation is time-consuming | Questionnaires, interview guides, requirement checklists | "It generated a gap analysis checklist I would have missed items on" |
| **Business Consultant** | Mapping customer requirements to proposed solution - quality is low | Intelligent matching of requirements to capabilities | "It mapped 50 requirements to our solutions with citations in an hour" |
| **System Engineer** | TSD creation is time-consuming, searching for technical patterns | Technical specs, architecture references, implementation guides | "It drafted the TSD sections with references to similar past implementations" |

### User Journey: From Pain to Value

```
USER SHARES KNOWLEDGE          USER ASKS QUESTIONS           LUMIKB HELPS CREATE
─────────────────────         ───────────────────           ───────────────────
• Solution documents          • "What products fit          • Draft RFI/RFP responses
• Product specifications        this requirement?"          • Questionnaires
• Past proposals              • "How did we solve           • Interview guidelines
• Technical guides              this before?"               • Gap analysis checklists
• Implementation docs         • "What's our approach        • BSD documents
                                to authentication?"         • TSD documents
                                                           • Requirement mappings
```

---

## MVP Scope

### MVP 1 Validation Statement

**"If users can upload their knowledge documents and get intelligent answers with citations, AND the system can help draft artifacts (RFP responses, questionnaires, checklists), we've validated the core value proposition."**

### Core Features (MVP 1)

| Feature | Description | Value Proof |
|---------|-------------|-------------|
| **Knowledge Ingestion** | Upload documents (PDF, DOCX, MD) into organized Knowledge Bases | Foundation - knowledge must get in |
| **Semantic Search** | Ask questions, get answers from your documents with citations | Core MATCH capability |
| **Chat Interface** | Conversational Q&A with document context | Natural interaction model |
| **Document Generation Assist** | Help create drafts: questionnaires, checklists, RFP responses | Core MAKE capability - the magic moment |
| **Citation Tracking** | Every answer traces back to source documents | Trust & compliance |
| **Basic RBAC** | Admin/User roles, KB-level access control | Security foundation |

### MVP 1 Success Criteria

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Retrieval Accuracy** | 80%+ relevant results in top 5 | Users must trust the answers |
| **Draft Quality** | 70%+ usable without major edits | Time savings must be real |
| **User Adoption** | 5+ pilot users active weekly | Solves real pain |
| **Time Savings** | 50%+ reduction in document creation time | Quantifiable value |

### Out of Scope for MVP 1

| Deferred Feature | Why Deferred | Target MVP |
|------------------|--------------|------------|
| Graph RAG (Neo4j) | Adds complexity, vector search sufficient to prove value | MVP 2 |
| BM25 Hybrid Search | Vector-only simpler, can add later | MVP 2 |
| Document Sync (OneDrive/SharePoint) | Manual upload sufficient for pilot | MVP 2 |
| Advanced Workflows | Focus on core Q&A + generation first | MVP 3 |
| Persona Agents | Platform feature, not core RAG | MVP 3 |
| Template Designer | Can use simple prompts initially | MVP 3 |

### Future Vision (MVP 2 & 3)

**MVP 2: Advanced Knowledge Base**
- Hybrid retrieval (Vector + BM25 + Graph)
- Document sync from cloud storage
- Advanced parsing (OCR, layout-aware)
- Quality scoring and compliance checks
- Template engine with intelligent slot-filling

**MVP 3: Configurable AI Workflow Engine**
- Visual workflow builder
- Persona agents with domain expertise
- Custom commands (/draft-proposal, /analyze-rfp)
- Quality gates with learning
- Full platform configurability

---

## Technical Preferences

### Deployment Model

| Preference | Details |
|------------|---------|
| **Primary** | On-premises (Docker Compose for dev, Kubernetes for production) |
| **Cloud-ready** | Design for future cloud deployment (AWS/Azure) |
| **Air-gapped capable** | Banking clients may require no external network calls |

### Technology Stack (Final - See Architecture Document)

> **Note:** Architecture decision ADR-001 selected Python + FastAPI monolith over the Go + Python microservices approach proposed in brainstorming. See `docs/architecture.md` for full rationale.

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Next.js 15 | Modern React 19, SSR, great DX |
| **Backend API** | Python + FastAPI | Unified with RAG ecosystem, async performance, simpler ops |
| **Background Jobs** | Celery + Redis | Async document processing, same decoupling as microservices |
| **Vector DB** | Qdrant | Open-source, self-hosted, excellent performance |
| **Metadata DB** | PostgreSQL | Reliable, feature-rich, widely supported |
| **Document Storage** | MinIO | S3-compatible, self-hosted blob storage |
| **LLM Gateway** | LiteLLM Proxy | Provider flexibility, fallback, cost tracking |

### Integration Requirements

- **MVP 1**: Standalone - no external integrations required
- **MVP 2**: Document sync (OneDrive, SharePoint, Google Drive)
- **Future**: SSO/SAML, API integrations

---

## Organizational Context

### Industry Vertical

**Banking & Financial Services**

This positions LumiKB for a demanding market with:
- High compliance requirements
- Sensitive data handling
- Strong security expectations
- Premium pricing potential
- Long sales cycles but sticky customers

### Target Customer Profile (For Productization)

| Segment | Characteristics | Why LumiKB Fits |
|---------|-----------------|-----------------|
| **Mid-size Banks** | 500-5000 employees, regional focus | Need efficiency, can't afford custom solutions |
| **Financial Consultancies** | Professional services, proposal-heavy | RFP/RFI response is core business activity |
| **Insurance Companies** | Product complexity, regulatory docs | Knowledge management critical for compliance |
| **FinTech Companies** | Fast-moving, documentation debt | Need to scale knowledge as team grows |

### Compliance Requirements

| Framework | Relevance | LumiKB Implications |
|-----------|-----------|---------------------|
| **SOC 2 Type II** | Required for B2B SaaS in finance | Audit logging, access controls, encryption at rest/transit |
| **GDPR** | If serving EU clients or employees | Data residency, right to deletion, consent management |
| **PCI-DSS** | If any payment card data in documents | Data isolation, encryption, access logging |
| **ISO 27001** | Common in banking sector | Information security management system alignment |
| **Bank Secrecy Act (BSA)** | US banking regulation | Audit trails, data retention policies |

### Compliance Design Principles (Build Into MVP 1)

1. **Audit Logging** - Every action logged with user, timestamp, resource
2. **Encryption at Rest** - All documents and vectors encrypted
3. **Encryption in Transit** - TLS 1.3 for all communications
4. **Role-Based Access** - KB-level isolation, no data leakage between tenants
5. **Data Residency** - On-prem deployment ensures data stays in jurisdiction
6. **Retention Policies** - Configurable document retention and deletion

---

## Risks and Assumptions

### Key Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Complexity Creep** | HIGH | HIGH | Strict MVP scoping, defer features aggressively, validate at each phase |
| **Stack Complexity** | MEDIUM | HIGH | Start with fewer components (no Neo4j, no Meilisearch in MVP 1) |
| **Retrieval Quality** | MEDIUM | HIGH | Iterative tuning, user feedback loops, fallback to keyword search |
| **LLM Cost/Latency** | MEDIUM | MEDIUM | LiteLLM for provider flexibility, caching, local model option |
| **User Adoption** | LOW | HIGH | Pilot with pain-point users, measure time savings, iterate on UX |
| **Security Vulnerabilities** | LOW | CRITICAL | Security review at each phase, penetration testing before prod |

### Critical Assumptions

| Assumption | If Wrong... | Validation Plan |
|------------|-------------|-----------------|
| Users will upload documents | No knowledge = no value | Pilot with 100-500 docs, measure upload friction |
| Semantic search beats keyword | Users won't trust results | A/B test retrieval quality, measure click-through |
| Draft generation saves time | Core value prop fails | Time-tracking in pilot, user interviews |
| On-prem deployment is acceptable | Need cloud option sooner | Survey target customers on deployment preferences |

### Complexity Management Strategy

**"Start Simple, Prove Value, Then Expand"**

1. **MVP 1**: Minimal viable stack
   - Vector search only (no hybrid)
   - Simple parsers (no DeepDoc)
   - Manual upload (no sync)
   - Basic RBAC (no hierarchy)

2. **Gate before expanding**: Each MVP must prove value before adding complexity

3. **One new capability at a time**: Don't add Graph RAG AND BM25 AND sync simultaneously

4. **User feedback drives prioritization**: What do pilot users actually need next?

---

## Supporting Materials

### Source Documents

| Document | Key Insights Used |
|----------|-------------------|
| [04-brainstorming-session-results-2025-11-22.md](04-brainstorming-session-results-2025-11-22.md) | 25 capabilities, MATCH→MERGE→MAKE pattern, 3 MVP phases, architecture decisions |
| [01-solution-idea.md](01-solution-idea.md) | Initial requirements and technology preferences |
| [02-first-commend.md](02-first-commend.md) | First architecture blueprint |
| [03-second-commend.md](03-second-commend.md) | Refined architecture with full tech stack |

---

_This Product Brief captures the vision and requirements for LumiKB._

_It was created through collaborative discovery and reflects the unique needs of this enterprise platform project targeting the Banking & Financial Services sector._

_Next: PRD workflow will transform this brief into detailed planning artifacts._
