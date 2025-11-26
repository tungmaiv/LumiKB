# Epic Technical Specification: Semantic Search & Citations

Date: 2025-11-25
Author: Tung Vu
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 delivers the **core differentiator** of LumiKB: semantic search with inline citations. This is "THE magic moment" where users ask natural language questions against their Knowledge Bases and receive synthesized answers with verifiable source citations.

This epic transforms LumiKB from a document storage system into an intelligent knowledge retrieval platform. The citation-first architecture ensures every AI-generated claim traces back to source documents, building the trust required for enterprise Banking & Financial Services deployments.

**User Value Statement:**
*"I can ask questions and get answers with citations I can trust - every claim shows me exactly where it came from."*

**Business Impact:**
- Enables Sarah (Sales Rep) to find winning proposal patterns in seconds
- Allows David (System Engineer) to discover past implementation approaches
- Validates the core MATCH capability of the MATCH → MERGE → MAKE vision
- Proves the citation system that differentiates LumiKB from generic AI tools

**Scope:**
11 stories implementing semantic search, answer synthesis with inline citations, cross-KB search, citation verification UI, quick search command palette, and audit logging.

## Objectives and Scope

### In Scope

**Core Capabilities:**
1. **Semantic Search Backend** (3.1) - Natural language search against Qdrant vector embeddings
2. **Answer Synthesis with Citations** (3.2) - LLM-generated answers with inline [n] markers mapped to source chunks
3. **Streaming Responses** (3.3) - SSE-based streaming for perceived speed
4. **Citation UI** (3.4, 3.5) - Inline citation markers, right panel with CitationCards, preview/navigation to sources
5. **Cross-KB Search** (3.6) - Search ALL permitted KBs by default, filter after results
6. **Quick Search & Command Palette** (3.7) - Cmd/Ctrl+K instant search overlay
7. **Search Result Actions** (3.8) - "Use in Draft", "View Source", "Find Similar"
8. **Relevance Explanation** (3.9) - Show WHY results are relevant
9. **Verify All Mode** (3.10) - Systematic citation verification flow
10. **Search Audit Logging** (3.11) - Compliance logging of all queries

**User Journey Coverage:**
- **Sarah's RFP Flow** (Primary): Search → Review results → Verify citations → Generate draft (handoff to Epic 4)
- **David's Discovery Flow**: Search → Find similar → Verify sources → Contribute knowledge

**Functional Requirements:**
- FR24-FR30 (Semantic Search & Q&A)
- FR24a-d (Quick Search variants)
- FR27a (Inline citations)
- FR28a-b (Source navigation)
- FR29a (Cross-KB default)
- FR30a-f (Confidence, explanations, actions)
- FR43-FR46 (Citation & Provenance)
- FR54 (Search audit logging)

### Out of Scope

**Deferred to Later Epics:**
- Document generation (Epic 4)
- Multi-turn chat conversations (Epic 4)
- Admin analytics on search patterns (Epic 5)
- Hybrid search (BM25 + vector) - Future enhancement
- Graph RAG relationships - Future enhancement
- Mobile-optimized search UI - Future

**Explicitly NOT in Epic 3:**
- Content creation/editing
- User management
- KB administration UI improvements
- Performance optimization beyond MVP targets

### Success Criteria

**Functional:**
- Users can search with natural language and receive relevant results in < 3 seconds
- Every AI answer includes inline citation markers [1], [2], etc.
- Clicking a citation navigates to the exact passage in source document
- Cross-KB search is default, single-KB filtering works
- Command palette (⌘K) provides instant search
- All search queries logged to audit.events

**Non-Functional:**
- Search response time: < 3 seconds (p95)
- Citation accuracy: 100% of markers map to valid sources
- UI responsiveness: Citations render without layout shift
- Confidence indicators: Always shown (never hidden)
- Accessibility: Full keyboard navigation, screen reader support

**User Acceptance:**
- Sarah can find RFP examples in < 10 seconds from query to verified citation
- David can discover past implementations across multiple KBs without knowing where they live
- First-time users understand citation verification in onboarding wizard

## System Architecture Alignment

### Components Introduced

**Backend Services:**
- `SearchService` (new) - Orchestrates semantic search and answer synthesis
- `CitationService` (new) - **THE CORE DIFFERENTIATOR** - Extracts citation markers, maps to source chunks, generates citation metadata
- `AuditService` (existing, extended) - Logs search queries per FR54

**Frontend Components:**
- `SearchBar` (new) - Always-visible top search input
- `CommandPalette` (new) - ⌘K quick search overlay (shadcn/ui Command component)
- `CitationMarker` (new) - Inline [n] clickable badges
- `CitationCard` (new) - Right panel citation display with preview/open actions
- `ConfidenceIndicator` (new) - Visual confidence bar with color coding
- `SearchResultCard` (new) - Result display with relevance explanation
- `VerifyAllMode` (new) - Sequential citation verification UI state

**Data Flow:**

**[View Interactive Diagram](../diagrams/epic3-search-dataflow-2025-11-25.excalidraw)** - Open in Excalidraw for full detail

![Search Data Flow](../diagrams/epic3-search-dataflow-2025-11-25.excalidraw)

