# Epic 7 Retrospective: Infrastructure & DevOps

**Date:** 2025-12-17
**Facilitator:** Bob (Scrum Master)
**Epic:** 7 - Infrastructure & DevOps
**Stories Completed:** 32/32 (100%)
**Total Story Points:** 116
**Duration:** ~10 days (2025-12-07 to 2025-12-17)

---

## Epic 7 Snapshot

| Metric | Value |
|--------|-------|
| **Stories** | 32 stories completed |
| **Story Points** | 116 SP delivered |
| **Velocity** | ~11.6 SP/day |
| **Code Reviews** | All APPROVED |
| **Test Coverage** | High (unit + integration tests per story) |

---

## Major Features Delivered

1. **Docker E2E Infrastructure & CI/CD Pipeline** (Stories 7.1-7.5)
2. **Backend Unit Test Fixes & Async Qdrant Migration** (Stories 7.6-7.8)
3. **LLM Model Registry with Multi-Provider Support** (Stories 7.9-7.10)
4. **Navigation Restructure with RBAC** (Story 7.11) - Users, Operators, Administrators
5. **KB-Level Configuration System** (Stories 7.12-7.17)
   - Chunking, Retrieval, Generation, Prompts settings
   - KBConfigResolver with Request→KB→System precedence
   - Presets (Legal, Technical, Creative, Code, General)
6. **Tech Debt Resolution** (Stories 7.18-7.23)
   - Document Worker KB Config, Export Audit Logging
   - Feedback Button Integration, Draft Validation Warnings
   - SSE Reconnection Logic, Feedback Analytics Dashboard
7. **KB Archive/Restore/Delete** (Stories 7.24-7.26)
8. **Queue Monitoring Enhancement** (Story 7.27)
9. **Markdown-First Document Processing** (Stories 7.28-7.31)
   - Markdown generation from DOCX/PDF
   - Precise chunk highlighting in viewer
   - View mode toggle (Original/Markdown)
10. **Docling Parser Integration** (Story 7.32)
    - Feature-flagged alternative parser
    - Strategy pattern with auto-fallback

---

## What Went Well

### 1. LLM Model Registry Architecture
- Multi-provider support (Ollama, OpenAI, Anthropic, Azure, Cohere)
- Per-KB model assignment with Qdrant collection auto-creation
- Clean separation: embedding vs. generation models

### 2. KB Settings System Design
- Typed Pydantic schemas (ChunkingConfig, RetrievalConfig, GenerationConfig, etc.)
- KBConfigResolver with 3-tier precedence (Request→KB→System)
- Clean UI with General, Models, Advanced, Prompts tabs

### 3. RBAC with Cumulative Permissions
- Three levels: User (1), Operator (2), Administrator (3)
- `@require_permission(level)` decorator for endpoints
- `MAX(permission_level)` across groups for multi-group users

### 4. Markdown-First Feature Chain
- Stories 7.28→7.29→7.30→7.31 delivered precise chunk highlighting
- Graceful fallback to original viewers when markdown unavailable
- 34+ tests for Enhanced Markdown Viewer alone

### 5. Docling Parser Strategy Pattern
- Feature flag: `LUMIKB_PARSER_DOCLING_ENABLED`
- KB setting: `processing.parser_backend` (unstructured/docling/auto)
- Auto-fallback on failure - safe rollout pattern

### 6. Correct-Course Process
- Story 7.32 added mid-sprint and integrated smoothly
- Process for adapting to new requirements is mature

---

## What Could Be Improved

### 1. Testing Documentation Gap (HIGH PRIORITY)
**Raised by:** Tung Vu (Project Lead)

Testers lack comprehensive documentation for:
- API endpoints reference
- Database credentials and connection strings
- Authentication flow for API testing
- Hybrid setup (local frontend/backend + containerized services)
- Environment configuration guide

**Impact:** Trial and error instead of efficient testing. New team members struggle to get started.

### 2. Deferred AC from Story 7.32
- AC-7.32.3 (Parser Selection UI in KB Settings) deferred as optional
- Backend complete, UI needs future work

### 3. External Library API Changes
- qdrant-client 1.16+ changed `search()` to `query_points()`
- Caused debugging time during Story 7.7

### 4. Epic 6 Action Items Not Addressed
- `formatBytes()` still duplicated in 3 files
- `DuplicateInfo` type still defined in 2 places

---

## Key Technical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **Feature flag + Strategy pattern** | Safe rollouts, easy disable | Good - Docling pattern for future features |
| **KBSettings Pydantic schemas** | Type safety, validation | Good - Clean config management |
| **Cumulative RBAC (1-2-3)** | Simple permission model | Good - Easy to understand |
| **Markdown-First with fallback** | Better UX without breaking old docs | Good - Graceful degradation |
| **KB-aware embedding in ChunkService** | Correct dimensions when KB has custom model | Good - Fixed search accuracy |

---

## Metrics Comparison

