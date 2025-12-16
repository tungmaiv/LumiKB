# Correct Course: KB-Level Configuration Feature

**Date:** 2025-12-09
**Initiated By:** Tung Vu (Product Owner)
**Prepared By:** Multi-Agent Team Discussion
**Epic:** 7 (Infrastructure & DevOps)
**Status:** Ready for SM Review

---

## Executive Summary

This document captures the correct-course decision to add **KB-Level Configuration** capabilities to LumiKB. Each Knowledge Base will have a dedicated configuration layer that overrides system defaults for embedding, generation, NER, chunking, retrieval, reranking, and custom prompts.

### Decision: Add to Epic 7 (Infrastructure & DevOps)

**Rationale:**
- Thematic fit: Epic 7's goal is "centralized configuration, model management"
- Foundation exists: Stories 7.9 (LLM Model Registry) and 7.10 (KB Model Configuration) are already DONE
- Existing `settings` JSONB column in `knowledge_bases` table ready for use
- No new epic overhead (tech spec, context files already exist)

---

## Feature Overview

### Three-Layer Configuration Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION RESOLUTION                      │
│                                                                  │
│  Request Parameters (highest priority)                          │
│         ↓ if null                                                │
│  KB-Level Settings (KnowledgeBase.settings JSONB)               │
│         ↓ if null                                                │
│  System Defaults (ConfigService / LLM Model defaults)           │
│                                                                  │
│  Resolution: First non-null value wins                          │
└─────────────────────────────────────────────────────────────────┘
```

### KB Settings Schema Structure

```python
class KBSettings(BaseModel):
    """Complete KB-level configuration stored in settings JSONB."""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reranking: RerankingConfig = Field(default_factory=RerankingConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    ner: NERConfig = Field(default_factory=NERConfig)
    processing: DocumentProcessingConfig = Field(default_factory=DocumentProcessingConfig)
    prompts: KBPromptConfig = Field(default_factory=KBPromptConfig)
    preset: Literal["legal", "technical", "creative", "code", "general", None] = None
```

### Configuration Categories

| Category | Key Parameters | Impact |
|----------|---------------|--------|
| **Chunking** | strategy, chunk_size, chunk_overlap, separators | Document segmentation quality |
| **Retrieval** | top_k, similarity_threshold, method (vector/hybrid/HyDE), MMR | Search relevance |
| **Reranking** | enabled, model, top_n | Result quality refinement |
| **Generation** | temperature, top_p, top_k, max_tokens, penalties | Response creativity/consistency |
| **NER** | enabled, confidence_threshold, entity_types | Entity extraction quality |
| **Processing** | ocr_enabled, language_detection, table_extraction | Document handling |
| **Prompts** | system_prompt, context_template, citation_style | Response behavior/tone |

---

## New Stories (7.12 - 7.17)

### Story 7.12: KB Settings Schema & Pydantic Models

**Description:** As a developer, I want typed Pydantic schemas for KB-level configuration so settings are validated and type-safe.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.12.1: ChunkingConfig schema**
**Given** I import ChunkingConfig from app.schemas.kb_settings
**Then** it includes: strategy (fixed/recursive/semantic), chunk_size (100-2000), chunk_overlap (0-500), separators (list[str])

**AC-7.12.2: RetrievalConfig schema**
**Given** I import RetrievalConfig from app.schemas.kb_settings
**Then** it includes: top_k (1-100), similarity_threshold (0.0-1.0), method (vector/hybrid/hyde), mmr_enabled, mmr_lambda, hybrid_alpha

**AC-7.12.3: RerankingConfig schema**
**Given** I import RerankingConfig from app.schemas.kb_settings
**Then** it includes: enabled (bool), model (str), top_n (1-50)

**AC-7.12.4: GenerationConfig schema**
**Given** I import GenerationConfig from app.schemas.kb_settings
**Then** it includes: temperature (0.0-2.0), top_p (0.0-1.0), top_k (1-100), max_tokens (100-16000), frequency_penalty (-2.0-2.0), presence_penalty (-2.0-2.0), stop_sequences (list[str])

**AC-7.12.5: NERConfig schema**
**Given** I import NERConfig from app.schemas.kb_settings
**Then** it includes: enabled (bool), confidence_threshold (0.0-1.0), entity_types (list[str]), batch_size (1-100)

**AC-7.12.6: DocumentProcessingConfig schema**
**Given** I import DocumentProcessingConfig from app.schemas.kb_settings
**Then** it includes: ocr_enabled (bool), language_detection (bool), table_extraction (bool), image_extraction (bool)

**AC-7.12.7: KBPromptConfig schema**
**Given** I import KBPromptConfig from app.schemas.kb_settings
**Then** it includes: system_prompt (str, max 4000 chars), context_template (str), citation_style (inline/footnote/none), uncertainty_handling (acknowledge/refuse/best_effort), response_language (str)

**AC-7.12.8: KBSettings composite schema**
**Given** I import KBSettings from app.schemas.kb_settings
**Then** it aggregates all sub-configs with default factories
**And** includes preset field for quick configuration

**AC-7.12.9: Backwards compatibility**
**Given** existing KBs have empty {} settings
**When** I parse with KBSettings
**Then** all defaults are applied without errors

**Prerequisites:** Story 7.10 (KB Model Configuration) - DONE

**Technical Notes:**
- Create `backend/app/schemas/kb_settings.py`
- Use Pydantic v2 with Field validators
- Export from `backend/app/schemas/__init__.py`
- Unit tests for validation edge cases

---

### Story 7.13: KBConfigResolver Service

**Description:** As a developer, I want a configuration resolver service so request/KB/system configs are merged with proper precedence.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.13.1: Resolve single parameter**
**Given** I call resolve_param("temperature", request_value=0.5, kb_settings, system_default=0.7)
**Then** it returns 0.5 (request wins)

**AC-7.13.2: Fallback to KB setting**
**Given** I call resolve_param("temperature", request_value=None, kb_settings={temperature: 0.3}, system_default=0.7)
**Then** it returns 0.3 (KB wins)

**AC-7.13.3: Fallback to system default**
**Given** I call resolve_param("temperature", request_value=None, kb_settings={}, system_default=0.7)
**Then** it returns 0.7 (system default)

**AC-7.13.4: Resolve full generation config**
**Given** I call resolve_generation_config(kb_id, request_overrides)
**Then** it returns merged GenerationConfig with correct precedence

**AC-7.13.5: Resolve full retrieval config**
**Given** I call resolve_retrieval_config(kb_id, request_overrides)
**Then** it returns merged RetrievalConfig with correct precedence

**AC-7.13.6: Resolve chunking config**
**Given** I call resolve_chunking_config(kb_id)
**Then** it returns ChunkingConfig from KB or system defaults

**AC-7.13.7: Get KB system prompt**
**Given** I call get_kb_system_prompt(kb_id)
**When** KB has custom system_prompt in prompts config
**Then** it returns the KB's system_prompt
**Else** it returns system default prompt

**AC-7.13.8: Cache KB settings**
**Given** multiple requests for same KB
**Then** KB settings are cached (Redis, 5min TTL)
**And** cache invalidated on KB settings update

**Prerequisites:** Story 7.12

**Technical Notes:**
- Create `backend/app/services/kb_config_resolver.py`
- Inject ConfigService and KBService as dependencies
- Use Redis for caching with pub/sub invalidation
- Unit tests for all precedence scenarios

---

### Story 7.14: KB Settings UI - General Panel

**Description:** As a KB owner, I want a settings UI to configure chunking, retrieval, and generation parameters for my Knowledge Base.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.14.1: Settings tab in KB modal**
**Given** I open KB settings modal
**Then** I see tabs: General, Models, Advanced, Prompts

**AC-7.14.2: Chunking section**
**Given** I view General tab
**Then** I see Chunking section with:
- Strategy dropdown (Fixed, Recursive, Semantic)
- Chunk size slider (100-2000, default 512)
- Chunk overlap slider (0-500, default 50)

**AC-7.14.3: Retrieval section**
**Given** I view General tab
**Then** I see Retrieval section with:
- Top K slider (1-100, default 10)
- Similarity threshold slider (0.0-1.0, default 0.7)
- Method dropdown (Vector, Hybrid, HyDE)
- MMR toggle with lambda slider

**AC-7.14.4: Generation section**
**Given** I view General tab
**Then** I see Generation section with:
- Temperature slider (0.0-2.0, default 0.7)
- Top P slider (0.0-1.0, default 1.0)
- Max tokens input (100-16000)

**AC-7.14.5: Reset to defaults button**
**Given** I have modified settings
**When** I click "Reset to Defaults"
**Then** all General settings revert to system defaults
**And** confirmation dialog shown first

**AC-7.14.6: Save settings**
**Given** I modify settings
**When** I click Save
**Then** settings are saved to KB.settings JSONB
**And** success toast shown

**AC-7.14.7: Validation feedback**
**Given** I enter invalid value (e.g., temperature > 2.0)
**Then** field shows error styling
**And** Save is disabled

**AC-7.14.8: Settings API endpoint**
**Given** I call PUT /api/v1/knowledge-bases/{id}/settings
**Then** settings JSONB is updated
**And** audit log entry created

**Prerequisites:** Story 7.12, 7.13

**Technical Notes:**
- Extend `frontend/src/components/kb/kb-settings-modal.tsx`
- Create `frontend/src/components/kb/settings/` folder
- Use shadcn/ui Slider, Select, Switch components
- React Hook Form for validation

---

### Story 7.15: KB Settings UI - Prompts Panel

**Description:** As a KB owner, I want to configure custom system prompts and citation styles for my Knowledge Base.

**Story Points:** 3

**Acceptance Criteria:**

**AC-7.15.1: Prompts tab**
**Given** I open KB settings modal
**When** I click Prompts tab
**Then** I see System Prompt section

**AC-7.15.2: System prompt editor**
**Given** I view Prompts tab
**Then** I see textarea for system prompt (max 4000 chars)
**And** character count indicator
**And** placeholder with example prompt

**AC-7.15.3: Prompt variables help**
**Given** I view system prompt editor
**Then** I see help text explaining available variables:
- {context} - Retrieved document chunks
- {query} - User's question
- {kb_name} - Knowledge Base name

**AC-7.15.4: Citation style selector**
**Given** I view Prompts tab
**Then** I see Citation Style dropdown:
- Inline [1], [2] (default)
- Footnote
- None

**AC-7.15.5: Uncertainty handling selector**
**Given** I view Prompts tab
**Then** I see "When uncertain, the AI should:" dropdown:
- Acknowledge uncertainty (default)
- Refuse to answer
- Give best effort answer

**AC-7.15.6: Response language**
**Given** I view Prompts tab
**Then** I see Response Language input (optional)
**And** placeholder: "Leave empty for auto-detect"

**AC-7.15.7: Preview prompt**
**Given** I have entered a system prompt
**When** I click "Preview"
**Then** I see rendered prompt with sample values

**AC-7.15.8: Prompt templates**
**Given** I view Prompts tab
**Then** I see "Load Template" dropdown with options:
- Default RAG
- Strict Citations
- Conversational
- Technical Documentation

**Prerequisites:** Story 7.14

**Technical Notes:**
- Create `frontend/src/components/kb/settings/prompts-panel.tsx`
- Textarea with CodeMirror or simple textarea
- Template loading from constants file

---

### Story 7.16: KB Settings Presets

**Description:** As a KB owner, I want preset configurations so I can quickly optimize my KB for common use cases.

**Story Points:** 3

**Acceptance Criteria:**

**AC-7.16.1: Preset selector in settings**
**Given** I open KB settings modal
**Then** I see "Quick Preset" dropdown at top with options:
- Custom (current)
- Legal
- Technical
- Creative
- Code
- General

**AC-7.16.2: Legal preset**
**Given** I select "Legal" preset
**Then** settings are populated with:
- temperature: 0.3
- chunk_size: 1000
- chunk_overlap: 200
- citation_style: footnote
- uncertainty_handling: acknowledge
- System prompt emphasizes accuracy and citations

**AC-7.16.3: Technical preset**
**Given** I select "Technical" preset
**Then** settings are populated with:
- temperature: 0.5
- chunk_size: 800
- chunk_overlap: 100
- citation_style: inline
- System prompt emphasizes precision and code examples

**AC-7.16.4: Creative preset**
**Given** I select "Creative" preset
**Then** settings are populated with:
- temperature: 0.9
- top_p: 0.95
- chunk_size: 500
- uncertainty_handling: best_effort
- System prompt allows creative interpretation

**AC-7.16.5: Code preset**
**Given** I select "Code" preset
**Then** settings are populated with:
- temperature: 0.2
- chunk_size: 600
- chunk_overlap: 50
- System prompt emphasizes code accuracy and syntax

**AC-7.16.6: General preset**
**Given** I select "General" preset
**Then** settings are populated with system defaults

**AC-7.16.7: Preset confirmation**
**Given** I have custom settings
**When** I select a preset
**Then** confirmation dialog warns about overwriting
**And** I can cancel or proceed

**AC-7.16.8: Preset indicator**
**Given** settings match a preset exactly
**Then** that preset is shown as selected
**When** I modify any setting
**Then** preset shows as "Custom"

**Prerequisites:** Story 7.14, 7.15

**Technical Notes:**
- Create `backend/app/core/kb_presets.py` with preset definitions
- Create `frontend/src/lib/kb-presets.ts` mirror
- API endpoint GET /api/v1/kb-presets

---

### Story 7.17: Service Integration

**Description:** As a system, I want search and generation services to use KB-level configuration so each KB behaves according to its settings.

**Story Points:** 2

**Acceptance Criteria:**

**AC-7.17.1: SearchService uses KB retrieval config**
**Given** I search in a KB with custom retrieval settings
**When** search executes
**Then** top_k, similarity_threshold, method from KB settings are used

**AC-7.17.2: GenerationService uses KB generation config**
**Given** I generate response in a KB with custom generation settings
**When** LLM call executes
**Then** temperature, top_p, max_tokens from KB settings are used

**AC-7.17.3: GenerationService uses KB system prompt**
**Given** KB has custom system_prompt
**When** I generate response
**Then** KB's system_prompt is used instead of default

**AC-7.17.4: Document worker uses KB chunking config**
**Given** I upload document to KB with custom chunking settings
**When** document is processed
**Then** chunk_size, chunk_overlap, strategy from KB settings are used

**AC-7.17.5: Request overrides still work**
**Given** KB has temperature: 0.5
**When** request includes temperature: 0.8
**Then** 0.8 is used (request wins)

**AC-7.17.6: Audit logging**
**Given** generation uses KB settings
**Then** audit log includes effective_config snapshot

**Prerequisites:** Story 7.13

**Technical Notes:**
- Modify `backend/app/services/search_service.py`
- Modify `backend/app/services/generation_service.py`
- Modify `backend/app/workers/parsing.py` and `embedding.py`
- Inject KBConfigResolver as dependency

---

## Documents to Update

### 1. Epic 7 Document (`docs/epics/epic-7-infrastructure.md`)

Add Stories 7.12-7.17 with full acceptance criteria (as detailed above).

Update summary table:
```markdown
| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| ... existing ... |
| 7.12 | 5 | KB Settings Schema & Pydantic Models |
| 7.13 | 5 | KBConfigResolver Service |
| 7.14 | 5 | KB Settings UI - General Panel |
| 7.15 | 3 | KB Settings UI - Prompts Panel |
| 7.16 | 3 | KB Settings Presets |
| 7.17 | 2 | Service Integration |

**Total Stories:** 17
**Total Story Points:** 80
```

### 2. Architecture Document (`docs/architecture/03-llm-configuration.md`)

Add new section "KB-Level Configuration":

```markdown
## KB-Level Configuration (Epic 7.12-7.17)

LumiKB supports **per-KB configuration overrides** that allow each Knowledge Base to have specialized settings for chunking, retrieval, generation, and prompts.

### Configuration Resolution

```
Request Parameters (highest priority)
       ↓ if null
KB-Level Settings (KnowledgeBase.settings JSONB)
       ↓ if null
System Defaults
```

### KB Settings Schema

The `knowledge_bases.settings` JSONB column stores a validated KBSettings structure:

| Section | Key Parameters |
|---------|---------------|
| chunking | strategy, chunk_size, chunk_overlap |
| retrieval | top_k, similarity_threshold, method, mmr_enabled |
| reranking | enabled, model, top_n |
| generation | temperature, top_p, max_tokens, penalties |
| ner | enabled, confidence_threshold, entity_types |
| processing | ocr_enabled, table_extraction |
| prompts | system_prompt, citation_style, uncertainty_handling |

### Presets

Quick configuration templates for common use cases:
- **Legal**: Low temperature (0.3), strict citations, footnote style
- **Technical**: Medium temperature (0.5), inline citations, code emphasis
- **Creative**: High temperature (0.9), flexible uncertainty handling
- **Code**: Very low temperature (0.2), syntax accuracy focus
- **General**: System defaults
```

### 3. Tech Spec (`docs/sprint-artifacts/tech-spec-epic-7.md`)

Add to "Detailed Design" section:

```markdown
### KB Settings Configuration

#### KB Settings Schema

```python
class KBSettings(BaseModel):
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    reranking: RerankingConfig
    generation: GenerationConfig
    ner: NERConfig
    processing: DocumentProcessingConfig
    prompts: KBPromptConfig
    preset: Literal["legal", "technical", "creative", "code", "general", None]
```

#### Configuration Resolution Service

```python
class KBConfigResolver:
    def resolve_generation_config(
        self,
        kb_id: UUID,
        request_overrides: dict | None = None
    ) -> GenerationConfig:
        """Merge request → KB → system configs."""

    def get_kb_system_prompt(self, kb_id: UUID) -> str:
        """Get KB's system prompt or default."""
```

#### New API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/knowledge-bases/{id}/settings` | Get KB settings |
| PUT | `/api/v1/knowledge-bases/{id}/settings` | Update KB settings |
| GET | `/api/v1/kb-presets` | List available presets |
```

Add to Acceptance Criteria section (Stories 7.12-7.17 as detailed above).

### 4. Sprint Status (`docs/sprint-artifacts/sprint-status.yaml`)

Add new stories under Epic 7:

```yaml
  # KB-Level Configuration (added 2025-12-09 via correct-course)
  7-12-kb-settings-schema: backlog  # KB settings Pydantic models
  7-13-kb-config-resolver-service: backlog  # Config resolution with precedence
  7-14-kb-settings-ui-general: backlog  # Settings UI - chunking, retrieval, generation
  7-15-kb-settings-ui-prompts: backlog  # Settings UI - system prompt, citation style
  7-16-kb-settings-presets: backlog  # Quick preset configurations
  7-17-service-integration: backlog  # SearchService, GenerationService use KB config
```

---

## Deferred Items

### EntitySchemaConfig → Epic 8

The `EntitySchemaConfig` portion (sample entities/relationships for knowledge graphs) is deferred to Epic 8 (GraphRAG) where it integrates naturally with:
- Story 8.7: KB-Domain Linking
- Story 8.8: Per-KB Entity Extraction Service

---

## Implementation Dependencies

```
7.12 (Schema) ─────┬──→ 7.13 (Resolver) ──→ 7.17 (Integration)
                   │
                   └──→ 7.14 (UI General) ──→ 7.15 (UI Prompts)
                                            │
                                            └──→ 7.16 (Presets)
```

**Recommended Execution Order:**
1. 7.12 (foundation)
2. 7.13 (service layer)
3. 7.14 + 7.17 in parallel (UI + backend integration)
4. 7.15
5. 7.16

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing KB functionality | High | Backwards-compatible schema with defaults |
| Performance impact from config resolution | Medium | Redis caching with pub/sub invalidation |
| UI complexity overwhelming users | Medium | Presets provide quick configuration |
| Schema migration for existing KBs | Low | Empty {} settings parse to defaults |

---

## SM Handover Checklist

- [ ] Review story specifications (7.12-7.17)
- [ ] Validate story point estimates
- [ ] Confirm epic assignment (Epic 7)
- [ ] Update sprint-status.yaml
- [ ] Update epic-7-infrastructure.md
- [ ] Update architecture docs (03-llm-configuration.md)
- [ ] Update tech-spec-epic-7.md
- [ ] Create story context files when ready for development
- [ ] Confirm EntitySchemaConfig deferral to Epic 8

---

## Approval

**Product Owner:** Tung Vu
**Date:** 2025-12-09
**Decision:** Approved for Epic 7 inclusion

**Scrum Master Review:** _Pending_
**Date:** _Pending_

---

_This document serves as input for the SM's correct-course workflow to implement the KB-level configuration feature._