The diagram shows the complete search pipeline from user query to frontend rendering, including:
- **Processes:** 1.0 Accept Query → 2.0 Generate Embedding → 3.0 Search Vectors → 4.0 Synthesize Answer → 5.0 Extract Citations → 6.0 Stream Response → 7.0 Log Audit Event
- **External Entities:** User, LiteLLM Service, Qdrant Service
- **Data Stores:** D2 (Audit Events/Postgres), D3 (Query Cache/Redis)
- **Data Flows:** All labeled arrows showing query, embeddings, vectors, chunks, citations, SSE events, and audit logs

### Integration Points

| External System | Purpose | Epic 3 Usage |
|-----------------|---------|--------------|
| **Qdrant** | Vector storage | Semantic search against kb_{id} collections |
| **LiteLLM Proxy** | LLM access | (1) Query embedding (2) Answer synthesis with citation instructions |
| **PostgreSQL** | Audit logs | Write search queries to audit.events |
| **Redis** | Caching | Cache frequent queries, embedding results |

### Architecture Patterns Used

1. **Citation-First Architecture** (ADR-005)
   - Rich metadata stored at indexing time (Epic 2)
   - CitationService as dedicated component
   - Inline markers + side panel UX pattern

2. **Streaming Responses**
   - FastAPI SSE for perceived speed
   - Token-by-token answer display
   - Immediate citation event on marker detection

3. **Cross-Service Queries**
   - Parallel Qdrant queries across permitted collections
   - Merge and re-rank by relevance score
   - Permission check per collection (reuse from Epic 2)

4. **Centralized Logging** (from architecture.md)
   - AuditService logs every search
   - Async write to avoid blocking response

### Alignment with Three-Panel Layout

Epic 3 completes the three-panel UX vision:

**[View Interactive Diagram](../diagrams/epic3-three-panel-layout-2025-11-25.excalidraw)** - Open in Excalidraw for full detail

![Three-Panel Layout](../diagrams/epic3-three-panel-layout-2025-11-25.excalidraw)

The diagram shows the complete three-panel interface:
- **Left Panel (240px):** KB List from Epic 2 - Shows Sales KB, Tech KB with selection state
- **Center Panel (flex-grow):** Search Results (Epic 3 NEW) - Query input, answer with [1][2] citations, result cards with relevance scores
- **Right Panel (360px):** Citations (Epic 3 NEW) - Citation cards [1], [2] with preview/open buttons, confidence indicator (88%), Verify All button

Left panel (KB sidebar) from Epic 2, center and right panels activated by Epic 3.

## Detailed Design

### Services and Modules

#### SearchService (`backend/app/services/search_service.py`)

**Responsibilities:**
- Orchestrate semantic search pipeline
- Coordinate between embedding, retrieval, and synthesis
- Calculate confidence scores
- Handle cross-KB search logic

**Key Methods:**

```python
class SearchService:
    async def search(
        self,
        query: str,
        kb_ids: list[str],
        user_id: str,
        limit: int = 10,
        stream: bool = False
    ) -> SearchResponse | AsyncGenerator[SSEEvent, None]:
        """
        Execute semantic search and return results with citations.

        If stream=True, yields SSE events:
        - {"type": "status", "content": "Searching..."}
        - {"type": "token", "content": "word"}
        - {"type": "citation", "data": {citation_metadata}}
        - {"type": "done", "confidence": 0.85}
        """

    async def _embed_query(self, query: str) -> list[float]:
        """Generate query embedding via LiteLLM."""

    async def _search_collections(
        self,
        embedding: list[float],
        kb_ids: list[str],
        limit: int
    ) -> list[SearchChunk]:
        """Search Qdrant collections in parallel, merge results."""

    async def _synthesize_answer(
        self,
        query: str,
        chunks: list[SearchChunk],
        stream: bool
    ) -> str | AsyncGenerator[str, None]:
        """Generate answer via LLM with citation instructions."""

    def _calculate_confidence(
        self,
        chunks: list[SearchChunk],
        query: str
    ) -> float:
        """
        Calculate confidence based on:
        - Average retrieval relevance scores
        - Number of supporting sources
        - Query-answer semantic similarity
        """
```

**Dependencies:**
- `CitationService` - for extracting and mapping citations
- `LiteLLMClient` - for embeddings and LLM synthesis
- `QdrantClient` - for vector search
- `AuditService` - for logging queries
- `PermissionService` (from Epic 2) - for KB access checks

**LLM System Prompt for Citations:**

```python
CITATION_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on provided source documents.

CRITICAL RULES:
1. Every factual claim MUST have a citation using [n] notation
2. Use [1] for first source, [2] for second source, etc.
3. Multiple sources for one claim: [1][2]
4. If information isn't in sources, say "I don't have information about that in the available documents."
5. Be concise but complete

Example:
"Our authentication approach uses OAuth 2.0 with PKCE [1] and supports MFA via TOTP [2]."

Sources:
[1] {chunk_1_text} (from {doc_1_name}, page {page_1})
[2] {chunk_2_text} (from {doc_2_name}, page {page_2})
"""
```

---

#### CitationService (`backend/app/services/citation_service.py`)

**THE CORE DIFFERENTIATOR**

**Responsibilities:**
- Extract citation markers [n] from LLM output
- Map markers to source chunks
- Build rich citation metadata for frontend
- Validate citation accuracy

**Key Methods:**

