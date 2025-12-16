# Technical Debt: Document Chunk Viewer Defects

**Created:** 2025-12-08
**Priority:** LOW
**Status:** DEFERRED - Consolidated
**Reporter:** Tung Vu (via Dev Agent)
**Story:** 7-8-ui-scroll-isolation-fix

---

## Migration Notice

> **CONSOLIDATED:** These items are tracked in the single-source-of-truth tracker.
> See: **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**
>
> **Tracked Items:**
> - TD-7.8-1: Chunk-to-Document Position Sync (LOW - P3)
> - TD-7.8-2: Chunk Search Semantic Enhancement (LOW - P4)

---

## Executive Summary

**TWO defects** identified in the Document Chunk Viewer feature (Stories 5-25, 5-26):

1. **TD-7.8-1:** Incorrect chunk-to-document position sync (chunk highlighting mismatch)
2. **TD-7.8-2:** Chunk search uses semantic search, not text search

Both are UX issues that don't block core functionality. Scroll isolation (AC-7.8.1-7.8.3) works correctly.

---

## TD-7.8-1: Chunk-to-Document Position Sync Mismatch

### Symptoms

- User clicks chunk in sidebar → document viewer scrolls but highlights incorrect text
- Position offset accumulates across chunks (later chunks more misaligned)
- Issue most visible in large documents with many chunks

### Root Cause Analysis

**Location:** Backend document extraction/chunking pipeline

**Problem 1: Chunk position calculation uses `text.find()` with fallback**

