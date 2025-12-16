# Sprint Change Proposal: Markdown-First Document Processing

## Change Request Summary

**Date:** 2025-12-10
**Approved:** 2025-12-11
**Requested By:** User
**Type:** Feature Enhancement
**Priority:** Medium
**Estimated Effort:** 10 story points (~8-12 hours)
**Status:** ✅ APPROVED - Stories added to Epic 7

---

## Correct-Course Workflow Results

**Triggering Story:** Story 5-26 (Document Chunk Viewer Frontend)
**Issue Type:** Technical limitation discovered during implementation
**Category:** TD-5.26-2 (chunk viewer position accuracy for non-markdown formats)

### Impact Analysis Summary

| Area | Impact | Details |
|------|--------|---------|
| **PRD** | None | Supports existing FR28a (view source documents), FR28b (highlight relevant sections) |
| **Architecture** | Minimal | Extends existing MinIO `.parsed.json` pattern |
| **Epic 7** | +4 stories | Stories 7-28 to 7-31 added (10 points) |
| **Other Epics** | None | No dependencies or conflicts |
| **Existing Code** | Low | New functionality, no breaking changes |

### Path Forward Selected

**Option 1: Direct Adjustment** ✅
- Add 4 new stories to Epic 7
- Implement incrementally (DOCX first, then PDF)
- No rollback required
- No PRD/MVP changes needed

---

## Problem Statement

The current chunk viewer has position accuracy issues when displaying where a chunk came from in the original document:

| Format | Current Behavior | Issue |
|--------|------------------|-------|
| **PDF** | Page-level navigation only | No character-level highlighting |
| **DOCX** | Scroll position estimation | Imprecise, uses ratio calculation |
| **Markdown/Text** | Line-based highlighting | Already accurate |

Users cannot see the exact location of a chunk within PDF/DOCX documents, making it difficult to verify context and citations.

## Proposed Solution

Implement **Markdown-First Document Processing** - convert PDF/DOCX to Markdown during parsing, store the markdown content, and use it for:
1. Accurate chunk position display (character offsets work in markdown)
2. A dedicated Markdown viewer for all document types
3. Consistent highlighting across all formats

### Architecture Change

```
CURRENT FLOW:
PDF/DOCX → unstructured → text + elements → chunk → embed → Qdrant
                                              ↓
                              Chunk viewer uses original file (imprecise)

PROPOSED FLOW:
PDF/DOCX → unstructured → elements → Markdown → chunk → embed → Qdrant
                                        ↓
                              Store in MinIO (.parsed.json)
                                        ↓
                              Chunk viewer uses Markdown (precise highlighting)
```

## User Requirements

1. **Storage**: Option A - Store markdown in MinIO (no database migration)
2. **Scope**: Start with DOCX, then add PDF support
3. **Display**: View documents in a nice Markdown viewer with accurate chunk highlighting

## Technical Analysis

### Existing Infrastructure (Ready to Use)

| Component | Status | Location |
|-----------|--------|----------|
| Markdown parsing | ✅ Exists | `backend/app/workers/parsing.py:parse_markdown()` |
| DOCX→HTML conversion | ✅ Exists | `mammoth` library, used in `documents.py` |
| Parsed content storage | ✅ Exists | MinIO `.parsed.json` pattern |
| Character offset tracking | ✅ Exists | `char_start`, `char_end` in chunks |
| Markdown viewer | ✅ Exists | `frontend/src/components/documents/chunk-viewer/viewers/markdown-viewer.tsx` |

### Missing Components

| Component | Effort | Description |
|-----------|--------|-------------|
| HTML→Markdown converter | Low | Add `markdownify` library (~15KB) |
| Markdown generation | Medium | New function `elements_to_markdown()` |
| Store markdown in parsed content | Low | Extend `.parsed.json` structure |
| Markdown content API endpoint | Low | `GET /documents/{id}/markdown-content` |
| Enhanced markdown viewer | Medium | Apply TextViewer's highlighting logic |

### Dependencies to Add

```toml
# backend/pyproject.toml [worker extras]
"markdownify>=0.11.0,<1.0.0",  # HTML to Markdown conversion
```

## Implementation Plan

### Phase 1: DOCX to Markdown (Priority)

**Backend Changes:**
1. Add `markdownify` dependency to `pyproject.toml`
2. Create `elements_to_markdown()` function in `parsing.py`
3. Extend `ParsedContent` dataclass with optional `markdown_content` field
4. Update `parsed_content_storage.py` to include markdown
5. Add `/documents/{id}/markdown-content` endpoint

**Frontend Changes:**
1. Update chunk viewer to fetch markdown content
2. Enhance `markdown-viewer.tsx` with line-based highlighting (copy from TextViewer)
3. Add toggle to switch between original view and markdown view

### Phase 2: PDF to Markdown (Follow-up)

1. Extend `parse_pdf()` to generate markdown with page markers
2. Include page numbers as HTML comments: `<!-- page:5 -->`
3. Handle tables, lists, and formatting preservation

## Files to Modify

