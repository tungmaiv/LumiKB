# Epic 4: Chat & Document Generation

**Goal:** Enable users to have multi-turn conversations and generate document drafts with citations that can be exported.

**User Value:** "I can chat with my knowledge, generate drafts for RFP responses, and export them with citations - the 80% draft in 30 seconds magic moment."

**FRs Covered:** FR31-35, FR35a-b, FR36-42, FR42a-e, FR55

**Technical Foundation:**
- Conversation context management
- LLM streaming with citation tracking
- Document export (DOCX, PDF, MD)
- Generation templates

---

## Story 4.1: Chat Conversation Backend

As a **user**,
I want **to have multi-turn conversations with my Knowledge Base**,
So that **I can explore topics in depth**.

**Acceptance Criteria:**

**Given** I have an active KB
**When** I call POST /api/v1/chat with a message
**Then** the system performs RAG (retrieval + generation)
**And** response includes answer with citations
**And** conversation context is stored in Redis

**Given** I send a follow-up message
**When** the chat endpoint processes it
**Then** previous messages are included as context
**And** the response is contextually aware

**And** conversation context includes:
- Previous messages (up to token limit)
- Retrieved chunks from each turn
- Generated responses

**Prerequisites:** Story 3.2

**Technical Notes:**
- Store conversation in Redis with session key
- Token limit: ~4000 for context, reserve rest for response
- Reference: FR31, FR32

---

## Story 4.2: Chat Streaming UI

As a **user**,
I want **to see chat responses stream in real-time**,
So that **the conversation feels natural and responsive**.

**Acceptance Criteria:**

**Given** I am in the chat interface
**When** I send a message
**Then** my message appears immediately on the right
**And** a "thinking" indicator appears for the AI

**Given** the AI is responding
**When** tokens stream in
**Then** they appear word-by-word in the chat bubble
**And** citation markers appear inline as they're generated
**And** citations populate in the right panel in real-time

**And** user messages have:
- Primary color background
- Right alignment
- Timestamp

**And** AI messages have:
- Surface color background
- Left alignment
- Inline citations
- Confidence indicator

**Prerequisites:** Story 4.1, Story 3.4

**Technical Notes:**
- Use ChatMessage component from UX spec
- SSE for streaming
- Reference: FR35, FR35a, FR35b

---

## Story 4.3: Conversation Management

As a **user**,
I want **to manage my conversation threads**,
So that **I can start fresh or continue previous work**.

**Acceptance Criteria:**

**Given** I am in the chat interface
**When** I click "New Chat"
**Then** a new conversation starts
**And** previous context is cleared

**Given** I have an active conversation
**When** I view the conversation history
**Then** I see all messages from the current session
**And** I can scroll through previous exchanges

**Given** I want to clear history
**When** I click "Clear Chat"
**Then** a confirmation appears
**And** confirming clears all messages
**And** undo is available for 30 seconds

**Prerequisites:** Story 4.2

**Technical Notes:**
- Conversations are session-scoped (not persisted to DB for MVP)
- Reference: FR33, FR34

---

## Story 4.4: Document Generation Request

As a **user**,
I want **to request AI-generated document drafts**,
So that **I can quickly create RFP responses and other artifacts**.

**Acceptance Criteria:**

**Given** I have search results or chat context
**When** I click "Generate Draft"
**Then** a generation modal appears with options:
- Document type dropdown (RFP Response, Checklist, Gap Analysis, Custom)
- Context/instructions textarea
- Source selection (use current results or specify)

**Given** I select document type and add context
**When** I click "Generate"
**Then** generation begins with progress indicator
**And** progress shows which sources are being used
**And** draft streams in with inline citations

**And** the request is logged to audit.events (FR55)

**Prerequisites:** Story 4.1, Story 3.8

**Technical Notes:**
- Document type determines prompt template
- Use selected results from Story 3.8 if available
- Reference: FR36, FR37, FR41, FR55

---

## Story 4.5: Draft Generation Streaming

As a **user**,
I want **to see my draft generate in real-time**,
So that **I can see progress and the draft feels responsive**.

**Acceptance Criteria:**

**Given** generation is in progress
**When** content streams
**Then** the draft appears in an editor panel
**And** citation markers [1], [2] appear inline
**And** a progress bar shows estimated completion

**Given** a section has low confidence
**When** it's generated
**Then** it's highlighted with amber background
**And** a note appears: "Review suggested - lower confidence"

**Given** generation completes
**When** the final token arrives
**Then** "Done" event fires
**And** summary appears: "Draft ready! Based on 5 sources from 3 documents"
**And** all citations are populated in the panel

