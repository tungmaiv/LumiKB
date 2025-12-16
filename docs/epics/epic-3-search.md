# Epic 3: Semantic Search & Citations

**Goal:** Enable users to search their Knowledge Bases with natural language and receive answers with inline citations linking to source documents.

**User Value:** "I can ask questions and get answers with citations I can trust - this is THE magic moment."

**FRs Covered:** FR24-30, FR24a-d, FR27a, FR28a-b, FR29a, FR30a-f, FR43-46, FR54

**Technical Foundation:**
- Qdrant semantic search
- LiteLLM for answer synthesis
- CitationService for source tracking
- SSE for streaming responses

---

## Story 3.1: Semantic Search Backend

As a **user**,
I want **to search my Knowledge Base with natural language**,
So that **I can find relevant information quickly**.

**Acceptance Criteria:**

**Given** I have access to a KB with documents
**When** I call POST /api/v1/search with a query and kb_id
**Then** the query is embedded using the same model as documents
**And** semantic search is performed against Qdrant
**And** top-k results (default: 10) are returned

**And** each result includes:
- document_id, document_name
- chunk_text (the relevant passage)
- page_number, section_header (if available)
- relevance_score (0-1)

**And** the search is logged to audit.events (FR54)

**Given** no relevant results exist
**When** search completes
**Then** empty results array is returned with helpful message

**Prerequisites:** Story 2.6

**Technical Notes:**
- Use langchain-qdrant QdrantVectorStore
- Relevance score from Qdrant distance metric
- Reference: FR24, FR25, FR54

---

## Story 3.2: Answer Synthesis with Citations Backend

As a **user**,
I want **search results synthesized into a coherent answer with citations**,
So that **I get direct answers rather than just document links**.

**Acceptance Criteria:**

**Given** search returns relevant chunks
**When** answer synthesis is requested
**Then** chunks are passed to LLM with citation instructions
**And** LLM generates an answer using [1], [2], etc. markers
**And** CitationService extracts markers and maps to source chunks

**And** the response includes:
- answer_text (with inline citation markers)
- citations array with full metadata per marker
- confidence_score (based on retrieval relevance)

**Given** the LLM response contains [1]
**When** citation extraction runs
**Then** citation 1 maps to the first source chunk used
**And** includes: document_name, page, section, excerpt, char_start, char_end

**And** confidence indicators are calculated based on:
- Retrieval relevance scores
- Number of supporting sources
- Query-answer semantic similarity

**Prerequisites:** Story 3.1

**Technical Notes:**
- System prompt instructs LLM to cite every claim
- CitationService is THE core differentiator - test thoroughly
- Reference: FR26, FR27, FR43, FR44, FR30c

---

## Story 3.3: Search API Streaming Response

As a **user**,
I want **search results to stream in real-time**,
So that **I see answers faster and feel the system is responsive**.

**Acceptance Criteria:**

**Given** I call the search endpoint with stream=true
**When** processing begins
**Then** SSE connection is established
**And** events stream as they're generated:
- `{"type": "status", "content": "Searching..."}`
- `{"type": "token", "content": "OAuth"}` (answer tokens)
- `{"type": "citation", "data": {...}}` (when citation marker parsed)
- `{"type": "done", "confidence": 0.85}`

**Given** streaming is in progress
**When** a citation marker [n] is detected
**Then** a citation event is immediately sent with full metadata
**And** the frontend can display the citation inline

**Given** an error occurs during streaming
**When** the error is caught
**Then** an error event is sent
**And** the connection is closed gracefully

**Prerequisites:** Story 3.2

**Technical Notes:**
- Use FastAPI StreamingResponse with SSE
- Parse tokens as they stream to detect [n] patterns
- Reference: FR35a (applies to search too)

---

## Story 3.4: Search Results UI with Inline Citations

As a **user**,
I want **to see search results with visible inline citations**,
So that **I can trust and verify the answers**.

**Acceptance Criteria:**

**Given** I submit a search query
**When** results stream in
**Then** the answer appears word-by-word in the center panel
**And** citation markers [1], [2] appear inline as blue clickable badges

**Given** an answer is displayed
**When** I view the citations panel (right side)
**Then** I see a card for each citation with:
- Citation number
- Document name
- Page/section reference
- Excerpt preview (truncated)
- "Preview" and "Open" buttons

**And** the confidence indicator shows:
- Green bar (80-100%): High confidence
- Amber bar (50-79%): Medium confidence
- Red bar (0-49%): Low confidence

**And** confidence is ALWAYS shown (FR30c)

**Prerequisites:** Story 3.3, Story 1.9

**Technical Notes:**
- Use CitationMarker and CitationCard components from UX spec
- Use ConfidenceIndicator component
- Reference: FR27a, FR30, FR30c

---

## Story 3.5: Citation Preview and Source Navigation

As a **user**,
I want **to preview and navigate to cited sources**,
So that **I can verify the information without losing context**.

**Acceptance Criteria:**

**Given** an answer has citations displayed
**When** I hover over a citation marker [1]
**Then** a tooltip shows the source title and excerpt snippet

**Given** I click a citation marker
**When** the citation panel scrolls
**Then** the corresponding CitationCard is highlighted

**Given** I click "Preview" on a CitationCard
**When** the preview opens
**Then** I see the cited passage with the relevant text highlighted
**And** I can scroll to see surrounding context