```python
@dataclass
class Citation:
    number: int
    document_id: str
    document_name: str
    page_number: int | None
    section_header: str | None
    excerpt: str  # ~200 chars
    char_start: int
    char_end: int
    confidence: float

class CitationService:
    def extract_citations(
        self,
        answer: str,
        source_chunks: list[SearchChunk]
    ) -> tuple[str, list[Citation]]:
        """
        Parse answer for [n] markers and map to sources.

        Returns:
            (answer_with_markers, citations_list)
        """

    def _find_markers(self, text: str) -> list[int]:
        """Extract all [n] patterns, return sorted unique numbers."""

    def _map_marker_to_chunk(
        self,
        marker_num: int,
        chunks: list[SearchChunk]
    ) -> Citation:
        """
        Map citation number to chunk.
        Uses 1-indexed (marker 1 → chunks[0]).
        """

    def validate_citation_coverage(
        self,
        answer: str,
        citations: list[Citation]
    ) -> float:
        """
        Calculate citation accuracy score:
        - % of sentences with citations
        - No orphaned markers (citation exists for every [n])
        """
```

**Citation Extraction Logic:**

```python
import re

CITATION_PATTERN = r'\[(\d+)\]'

def extract_markers(text: str) -> list[int]:
    """Find all [n] markers."""
    matches = re.findall(CITATION_PATTERN, text)
    return sorted(set(int(n) for n in matches))
```

**Chunk Metadata Structure** (from Epic 2 indexing):

```python
# Stored in Qdrant payload during document processing
{
    "document_id": "doc-uuid",
    "document_name": "Acme Bank Proposal.pdf",
    "page_number": 14,
    "section_header": "Authentication Architecture",
    "chunk_text": "OAuth 2.0 with PKCE flow ensures...",
    "char_start": 3450,
    "char_end": 3892
}
```

---

#### API Endpoints

**POST /api/v1/search** (New)

```python
@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    service: SearchService = Depends(get_search_service)
):
    """
    Semantic search with answer synthesis and citations.

    Query Params (optional):
        stream: bool = False  # Enable SSE streaming

    Returns:
        SearchResponse or SSE stream
    """
```

**Request Schema:**

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    kb_ids: list[str] | None = None  # None = search all permitted KBs
    limit: int = Field(default=10, ge=1, le=50)

class SearchResponse(BaseModel):
    query: str
    answer: str  # With inline [1], [2] markers
    citations: list[CitationSchema]
    confidence: float
    results: list[SearchResultSchema]  # Raw search results

class CitationSchema(BaseModel):
    number: int
    document_id: str
    document_name: str
    page_number: int | None
    section_header: str | None
    excerpt: str
    char_start: int
    char_end: int

class SearchResultSchema(BaseModel):
    document_id: str
    document_name: str
    kb_id: str
    kb_name: str
    chunk_text: str
    relevance_score: float
    page_number: int | None
    section_header: str | None
```

**SSE Event Types:**

```json
// Status update
{"type": "status", "content": "Searching knowledge bases..."}

// Answer token
{"type": "token", "content": "OAuth "}

// Citation event (when [n] detected)
{
  "type": "citation",
  "data": {
    "number": 1,
    "document_name": "Acme Proposal.pdf",
    "page_number": 14,
    ...
  }
}

// Completion
{"type": "done", "confidence": 0.88, "result_count": 5}
```

**POST /api/v1/search/quick** (New)

```python
@router.post("/quick")
async def quick_search(
    request: QuickSearchRequest,
    current_user: User = Depends(get_current_user),
    service: SearchService = Depends(get_search_service)
):
    """
    Lightweight search for command palette.
    Returns top 5 results without full answer synthesis.
    """
```

---

### Data Models and Contracts

**No new database tables** - Epic 3 is read-only against Epic 2 data.

**Qdrant Query Pattern:**

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Cross-KB search
results = await qdrant_client.search(
    collection_name=f"kb_{kb_id}",
    query_vector=embedding,
    limit=limit,
    with_payload=True  # Include all metadata
)

# Merge results from multiple KBs
all_results = []
for kb_id in kb_ids:
    kb_results = await search_single_kb(kb_id, embedding, limit)
    all_results.extend(kb_results)

# Re-rank by score
all_results.sort(key=lambda r: r.score, reverse=True)
return all_results[:limit]
```

**Redis Caching:**

```python
# Cache query embeddings (1 hour TTL)
cache_key = f"embedding:{hash(query)}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

embedding = await litellm.embed(query)
await redis.setex(cache_key, 3600, json.dumps(embedding))
```

---

### APIs and Interfaces

**Frontend API Client** (`frontend/src/lib/api/search.ts`)

```typescript
export interface SearchRequest {
  query: string;
  kbIds?: string[] | null;  // null = search all
  limit?: number;
}

export interface SearchResponse {
  query: string;
  answer: string;
  citations: Citation[];
  confidence: number;
  results: SearchResult[];
}

export interface Citation {
  number: number;
  documentId: string;
  documentName: string;
  pageNumber?: number;
  sectionHeader?: string;
  excerpt: string;
  charStart: number;
  charEnd: number;
}

export const searchApi = {
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await fetch('/api/v1/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return response.json();
  },

  // SSE streaming version
  searchStream(request: SearchRequest): EventSource {
    const url = `/api/v1/search?stream=true`;
    return new EventSource(url, {
      // ... SSE config
    });
  },
};
```