| Metric | Epic 6 | Epic 7 | Trend |
|--------|--------|--------|-------|
| Stories | 9 | 32 | Much larger scope |
| Story Points | 35 | 116 | 3.3x increase |
| Duration | ~1 day | ~10 days | Scaled appropriately |
| Test Coverage | 94% | High | Maintained |
| Critical Gaps | 0 | 1 (Testing Docs) | Identified for action |

---

## Key Learnings

### L1: Feature Flag + Strategy Pattern = Safe Rollouts
Story 7.32 (Docling) demonstrated the pattern:
- `LUMIKB_PARSER_DOCLING_ENABLED` feature flag
- Strategy pattern in `parsing.py`
- Auto-fallback on failure
- Test without production risk

### L2: KB-Level Configuration is Powerful
KBSettings schema + KBConfigResolver enables:
- Per-KB customization (chunking, retrieval, generation, prompts)
- Request-level overrides when needed
- System defaults as fallback
- Clean precedence: Request → KB → System

### L3: RBAC with Cumulative Permissions Simplifies Access Control
- Three levels: User (1), Operator (2), Administrator (3)
- Higher levels inherit lower permissions
- `MAX(permission_level)` for multi-group users
- Simple to explain and maintain

### L4: Correct-Course Process Works
- Story 7.32 added mid-sprint via correct-course proposal
- Integrated smoothly without disrupting other work
- Process for adapting to new requirements is mature

### L5: Testing Documentation is Critical (NEW)
- Missing testing documentation creates friction
- Testers need: API reference, credentials, auth guide, setup instructions
- Investment in documentation pays off in efficiency

---

## Action Items

### HIGH PRIORITY

| ID | Action | Owner | Deadline | Success Criteria |
|----|--------|-------|----------|------------------|
| **A1** | Create comprehensive Testing Guide | Dev/QA | Before Epic 8 Phase 2 | Document covers: API endpoints, credentials, auth flow, hybrid setup, example curl commands |
| **A2** | Add Parser Selection UI to KB Settings | Dev | Epic 8 or later | AC-7.32.3 satisfied - dropdown in Processing tab |

### MEDIUM PRIORITY (Carried from Epic 6)

| ID | Action | Owner | Deadline | Success Criteria |
|----|--------|-------|----------|------------------|
| A3 | Extract `formatBytes()` to shared utility | Dev | Ongoing | Single source in `frontend/src/lib/utils.ts` |
| A4 | Consolidate `DuplicateInfo` type | Dev | Ongoing | Single source in `frontend/src/types/` |

### LOW PRIORITY

| ID | Action | Owner | Deadline | Success Criteria |
|----|--------|-------|----------|------------------|
| A5 | Pin qdrant-client version | Dev | Next dependency update | Version locked in pyproject.toml |
| A6 | Batch small tech debt stories differently | SM | Epic 9 planning | Consider grouping by area |

---

## Previous Retrospective Follow-Through (Epic 6)

| Action Item | Status | Notes |
|-------------|--------|-------|
| A1: Extract `formatBytes()` | ⏳ Not addressed | Carried forward |
| A2: Consolidate `DuplicateInfo` type | ⏳ Not addressed | Carried forward |
| A3: Permission rejection tests | ⏳ Not addressed | Low priority |
| A4: Search verification test | ⏳ Not addressed | Low priority |
| A5: "Type DELETE to confirm" UX | ⏳ Not addressed | Low priority |
| A6: Error handling in bulk purge | ✅ Addressed | In Story 7.24-7.26 |

---

## Epic 8 Preparation

### Ready to Start
- **Story 8.0 (Query Rewriting)** - No GraphRAG dependencies
  - Uses existing LiteLLM infrastructure
  - Can improve chat quality immediately

### GraphRAG Foundation (Phase 1)
Stories 8.1-8.7 require:
- Neo4j Docker infrastructure
- Domain data model and migrations
- Domain management UI

### Dependencies Satisfied
- ✅ LLM Model Registry (Story 7.9) - Complete
- ✅ Debug Mode (Story 9.15) - Complete

### Critical Path
1. **A1: Testing Guide** - Needed for QA validation of Epic 8

---

## What's Next?

With Epic 7 complete, LumiKB now has:
- Full LLM Model Registry with multi-provider support
- KB-level configuration for chunking, retrieval, generation, prompts
- RBAC with three permission levels
- KB Archive/Restore/Delete functionality
- Markdown-first document processing with precise highlighting
- Docling parser as alternative backend (feature-flagged)

**Remaining Epics:**
- Epic 8: GraphRAG Integration (18 stories, 81 SP)
- Epic 9: Observability (4 stories ready-for-dev)

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Scrum Master | Bob | 2025-12-17 |
| Project Lead | Tung Vu | 2025-12-17 |

---

*Epic 7 delivered successfully with high velocity (116 SP in ~10 days). Key improvement area identified: Testing documentation.*