**Given** I click "Open Document"
**When** the document viewer opens
**Then** the full document is shown
**And** it scrolls to and highlights the cited passage (FR28b)

**Prerequisites:** Story 3.4

**Technical Notes:**
- Preview in modal/sheet, document in new tab or full panel
- Use char_start/char_end from citation metadata for highlighting
- Reference: FR28, FR28a, FR28b, FR45

---

## Story 3.6: Cross-KB Search

As a **user**,
I want **to search across all my Knowledge Bases at once**,
So that **I can find information regardless of where it's stored**.

**Acceptance Criteria:**

**Given** I have access to multiple KBs
**When** I search without specifying a KB (default)
**Then** search runs against ALL my permitted KBs
**And** results are merged and ranked by relevance

**And** each result shows which KB it came from
**And** I can filter results by KB after viewing

**Given** I want to search a specific KB
**When** I use the "Search within current KB" filter
**Then** only that KB is searched

**And** cross-KB search is the DEFAULT (FR29a)

**Prerequisites:** Story 3.1, Story 2.2

**Technical Notes:**
- Query multiple Qdrant collections in parallel
- Permission check per collection
- Merge and re-rank results by score
- Reference: FR29, FR29a, FR30e

---

## Story 3.7: Quick Search and Command Palette

As a **user**,
I want **to quickly search via keyboard shortcut**,
So that **I can find information without leaving my current context**.

**Acceptance Criteria:**

**Given** I am anywhere in the application
**When** I press Cmd/Ctrl+K
**Then** a command palette overlay appears
**And** focus is in the search input

**Given** the command palette is open
**When** I type a query and press Enter
**Then** quick search results appear in the palette
**And** I can select a result with arrow keys

**Given** I select a result
**When** I press Enter
**Then** the full search view opens with that result highlighted

**Given** I press Escape
**When** the palette is open
**Then** it closes and focus returns to previous element

**Prerequisites:** Story 3.4

**Technical Notes:**
- Use shadcn/ui Command component (Radix Dialog + cmdk)
- Quick search uses same backend, limited to top 5 results
- Reference: FR24a, FR24b, FR24c

---

## Story 3.8: Search Result Actions

As a **user**,
I want **quick actions on search results**,
So that **I can efficiently work with found information**.

**Acceptance Criteria:**

**Given** a search result is displayed
**When** I view the result card
**Then** I see action buttons:
- "Use in Draft" (prepares for generation)
- "View" (opens document)
- "Similar" (finds similar content)

**Given** I click "Use in Draft"
**When** the action completes
**Then** the result is marked for use in document generation
**And** a badge appears showing "Selected for draft"

**Given** I click "Similar"
**When** the search runs
**Then** results similar to that chunk are displayed
**And** the original query is replaced with "Similar to: [title]"

**Prerequisites:** Story 3.4

**Technical Notes:**
- "Similar" uses the chunk embedding for similarity search
- "Use in Draft" stores selection in session state
- Reference: FR30b

---

## Story 3.9: Relevance Explanation

As a **user**,
I want **to understand WHY a result is relevant**,
So that **I can trust the search quality**.

**Acceptance Criteria:**

**Given** search results are displayed
**When** I view a result card
**Then** I see a "Relevant because:" section explaining:
- Key matching terms/concepts
- Semantic similarity factors
- Source document context

**Given** I want more detail
**When** I expand the explanation
**Then** I see:
- Matching keywords highlighted
- Semantic distance score
- Other documents this relates to

**Prerequisites:** Story 3.4

**Technical Notes:**
- Generate explanation via LLM based on query + chunk
- Cache explanations to avoid repeated LLM calls
- Reference: FR30a

---

## Story 3.10: Verify All Citations

As a **skeptical user**,
I want **to verify all citations in sequence**,
So that **I can systematically check the AI's sources**.

**Acceptance Criteria:**

**Given** an answer has multiple citations
**When** I click "Verify All" button
**Then** verification mode activates
**And** the first citation is highlighted in both answer and panel

**Given** verification mode is active
**When** I click "Next" or press arrow key
**Then** the next citation is highlighted
**And** the preview automatically shows that citation's source

**Given** I verify a citation
**When** I click the checkmark
**Then** a green "Verified" badge appears on that citation
**And** verification progress shows (e.g., "3/7 verified")

**Given** I've verified all citations
**When** I complete the sequence
**Then** "All sources verified" message appears
**And** a summary badge shows on the answer

**Prerequisites:** Story 3.5

**Technical Notes:**
- Track verification state in component state
- Persist verified state for session duration
- Reference: FR30d

---

## Summary

Epic 3 establishes the semantic search and citation system for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 3.1 | - | Semantic search backend |
| 3.2 | - | Answer synthesis with citations |
| 3.3 | - | Search API streaming response |
| 3.4 | - | Search results UI with inline citations |
| 3.5 | - | Citation preview and source navigation |
| 3.6 | - | Cross-KB search |
| 3.7 | - | Quick search and command palette |
| 3.8 | - | Search result actions |
| 3.9 | - | Relevance explanation |
| 3.10 | - | Verify all citations |

**Total Stories:** 10 (Story 3.11 - Search Audit Logging moved to Epic 5 as Story 5.14)

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