**SSE Event Handling:**

```typescript
// frontend/src/lib/hooks/use-search-stream.ts
export function useSearchStream(query: string) {
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const eventSource = searchApi.searchStream({ query });

    eventSource.addEventListener('token', (e) => {
      const { content } = JSON.parse(e.data);
      setAnswer(prev => prev + content);
    });

    eventSource.addEventListener('citation', (e) => {
      const citation = JSON.parse(e.data);
      setCitations(prev => [...prev, citation]);
    });

    eventSource.addEventListener('done', (e) => {
      setIsLoading(false);
      eventSource.close();
    });

    return () => eventSource.close();
  }, [query]);

  return { answer, citations, isLoading };
}
```

---

### Workflows and Sequencing

**Story 3.1-3.3: Search & Answer Synthesis Flow**

```
┌────────────────────────────────────────────────────────────┐
│  1. User enters query in SearchBar                         │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  2. Frontend: POST /api/v1/search?stream=true              │
│     { query, kbIds: null }  // null = search all           │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  3. SearchService.search()                                 │
│     a. Check user permissions for all KBs                  │
│     b. Generate query embedding (LiteLLM)                  │
│     c. Search Qdrant collections in parallel               │
│     d. Merge + re-rank results                             │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  4. SearchService._synthesize_answer()                     │
│     - Build system prompt with citation instructions       │
│     - Pass top-k chunks as context                         │
│     - Stream LLM response                                  │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  5. CitationService.extract_citations()                    │
│     a. Parse [1], [2] markers from answer                  │
│     b. Map markers to source chunks                        │
│     c. Build Citation objects with metadata                │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  6. SSE Events Streamed to Frontend                        │
│     {"type": "token", "content": "OAuth "}                 │
│     {"type": "token", "content": "2.0 "}                   │
│     {"type": "token", "content": "[1] "}                   │
│     {"type": "citation", "data": {citation_1_metadata}}    │
│     ...                                                    │
│     {"type": "done", "confidence": 0.88}                   │
└────────────────────┬───────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  7. Frontend Rendering                                     │
│     - Answer appears word-by-word in center panel          │
│     - [1], [2] markers render as CitationMarker badges     │
│     - Citations populate right panel as CitationCards      │
│     - ConfidenceIndicator shows 88% (green bar)            │
└────────────────────────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────┐
│  8. AuditService.log_search()  (async background)          │
│     INSERT INTO audit.events (user_id, action='search',    │
│       details={query, kb_ids, result_count})               │
└────────────────────────────────────────────────────────────┘
```

**Story 3.5: Citation Preview Flow**

```
User clicks CitationMarker [1]
    ↓
CitationPanel scrolls to CitationCard #1
    ↓
User clicks "Preview" on CitationCard
    ↓
Modal/Sheet opens with:
    - Document name
    - Page/section context
    - Highlighted excerpt (char_start to char_end)
    - Surrounding context (±200 chars)
    ↓
User clicks "Open Document"
    ↓
Navigate to /documents/{doc_id}?highlight={char_start}-{char_end}
    ↓
Document viewer scrolls to highlighted passage
```

**Story 3.6: Cross-KB Search Flow**

```
Default Behavior (kbIds = null):
    ↓
SearchService gets all KBs user has READ access to
    ↓
For each KB:
    Parallel async search against kb_{id} collection
    ↓
Merge results from all KBs
    ↓
Re-rank by relevance score (descending)
    ↓
Return top-k across all KBs
    ↓
Frontend displays with KB tag on each result:
    "Acme Bank Proposal.pdf | Sales KB | 92%"
```

**Story 3.10: Verify All Citations Flow**

