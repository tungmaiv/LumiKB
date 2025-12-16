# Sprint Change Proposal: Docling Document Parser Integration

**Date:** 2025-12-16
**Proposal ID:** SCP-2025-12-16-DOCLING
**Status:** APPROVED
**Author:** SM (Scrum Master Agent)

---

## 1. Identified Issue

### Summary

During research for document processing improvements, the **Docling** library was identified as a superior alternative to the current Unstructured library. This is a scope addition opportunity that can provide significant value with minimal risk through feature-flagged implementation.

### Issue Type

- [x] Scope addition (new capability)
- [ ] Technical limitation discovered
- [ ] New requirement emerged
- [ ] Misunderstanding of requirements
- [ ] Strategic pivot
- [ ] Failed approach

### Evidence

- **Docling GitHub**: 46.8k stars, active development
- **License**: MIT (fully permissible for commercial use)
- **Technical Report**: arxiv.org/abs/2408.09869
- **Capabilities**: Better table extraction (TableFormer), layout analysis (Heron model), 15+ document formats

---

## 2. Epic Impact Assessment

### Current Epic (Epic 7: Infrastructure & DevOps)

**Impact**: LOW - Self-contained feature addition

| Aspect | Assessment |
|--------|------------|
| Epic scope | Extended by 1 story (7.32) |
| Dependencies | None - builds on existing KB Settings (7.12, 7.14) |
| Timeline | +2 story points (116 total) |
| Risk to existing work | None - feature-flagged, backward compatible |

### Future Epics

**No impact on Epics 8-9**. Docling integration is isolated to document processing and doesn't affect GraphRAG (Epic 8) or Observability (Epic 9).

---

## 3. Artifact Conflict Analysis

### PRD Impact

**No conflicts**. The PRD's functional requirements for document processing (FR17-FR23) are preserved. Docling adds enhanced capability without changing core requirements.

### Architecture Impact

**Minor documentation update only**:
- Added Docling as optional document parser in technology stack (02-technology-stack.md)
- No structural or pattern changes required

### UI/UX Impact

**Minor addition** (optional):
- Document Parser dropdown in KB Settings > Processing tab
- Can be deferred to separate story if time-constrained

---

## 4. Recommended Path Forward

### Selected Approach: Option 1 - Direct Adjustment

Add Story 7.32 to Epic 7 with feature-flagged implementation.

| Factor | Assessment |
|--------|------------|
| Effort estimate | LOW (2 story points) |
| Risk level | LOW (feature-flagged, backward compatible) |
| Timeline impact | Minimal (+2 pts to Epic 7) |
| Technical complexity | LOW (strategy pattern, wrapper module) |

### Rationale

1. **Zero risk to existing functionality**: Feature flag (LUMIKB_PARSER_DOCLING_ENABLED=false by default) ensures no change to production behavior
2. **KB-level flexibility**: Administrators can enable per-KB for testing before organization-wide rollout
3. **Clean fallback**: Auto mode provides graceful degradation
4. **Future extensibility**: Opens path to additional document formats (PPTX, XLSX, HTML, images)

---

## 5. Implementation Plan

### Documents Updated

| Document | Status | Changes |
|----------|--------|---------|
| Epic 7 (epic-7-infrastructure.md) | DONE | Added Story 7.32 definition |
| Sprint Status (sprint-status.yaml) | DONE | Added 7-32 entry |
| Technology Stack (02-technology-stack.md) | DONE | Added Docling to integration points |
| KB Settings Schema (kb_settings.py) | DONE | Added DocumentParserBackend enum |
| Story 7.32 document | DONE | Created full specification |
| Story 7.32 context.xml | DONE | Created implementation context |

### Story 7.32 Scope

**Title**: Docling Document Parser Integration
**Points**: 2
**Type**: Feature Enhancement (Feature-Flagged)
**Branch**: feature/docling-parser-poc

**Key ACs**:
- AC-7.32.1: System-level feature flag (LUMIKB_PARSER_DOCLING_ENABLED)
- AC-7.32.2: KB setting (processing.parser_backend: unstructured/docling/auto)
- AC-7.32.4-6: Backward compatibility preserved
- AC-7.32.7-8: Strategy pattern implementation
- AC-7.32.9-10: Graceful fallback behavior

### Files to Create/Modify

| File | Action | Lines |
|------|--------|-------|
| backend/app/core/config.py | Modify | +4 |
| backend/app/schemas/kb_settings.py | Modify | +12 (DONE) |
| backend/app/workers/docling_parser.py | Create | ~200 |
| backend/app/workers/parsing.py | Modify | +40 |
| backend/app/workers/document_tasks.py | Modify | +8 |
| backend/pyproject.toml | Modify | +3 |
| backend/tests/unit/test_docling_parser.py | Create | ~120 |
| backend/tests/integration/test_parser_strategy.py | Create | ~80 |

---

## 6. Agent Handoff

### Dev Agent Responsibilities

1. Implement system-level feature flag in config.py
2. Create docling_parser.py module with ParsedContent output
3. Add strategy pattern to parsing.py
4. Update document_tasks.py to pass KB config
5. Add optional dependency to pyproject.toml
6. Write unit tests with mocked Docling
7. Write integration tests with conditional skip

### SM Agent Responsibilities

1. Monitor story progress
2. Conduct code review when story reaches review state
3. Update sprint-status.yaml upon completion

---

## 7. Approval

### User Approval

**Date**: 2025-12-16
**Decision**: APPROVED
**Conditions**: None

### Approval Notes

User explicitly approved with request: "please approve, please add story, update all related document prd, architecture, epics, epic context ect"

All requested documentation has been updated.

---

## 8. Summary

| Metric | Value |
|--------|-------|
| New stories added | 1 (Story 7.32) |
| Story points added | 2 |
| Epic 7 new total | 116 points (32 stories) |
| PRD changes | None |
| Architecture changes | Documentation only |
| Breaking changes | None |
| Feature flag | LUMIKB_PARSER_DOCLING_ENABLED (default: false) |