File: [backend/app/workers/chunking.py:268-275](../../backend/app/workers/chunking.py#L268-L275)

```python
chunk_start = parsed_content.text.find(sub_chunk, max(0, char_offset - 100))
if chunk_start == -1:
    chunk_start = char_offset  # Fallback: approximate position
```

When `text.find()` returns -1 (chunk not found verbatim), the fallback uses approximate position which may be incorrect.

**Problem 2: Document content API has two different text sources**

File: [backend/app/api/v1/documents.py:1310-1335](../../backend/app/api/v1/documents.py#L1310-L1335)

```python
# Primary: Load from parsed content storage
parsed = await load_parsed_content(kb_id, doc_id)
text_content = parsed.text if parsed else None

# Fallback: Reconstruct from chunks
if not text_content:
    chunks_response = await chunk_service.get_chunks(...)
    text_content = "\n\n".join(chunk.text for chunk in chunks_response.chunks)
```

- **Primary path:** Uses original `parsed_content.text` - positions are correct
- **Fallback path:** Reconstructs text with `\n\n` separators - positions don't match stored `char_start`/`char_end`

**Problem 3: Text extraction may normalize whitespace differently**

File: [backend/app/workers/parsing.py](../../backend/app/workers/parsing.py)

Different document formats (PDF, DOCX, TXT) have different whitespace handling during extraction. The extracted text may have different character counts than the original display rendering.

### Why This Belongs to Document Extraction Module

The `char_start`/`char_end` values are calculated during chunking based on `parsed_content.text`. If the viewer receives text from a different source (reconstruction) or if the original text extraction normalizes whitespace, positions won't align.

**Fix should be in:**
- `backend/app/workers/chunking.py` - More robust position calculation
- `backend/app/workers/parsing.py` - Consistent whitespace handling
- `backend/app/api/v1/documents.py` - Always use same text source

### Proposed Fix

```python
# Option A: Store original parsed text reliably
# Ensure load_parsed_content() always works (persistent storage)

# Option B: Calculate char offsets relative to reconstructed text
# Re-calculate positions when serving content via fallback

# Option C: Use chunk_index instead of char positions
# Frontend highlights based on chunk boundaries, not character offsets
```

### Acceptance Criteria for Fix

- [ ] Click chunk 1 → highlights exact chunk 1 text in viewer
- [ ] Click chunk N → highlights exact chunk N text in viewer
- [ ] Works for all document types (PDF, DOCX, TXT, MD)
- [ ] Works when parsed content is loaded from storage
- [ ] Works when text is reconstructed from chunks

---

## TD-7.8-2: Chunk Search Uses Semantic Search (Not Text Search)

### Symptoms

- User types "authentication" in chunk search
- Results ranked by embedding similarity, not exact text match
- User may not see chunks containing exact keyword

### Root Cause Analysis

**Location:** Backend chunk service

File: [backend/app/services/chunk_service.py:204-286](../../backend/app/services/chunk_service.py#L204-L286)

```python
async def _search_chunks(self, search_query: str, ...):
    # Story 7-17 (2025-12-17): Resolve KB embedding model
    # This ensures query embedding dimensions match indexed vectors
    embedding_model_config = None
    if self._kb_config_resolver:
        embedding_model_config = (
            await self._kb_config_resolver.get_kb_embedding_model(self.kb_id)
        )

    # Generate query embedding with KB-specific model
    if embedding_model_config:
        client = LiteLLMEmbeddingClient(
            model=embedding_model_config.model_id,
            provider=embedding_model_config.provider,
            api_base=embedding_model_config.api_endpoint,
        )
        embeddings = await client.get_embeddings([search_query])
    else:
        embeddings = await embedding_client.get_embeddings([search_query])

    query_vector = embeddings[0]

    # Search with embedding
    search_result = await qdrant_service.search(
        collection_name=self.collection_name,
        query_vector=query_vector,  # Vector similarity search
        ...
    )
```

**Current Behavior:**
- User search query → embedded via KB's configured embedding model (Story 7-17 enhancement)
- Falls back to system default if KB has no custom embedding model
- Qdrant performs vector similarity search using `query_points` API (qdrant-client 1.16+)
- Returns semantically similar chunks (not text matches)

**Expected Behavior:**
- Text search should find exact/partial text matches
- Like "Ctrl+F" in a document

### Why This is Deferred

Semantic search is correct behavior for the current implementation. Adding text search requires:
1. Full-text index in Qdrant payload fields
2. Or separate PostgreSQL full-text search on chunk text
3. UI option to toggle search mode (semantic vs text)

This is a feature enhancement, not a bug fix.

### Proposed Fix

```python
# Option A: Qdrant payload search (if indexed)
scroll_filter = qdrant_models.Filter(
    must=[
        doc_filter,
        qdrant_models.FieldCondition(
            key="chunk_text",
            match=qdrant_models.MatchText(text=search_query)
        )
    ]
)

# Option B: Hybrid search
# 1. Do text filter first
# 2. Then rank by semantic similarity

# Option C: Add search mode toggle
# User chooses: "Semantic" (default) or "Text"
```

### Acceptance Criteria for Fix

- [ ] New search mode: "Text Search" (exact/partial match)
- [ ] Default: "Semantic Search" (current behavior)
- [ ] UI toggle or dropdown to switch modes
- [ ] Text search highlights matching text in results

---

## Priority Assessment

| ID | Issue | Impact | Complexity | Priority |
|----|-------|--------|------------|----------|
| TD-7.8-1 | Position sync mismatch | Medium - UX degradation | High - touches parsing, chunking, API | **P3** |
| TD-7.8-2 | Search is semantic-only | Low - works, just unexpected | Medium - new search mode | **P4** |

**Recommendation:** Defer both to Epic 8+ or future polish sprint. Core chunk viewer functionality works.

---

## Related Files

### Backend
- `backend/app/workers/chunking.py` - Chunk position calculation
- `backend/app/workers/parsing.py` - Text extraction
- `backend/app/services/chunk_service.py` - Chunk search
- `backend/app/api/v1/documents.py` - Content API

### Frontend
- `frontend/src/components/documents/chunk-viewer/document-chunk-viewer.tsx` - Main viewer
- `frontend/src/components/documents/chunk-viewer/chunk-sidebar.tsx` - Chunk list/search
- `frontend/src/components/documents/chunk-viewer/viewers/text-viewer.tsx` - Text highlighting
- `frontend/src/hooks/useDocumentChunks.ts` - Chunk fetching
- `frontend/src/hooks/useDocumentContent.ts` - Content fetching

---

## Story 7-8 Completion Status

Despite these deferred issues, **Story 7-8 is DONE**:

**Completed:**
- [x] AC-7.8.1: Document viewer panel scrolls independently from chunk sidebar
- [x] AC-7.8.2: Chunk sidebar scrolls independently from document viewer panel
- [x] AC-7.8.3: Scroll isolation maintained after panel resize via drag handle

**Evidence:**
- `overscroll-behavior: contain` applied to all scrollable containers
- Split-pane resize works without scroll interference
- Tested in Chrome (primary development browser)

**Deferred (not blocking):**
- TD-7.8-1: Position sync (extraction module issue)
- TD-7.8-2: Text search (feature enhancement)

---

## References

- Story: [7-8-ui-scroll-isolation-fix.md](./7-8-ui-scroll-isolation-fix.md)
- Story 5-25: Document Chunk Viewer Backend
- Story 5-26: Document Chunk Viewer Frontend
- MDN: [overscroll-behavior](https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior)