```
User clicks "Verify All" button
    ↓
VerifyAllMode activates:
    state = { currentIndex: 0, verified: [] }
    ↓
Highlight citation [1] in answer + CitationPanel
Show preview for citation 1 automatically
    ↓
User reviews → clicks checkmark
    ↓
Add citation 1 to verified list
Increment currentIndex
Highlight citation [2]
    ↓
Repeat until all citations verified
    ↓
Show completion: "All 5 sources verified ✓"
Badge appears on answer: "Sources verified"
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement | Mitigation |
|--------|--------|-------------|------------|
| **Search response time** | < 3s (p95) | First token to client | (1) Cache query embeddings in Redis (2) Qdrant gRPC mode (3) Parallel KB queries |
| **Embedding generation** | < 500ms | LiteLLM API call | (1) Batch embeddings (2) Cache frequent queries |
| **Vector search** | < 1s per KB | Qdrant search latency | (1) HNSW index optimization (2) Limit top-k to 20 |
| **LLM synthesis** | First token < 1s | Time to first SSE token | (1) Streaming mode (2) Smaller context window (3) Fallback to cached answer if <5% query change |
| **Citation extraction** | < 100ms | Regex + mapping | (1) Optimized regex (2) Pre-build chunk lookup |
| **Concurrent searches** | 20+ users | Load test with k6 | (1) Async all the way (2) Connection pooling |

**Performance Testing:**
- k6 script for load testing search endpoint
- Simulate 20 concurrent users with 5 searches each
- Monitor Qdrant query times, LLM latency, Redis hit rates

### Security

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| **Permission enforcement** | Check KB read access before search | Unit test: unauthorized user gets 404 |
| **Query sanitization** | Pydantic validation, max 500 chars | Reject queries >500 chars, special chars escaped |
| **Result filtering** | Only return docs from permitted KBs | Integration test: user A can't see user B's KB results |
| **Audit logging** | Log every query with user_id | Verify audit.events has search entries |
| **Rate limiting** | 30 searches/minute per user | Reject 31st request with 429 |
| **PII in queries** | No PII detection in MVP (logged as-is) | Document risk, defer to Epic 5 |

**Security Testing:**
- Attempt cross-KB access without permission
- SQL injection via query parameter
- XXS via malicious query strings in audit logs

### Reliability/Availability

| Requirement | Implementation | Recovery |
|-------------|----------------|----------|
| **Qdrant unavailable** | Search fails gracefully | Return cached results if available, else friendly error "Search temporarily unavailable" |
| **LLM timeout** | 30s timeout on synthesis | Fallback: return raw chunks without synthesis |
| **Partial KB failure** | If 1 of 5 KBs fails, return results from other 4 | Log error, continue with available KBs |
| **Citation extraction error** | If regex fails, return answer without citations | Log warning, show disclaimer "Citations unavailable for this response" |
| **Streaming disconnect** | Client reconnects | Server keeps state for 60s, resume streaming |

**Graceful Degradation:**
1. LiteLLM slow → Cache previous similar queries
2. Qdrant slow → Return top-3 results instead of 10
3. Redis down → Skip caching, direct calls
4. All failures → Display error with "Try again" button

### Observability

| Signal | Metric | Alert Threshold |
|--------|--------|-----------------|
| **Search requests** | Count per minute | > 100/min (capacity planning) |
| **Search errors** | Error rate % | > 5% error rate |
| **Search latency** | p50, p95, p99 | p95 > 5s |
| **Citation accuracy** | % answers with valid citations | < 95% citation validity |
| **LLM latency** | Time to first token | > 2s |
| **Qdrant latency** | Vector search time | > 1.5s |
| **Cache hit rate** | Redis cache hits % | < 60% hit rate |

**Logging:**

```python
logger = get_logger()
logger.info(
    "search_completed",
    query_length=len(query),
    kb_count=len(kb_ids),
    result_count=len(results),
    citation_count=len(citations),
    confidence=confidence,
    latency_ms=latency,
    cached=cache_hit
)
```

**Metrics:**
- Prometheus metrics exposed at /metrics
- Grafana dashboard for search pipeline visualization

## Dependencies and Integrations

### External Dependencies

| Dependency | Version | Purpose | Risk Mitigation |
|------------|---------|---------|-----------------|
| **langchain-qdrant** | ≥1.1.0 | Vector search client | Use QdrantVectorStore (not deprecated Qdrant class) |
| **qdrant-client** | ≥1.10.0 | Low-level Qdrant ops | gRPC mode for performance |
| **litellm** | ≥1.50.0 | LLM & embedding access | Fallback providers configured |
| **redis** | ≥7.1.0 | Query caching | Graceful degradation if down |

**Backend pyproject.toml additions:**

```toml
[project.dependencies]
# Already in Epic 2
langchain-qdrant = "^1.1.0"
qdrant-client = "^1.10.0"
litellm = "^1.50.0"
redis = "^7.1.0"

# No new dependencies for Epic 3
```

**Frontend package.json additions:**

```json
{
  "dependencies": {
    "cmdk": "^1.0.0"  // For Command Palette component (shadcn/ui dependency)
  }
}
```

### Internal Dependencies

| From Epic | Dependency | Epic 3 Usage |
|-----------|------------|--------------|
| **Epic 1** | Authentication | Current user for permission checks |
| **Epic 1** | AuditService | Log search queries to audit.events |
| **Epic 2** | KBPermission | Check user has READ access to KBs |
| **Epic 2** | Qdrant collections | Search against kb_{id} collections created in Epic 2 |
| **Epic 2** | Document metadata | Citations reference documents table |

**Critical Path:** Epic 3 **requires** Epic 2 completion (documents must be indexed with rich metadata).

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                          │
│  - SearchBar component                                       │
│  - CommandPalette (⌘K)                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS REST + SSE
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  SearchService                                         │  │
│  │    ├─→ CitationService                                │  │
│  │    ├─→ PermissionService (Epic 2)                     │  │
│  │    └─→ AuditService (Epic 1)                          │  │
│  └───────────────────────────────────────────────────────┘  │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       │          │          │          │
       ↓          ↓          ↓          ↓
  ┌─────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
  │ Qdrant  │ │LiteLLM │ │  Redis  │ │PostgreSQL│
  │ (vector)│ │ (LLM)  │ │ (cache) │ │ (audit)  │
  └─────────┘ └────────┘ └─────────┘ └──────────┘
```

## Acceptance Criteria (Authoritative)

### Story 3.1: Semantic Search Backend

**Given** a user with READ access to a KB with indexed documents
**When** they POST /api/v1/search with query "authentication approach"
**Then** the system:
- Generates query embedding via LiteLLM
- Searches Qdrant collection kb_{id}
- Returns top-10 chunks with relevance scores
- Response includes document_id, document_name, chunk_text, page_number, section_header
- Search is logged to audit.events with user_id, query, kb_ids, result_count

**And** response time is < 3 seconds (p95)

### Story 3.2: Answer Synthesis with Citations