### Backend
| File | Change |
|------|--------|
| `backend/pyproject.toml` | Add `markdownify>=0.11.0` |
| `backend/app/workers/parsing.py` | Add `elements_to_markdown()`, update parsers |
| `backend/app/services/parsed_content_storage.py` | Handle `markdown_content` field |
| `backend/app/api/v1/documents.py` | Add markdown content endpoint |
| `backend/app/schemas/document.py` | Add `MarkdownContentResponse` schema |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/components/documents/chunk-viewer/viewers/markdown-viewer.tsx` | Add line-based highlighting |
| `frontend/src/app/(protected)/documents/[id]/chunks/page.tsx` | Fetch and use markdown content |
| `frontend/src/components/documents/chunk-viewer/index.tsx` | Add view mode toggle |

## Acceptance Criteria

### AC-1: DOCX Markdown Conversion
- [ ] DOCX documents are converted to Markdown during parsing
- [ ] Markdown preserves headings, lists, tables, and formatting
- [ ] Markdown is stored in MinIO alongside parsed content

### AC-2: Markdown Content API
- [ ] New endpoint returns markdown content for a document
- [ ] Returns 404 if markdown not available (older documents)
- [ ] Handles documents that are still processing

### AC-3: Chunk Viewer Enhancement
- [ ] Markdown viewer displays document with proper formatting
- [ ] Selected chunk is highlighted with exact character position
- [ ] Highlighting is visually clear (background color + scroll into view)

### AC-4: View Mode Toggle
- [ ] User can switch between "Original" and "Markdown" views
- [ ] Default to Markdown view when available
- [ ] Graceful fallback to original viewer if markdown unavailable

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Markdown loses complex formatting | Medium | Keep original file, markdown is supplementary |
| Older documents lack markdown | Low | Graceful fallback to existing viewers |
| Storage overhead | Low | Markdown is text-only, minimal increase |
| Processing time increase | Low | Generate in same parsing step |

## Definition of Done

- [ ] DOCX→Markdown conversion implemented and tested
- [ ] Markdown stored in MinIO parsed content
- [ ] API endpoint for markdown content working
- [ ] Chunk viewer displays markdown with accurate highlighting
- [ ] View mode toggle functional
- [ ] Unit tests for markdown generation
- [ ] Integration tests for API endpoint
- [ ] E2E tests for chunk viewer enhancement
- [ ] Code review approved

## Stories Added to Epic 7

| Story | Points | Description | Status |
|-------|--------|-------------|--------|
| **7-28** | 3 | Markdown Generation from DOCX/PDF (Backend) | `backlog` |
| **7-29** | 2 | Markdown Content API Endpoint (Backend) | `backlog` |
| **7-30** | 3 | Enhanced Markdown Viewer with Highlighting (Frontend) | `backlog` |
| **7-31** | 2 | View Mode Toggle for Chunk Viewer (Frontend) | `backlog` |
| **Total** | **10** | | |

### Story Dependencies

```
7-28 (Markdown Generation)
  └── 7-29 (API Endpoint)
        └── 7-30 (Enhanced Viewer)
              └── 7-31 (View Toggle)
```

### Implementation Sequence

1. **Story 7-28** (Backend First)
   - Add `markdownify>=0.11.0` dependency
   - Create `elements_to_markdown()` function
   - Extend `ParsedContent` dataclass
   - Store markdown in MinIO `.parsed.json`

2. **Story 7-29** (Backend API)
   - `GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content`
   - Handle 404 for older documents
   - Handle 400 for processing documents

3. **Story 7-30** (Frontend Viewer)
   - `useMarkdownContent` hook
   - Character-based highlighting (`char_start`/`char_end`)
   - Graceful fallback to original viewer

4. **Story 7-31** (Frontend Toggle)
   - "Original" / "Markdown" toggle component
   - localStorage preference persistence
   - Disabled state when markdown unavailable

---

## Related Documentation

- [Epic 7: Infrastructure & DevOps](../epics/epic-7-infrastructure.md) - Stories 7.28-7.31
- [Chunk Viewer Implementation](5-25-document-chunk-viewer-backend.md)
- [Document Processing Pipeline](../architecture.md)
- [Sprint Status Tracking](sprint-status.yaml) - `7-28-*` through `7-31-*`

---

## Approval Record

| Step | Date | Action | By |
|------|------|--------|-----|
| Proposal Created | 2025-12-10 | Initial proposal drafted | User |
| Correct-Course Started | 2025-12-11 | Workflow initiated | SM Agent |
| Impact Analysis | 2025-12-11 | Sections 1-4 completed | SM Agent |
| Stories Drafted | 2025-12-11 | 4 stories defined with ACs | SM Agent |
| Epic Updated | 2025-12-11 | Stories added to epic-7-infrastructure.md | SM Agent |
| Sprint Status Updated | 2025-12-11 | Tracking entries added to sprint-status.yaml | SM Agent |
| **APPROVED** | 2025-12-11 | User approved all changes | User |

---

## Implementation Handoff

**Ready for Development:** Stories 7-28 through 7-31 are now in the backlog.

**Recommended Priority:** After current in-progress stories complete.

**Prerequisites:**
- Story 7-28 has no prerequisites (can start immediately)
- Stories 7-29, 7-30, 7-31 must be completed in sequence

**SM Note:** Execute via `dev-story` workflow when ready to implement.