**Prerequisites:** Story 4.4

**Technical Notes:**
- Use DraftSection component from UX spec
- Confidence calculated per section based on source coverage
- Reference: FR42a, FR42b, FR42e

---

## Story 4.6: Draft Editing

As a **user**,
I want **to edit the generated draft before exporting**,
So that **I can refine and customize the content**.

**Acceptance Criteria:**

**Given** a draft is generated
**When** I click in the draft area
**Then** I can edit the text directly
**And** citation markers remain intact unless deleted

**Given** I'm editing
**When** I delete a citation marker
**Then** it's removed from the text
**And** the citation panel updates accordingly

**Given** I want to regenerate a section
**When** I select text and click "Regenerate"
**Then** that section is regenerated
**And** the rest of the draft is preserved

**Prerequisites:** Story 4.5

**Technical Notes:**
- Use contenteditable or lightweight editor
- Track citation markers as special spans
- Reference: FR39, FR42

---

## Story 4.7: Document Export

As a **user**,
I want **to export my draft in common formats**,
So that **I can use it in my workflow**.

**Acceptance Criteria:**

**Given** a draft exists
**When** I click "Export"
**Then** I see format options: DOCX, PDF, Markdown

**Given** I select DOCX
**When** export completes
**Then** the document downloads
**And** citations appear as footnotes or inline references
**And** formatting is preserved (headers, lists, etc.)

**Given** I select PDF
**When** export completes
**Then** the PDF downloads with proper formatting
**And** citations are rendered appropriately

**Given** I select Markdown
**When** export completes
**Then** the .md file downloads
**And** citations are formatted as [^1] footnotes

**And** before any export, a prompt appears: "Have you verified the sources?" (FR40b)

**Prerequisites:** Story 4.6

**Technical Notes:**
- Use python-docx for DOCX
- Use weasyprint or reportlab for PDF
- Reference: FR40, FR40a, FR40b

---

## Story 4.8: Generation Feedback and Recovery

As a **user**,
I want **to provide feedback when generation doesn't meet my needs**,
So that **I can get better results**.

**Acceptance Criteria:**

**Given** a draft is generated
**When** I'm not satisfied
**Then** I can click "This doesn't look right"
**And** a feedback modal appears

**Given** I provide feedback
**When** I submit
**Then** alternative approaches are offered:
- "Try different sources" (searches again)
- "Use template" (starts from structured template)
- "Regenerate with feedback" (includes my feedback as instruction)

**Given** generation fails
**When** error is detected
**Then** user sees friendly error message
**And** recovery options are presented
**And** they can try again or fall back to template

**Prerequisites:** Story 4.5

**Technical Notes:**
- Log feedback for future improvements
- Reference: FR42c, FR42d

---

## Story 4.9: Generation Templates

As a **user**,
I want **pre-built templates for common document types**,
So that **I can generate consistent, well-structured drafts**.

**Acceptance Criteria:**

**Given** I select a document type
**When** generation starts
**Then** the appropriate template structures the output:

**RFP Response:**
- Executive Summary
- Technical Approach
- Relevant Experience
- Pricing (placeholder)

**Checklist:**
- Numbered requirements
- Status column
- Notes column

**Gap Analysis:**
- Requirement
- Current State
- Gap Identified
- Recommendation

**And** each template section includes citations from relevant sources

**Prerequisites:** Story 4.4

**Technical Notes:**
- Templates as prompt engineering
- Reference: FR37

---

## Story 4.10: Generation Audit Logging

As a **compliance officer**,
I want **all generation requests logged with full context**,
So that **we can audit AI-assisted content creation**.

**Acceptance Criteria:**

**Given** a generation request is made
**When** generation completes (or fails)
**Then** an audit event is logged with:
- user_id
- document_type
- prompt/instructions provided
- source_documents used (list of doc IDs)
- citation_count
- generation_time_ms
- success/failure status

**And** the full generated content is NOT stored in audit (privacy)
**And** source document references ARE stored (provenance)

**Prerequisites:** Story 4.4, Story 1.7

**Technical Notes:**
- Log sources, not content
- Reference: FR55, FR46

---

## Summary

Epic 4 establishes the chat and document generation system for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 4.1 | - | Chat conversation backend |
| 4.2 | - | Chat streaming UI |
| 4.3 | - | Conversation management |
| 4.4 | - | Document generation request |
| 4.5 | - | Draft generation streaming |
| 4.6 | - | Draft editing |
| 4.7 | - | Document export |
| 4.8 | - | Generation feedback and recovery |
| 4.9 | - | Generation templates |
| 4.10 | - | Generation audit logging |

**Total Stories:** 10

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