**Given** search returns relevant chunks
**When** answer synthesis is requested
**Then** the system:
- Passes chunks to LLM with citation instructions
- LLM generates answer with [1], [2] markers
- CitationService extracts markers and maps to source chunks
- Response includes:
  - answer_text with inline [n] markers
  - citations array with full metadata (doc_name, page, section, excerpt, char_start, char_end)
  - confidence_score (0-1)

**And** every [n] marker has a corresponding citation in the array
**And** confidence calculation considers retrieval relevance + source count

### Story 3.3: Search API Streaming Response

**Given** search endpoint called with stream=true
**When** processing begins
**Then** SSE connection opens and events stream:
- `{"type": "status", "content": "Searching..."}`
- `{"type": "token", "content": "word"}` (answer tokens)
- `{"type": "citation", "data": {...}}` (when [n] detected)
- `{"type": "done", "confidence": 0.85}`

**And** citations appear immediately when marker is parsed
**And** client can cancel stream
**And** errors are sent as error event + connection closes gracefully

### Story 3.4: Search Results UI with Inline Citations

**Given** search streaming completes
**When** answer is displayed
**Then** the UI shows:
- Answer text in center panel with word-by-word appearance
- Citation markers [1], [2] as blue clickable badges inline
- Right panel with CitationCard for each citation (number, doc name, page, excerpt, preview/open buttons)
- Confidence indicator bar (green 80-100%, amber 50-79%, red 0-49%)

**And** confidence is ALWAYS shown (never hidden)
**And** layout does not shift when citations populate

### Story 3.5: Citation Preview and Source Navigation

**Given** an answer with citations is displayed
**When** user hovers over citation marker [1]
**Then** tooltip shows doc title + excerpt snippet

**When** user clicks citation marker [1]
**Then** CitationPanel scrolls to CitationCard #1 and highlights it

**When** user clicks "Preview" on CitationCard
**Then** preview modal opens showing:
- Document name, page, section
- Cited passage highlighted
- Surrounding context (±200 chars)

**When** user clicks "Open Document"
**Then** document viewer opens at cited passage (scrolled and highlighted)

### Story 3.6: Cross-KB Search

**Given** user has READ access to 3 KBs
**When** they search without specifying kb_ids (default)
**Then** search runs against ALL 3 KBs in parallel
**And** results are merged and ranked by relevance
**And** each result shows KB name tag

**When** user applies "Search within current KB" filter
**Then** only that KB's results are shown

**And** cross-KB search is the default behavior (kb_ids = null)

### Story 3.7: Quick Search and Command Palette

**Given** user is anywhere in the app
**When** they press Cmd/Ctrl+K
**Then** command palette overlay appears with focus in search input

**When** user types query and presses Enter
**Then** quick search results (top 5) appear in palette
**And** arrow keys navigate results
**And** Enter selects result → opens full search view

**When** user presses Escape
**Then** palette closes, focus returns to previous element

### Story 3.8: Search Result Actions

**Given** search results are displayed
**When** user views a result card
**Then** action buttons are shown:
- "Use in Draft" (marks for generation in Epic 4)
- "View" (opens document)
- "Similar" (finds similar content)

**When** user clicks "Similar"
**Then** new search runs using that chunk's embedding
**And** query shows "Similar to: [doc title]"

### Story 3.9: Relevance Explanation

**Given** search results are displayed
**When** user views a result card
**Then** "Relevant because:" section explains:
- Matching keywords highlighted
- Semantic similarity factors
- Source document context

**When** user expands explanation
**Then** detailed view shows:
- Semantic distance score
- Related documents

### Story 3.10: Verify All Citations

**Given** an answer has 5 citations
**When** user clicks "Verify All" button
**Then** verification mode activates:
- Citation [1] highlighted in answer + panel
- Preview shows citation 1 source automatically

**When** user clicks checkmark or "Next"
**Then** citation 1 marked verified (green badge)
**And** citation [2] becomes active

**When** all citations verified
**Then** "All sources verified ✓" message appears
**And** answer shows "Sources verified" badge

### Story 3.11: Search Audit Logging

**Given** any search is performed
**When** results return
**Then** audit event is logged with:
- user_id
- action='search'
- query text
- kb_ids searched
- result_count
- response_time_ms
- timestamp (UTC)

**And** audit write is async (doesn't block search response)
**And** admins can filter audit logs by action='search'

## Traceability Mapping

| AC | Spec Section | Component/API | Test ID | Test Type |
|----|--------------|---------------|---------|-----------|
| 3.1 - Search backend | SearchService | SearchService._search_collections() | T3.1.1 | Integration |
| 3.1 - Embedding | SearchService | SearchService._embed_query() | T3.1.2 | Unit |
| 3.1 - Audit log | AuditService | AuditService.log_search() | T3.1.3 | Integration |
| 3.2 - Answer synthesis | SearchService | SearchService._synthesize_answer() | T3.2.1 | Integration |
| 3.2 - Citation extraction | CitationService | CitationService.extract_citations() | T3.2.2 | Unit |
| 3.2 - Confidence calc | SearchService | SearchService._calculate_confidence() | T3.2.3 | Unit |
| 3.3 - SSE streaming | API endpoint | POST /api/v1/search?stream=true | T3.3.1 | Integration |
| 3.3 - Citation event | API endpoint | SSE citation event format | T3.3.2 | Integration |
| 3.4 - Citation UI | CitationMarker | frontend/components/citations/ | T3.4.1 | Component |
| 3.4 - Confidence UI | ConfidenceIndicator | frontend/components/search/ | T3.4.2 | Component |
| 3.5 - Citation preview | CitationCard | frontend/components/citations/ | T3.5.1 | Component |
| 3.5 - Source nav | Document viewer | /documents/{id}?highlight= | T3.5.2 | E2E |
| 3.6 - Cross-KB search | SearchService | SearchService.search() with kb_ids=None | T3.6.1 | Integration |
| 3.6 - KB filtering | SearchBar | Frontend filter state | T3.6.2 | Component |
| 3.7 - Command palette | CommandPalette | frontend/components/search/ | T3.7.1 | Component |
| 3.7 - Keyboard shortcut | CommandPalette | ⌘K trigger | T3.7.2 | E2E |
| 3.8 - Result actions | SearchResultCard | Action button handlers | T3.8.1 | Component |
| 3.8 - Find similar | SearchService | Similar search via chunk embedding | T3.8.2 | Integration |
| 3.9 - Relevance explain | SearchResultCard | Explanation generation | T3.9.1 | Component |
| 3.10 - Verify All mode | VerifyAllMode | Verification state machine | T3.10.1 | Component |
| 3.11 - Audit logging | AuditService | audit.events inserts | T3.11.1 | Integration |

**FR Traceability:**

| FR | Spec Section | Story | Test Coverage |
|----|--------------|-------|---------------|
| FR24 | SearchService | 3.1 | T3.1.1, T3.1.2 |
| FR24a-d | CommandPalette | 3.7 | T3.7.1, T3.7.2 |
| FR25 | SearchService._search_collections() | 3.1 | T3.1.1 |
| FR26 | SearchService._synthesize_answer() | 3.2 | T3.2.1 |
| FR27, FR27a | CitationService | 3.2, 3.4 | T3.2.2, T3.4.1 |
| FR28, FR28a-b | Citation UI | 3.5 | T3.5.1, T3.5.2 |
| FR29, FR29a | Cross-KB search | 3.6 | T3.6.1 |
| FR30, FR30a-f | Search UI | 3.4, 3.8, 3.9, 3.10 | T3.4.2, T3.8.1, T3.9.1, T3.10.1 |
| FR43-46 | CitationService | 3.2 | T3.2.2 |
| FR54 | AuditService.log_search() | 3.11 | T3.11.1 |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM citation quality** - LLM doesn't consistently use [n] markers | Medium | High | (1) Strong system prompt (2) Few-shot examples (3) Validation in CitationService (4) Manual QA |
| **Performance degradation** - Cross-KB search too slow with 10+ KBs | Medium | High | (1) Parallel queries (2) Limit to top-3 KBs by recent usage (3) Caching |
| **Citation mapping errors** - Marker [n] maps to wrong chunk | Low | Critical | (1) Comprehensive unit tests (2) Validation that marker ≤ chunk_count (3) Logging |
| **Qdrant availability** - Vector DB downtime breaks search | Low | High | (1) Graceful degradation (2) Cached results (3) Health checks |
| **LLM hallucination** - Answer includes info NOT in sources | Medium | Critical | (1) Citation validation (2) Confidence scoring (3) User verification flow |

### Assumptions

| Assumption | Validation | Fallback |
|------------|------------|----------|
| **Qdrant metadata richness** - Epic 2 indexed chunks with page, section, char_start/end | Verify in integration tests | If missing, citations show doc-level only (less precise) |
| **LLM instruction following** - GPT-4 reliably follows citation format | Test with 100+ queries | Switch to more structured output (JSON mode) |
| **User behavior** - Users will verify citations before trusting | Onboarding wizard enforces | Warn on export "Have you verified sources?" |
| **Network reliability** - SSE streams don't drop frequently | Tested in staging | Implement reconnect logic |

### Open Questions

| Question | Owner | Resolution Date | Answer |
|----------|-------|-----------------|--------|
| Should we support citation editing (user corrects [n])? | Product | Before 3.2 implementation | No - trust LLM, log errors for improvement |
| Cache strategy for cross-KB search? | Tech Lead | Before 3.6 | Redis cache per KB, merge cached results |
| Should Quick Search synthesize answer or just return chunks? | UX | Before 3.7 | Chunks only (faster, command palette use case) |
| Confidence threshold for warning users? | Product | Before 3.4 | <50% = red warning, 50-79% = amber caution |
| Do we need A/B testing for citation prompts? | Product | Epic 4 | Defer - manual QA sufficient for MVP |

## Test Strategy Summary

### Test Levels

| Level | Scope | Tools | Coverage Target |
|-------|-------|-------|-----------------|
| **Unit** | Service methods, citation extraction, confidence calc | pytest, fixtures | 80% |
| **Integration** | API endpoints with Qdrant, LiteLLM, Redis | pytest, testcontainers | Key paths |
| **Component** | React components (CitationMarker, SearchResultCard) | Vitest, React Testing Library | All components |
| **E2E** | Full search flow: query → results → verify citations | Playwright | Critical path |

### Key Test Scenarios

**Unit Tests (pytest):**

```python
# test_citation_service.py
async def test_extract_citations_with_valid_markers():
    """CitationService correctly extracts [1], [2] from answer."""
    chunks = [mock_chunk_1, mock_chunk_2]
    answer = "OAuth 2.0 [1] with MFA [2]."

    text, citations = service.extract_citations(answer, chunks)

    assert len(citations) == 2
    assert citations[0].number == 1
    assert citations[0].document_name == mock_chunk_1.document_name

async def test_extract_citations_orphaned_marker():
    """Raises error if [3] exists but only 2 chunks provided."""
    chunks = [mock_chunk_1, mock_chunk_2]
    answer = "OAuth [1] and biometric [3]."  # [3] invalid

    with pytest.raises(CitationMappingError):
        service.extract_citations(answer, chunks)
```

**Integration Tests (pytest + testcontainers):**

```python
# test_search_integration.py
async def test_semantic_search_returns_relevant_results(client, test_db):
    """Search endpoint returns results from Qdrant."""
    # Setup: Index test document in Qdrant
    # Execute: POST /api/v1/search
    response = await client.post("/api/v1/search", json={
        "query": "authentication approach",
        "kb_ids": [kb_id]
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    assert data["confidence"] > 0

async def test_cross_kb_search_merges_results(client, test_db):
    """Cross-KB search queries multiple collections."""
    # Setup: Create 2 KBs with indexed docs
    response = await client.post("/api/v1/search", json={
        "query": "security",
        "kb_ids": None  # Search all
    })

    results = response.json()["results"]
    kb_ids = {r["kb_id"] for r in results}
    assert len(kb_ids) == 2  # Results from both KBs
```

**Component Tests (Vitest):**

```typescript
// citation-marker.test.tsx
describe('CitationMarker', () => {
  it('renders citation number', () => {
    render(<CitationMarker number={1} onClick={mockFn} />);
    expect(screen.getByText('[1]')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<CitationMarker number={1} onClick={onClick} />);
    fireEvent.click(screen.getByText('[1]'));
    expect(onClick).toHaveBeenCalledWith(1);
  });
});
```

**E2E Tests (Playwright):**

```typescript
// e2e/search/search-with-citations.spec.ts
test('user can search and verify citations', async ({ page }) => {
  await page.goto('/dashboard');

  // Enter search query
  await page.fill('[data-testid="search-bar"]', 'authentication approach');
  await page.press('[data-testid="search-bar"]', 'Enter');

  // Wait for results
  await page.waitForSelector('[data-testid="search-answer"]');

  // Verify citation markers exist
  const markers = page.locator('[data-testid^="citation-marker-"]');
  await expect(markers).toHaveCount(2); // Expecting [1], [2]

  // Click first citation
  await markers.first().click();

  // Verify citation panel highlights
  const card = page.locator('[data-testid="citation-card-1"]');
  await expect(card).toHaveClass(/highlighted/);

  // Click preview
  await card.locator('button:has-text("Preview")').click();

  // Verify preview modal
  await expect(page.locator('[data-testid="citation-preview-modal"]')).toBeVisible();
});
```

### Testing Priorities

**P0 (Must Pass):**
- Citation extraction accuracy (100%)
- Cross-KB search permission enforcement
- Audit logging for all searches
- SSE streaming stability

**P1 (Important):**
- Search performance < 3s
- Confidence calculation correctness
- Citation preview functionality

**P2 (Nice to Have):**
- Command palette keyboard navigation
- Relevance explanation quality
- Similar search accuracy

### Test Data Strategy

**Fixtures:**
```python
# conftest.py
@pytest.fixture
def mock_search_chunks():
    """Sample search chunks with rich metadata."""
    return [
        SearchChunk(
            document_id="doc-1",
            document_name="Acme Proposal.pdf",
            page_number=14,
            section_header="Authentication",
            chunk_text="OAuth 2.0 with PKCE...",
            char_start=3450,
            char_end=3892,
            score=0.92
        ),
        # ... more chunks
    ]
```

**Factories:**
```python
# factories/search_factory.py
class SearchChunkFactory:
    """Factory for generating test search chunks."""

    @staticmethod
    def create(overrides=None):
        defaults = {
            "document_id": f"doc-{uuid.uuid4()}",
            "document_name": "Test Document.pdf",
            "chunk_text": "Sample content for testing.",
            "score": 0.85,
        }
        return SearchChunk(**(defaults | (overrides or {})))
```

### Continuous Testing

**Pre-commit:**
- Linting (ruff, eslint)
- Unit tests (fast subset)
- Type checking

**CI Pipeline:**
1. Lint backend + frontend
2. Unit tests (parallel)
3. Integration tests (with testcontainers)
4. Component tests
5. Coverage report (threshold: 70%)
6. E2E tests (manual dispatch after Epic 5 Docker setup)

**Regression Suite:**
- Run full test suite on main branch push
- Nightly E2E tests against staging

---

**Test Coverage Summary:**
- **Unit tests**: 80%+ coverage for SearchService, CitationService
- **Integration tests**: All API endpoints, Qdrant queries, audit logging
- **Component tests**: All new UI components (CitationMarker, ConfidenceIndicator, etc.)
- **E2E tests**: Critical path (search → results → verify → navigate to source)

**Deferred to Epic 5:**
- Full E2E automation in CI (requires Docker Compose)
- Load testing with 50+ concurrent users
- Chaos engineering (Qdrant failures, network issues)
