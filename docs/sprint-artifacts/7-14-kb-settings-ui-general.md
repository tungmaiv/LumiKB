# Story 7.14: KB Settings UI - General Panel

Status: done

## Story

As a KB owner,
I want a settings UI to configure chunking, retrieval, and generation parameters,
so that I can optimize my Knowledge Base behavior for specific use cases.

## Acceptance Criteria

### AC-7.14.1: Settings tab structure in KB modal
**Given** I open KB settings modal
**Then** I see tabs: General, Models, Advanced, Prompts

### AC-7.14.2: Chunking section
**Given** I view General tab
**Then** I see Chunking section with:
- Strategy dropdown (Fixed, Recursive, Semantic)
- Chunk size slider (100-2000, default 512)
- Chunk overlap slider (0-500, default 50)

### AC-7.14.3: Retrieval section
**Given** I view General tab
**Then** I see Retrieval section with:
- Top K slider (1-100, default 10)
- Similarity threshold slider (0.0-1.0, default 0.7)
- Method dropdown (Vector, Hybrid, HyDE)
- MMR toggle with lambda slider

### AC-7.14.4: Generation section
**Given** I view General tab
**Then** I see Generation section with:
- Temperature slider (0.0-2.0, default 0.7)
- Top P slider (0.0-1.0, default 1.0)
- Max tokens input (100-16000)

### AC-7.14.5: Reset to defaults button
**Given** I have modified settings
**When** I click "Reset to Defaults"
**Then** all General settings revert to system defaults
**And** confirmation dialog shown first

### AC-7.14.6: Save settings
**Given** I modify settings
**When** I click Save
**Then** settings are saved to KB.settings JSONB
**And** success toast shown

### AC-7.14.7: Validation feedback
**Given** I enter invalid value (e.g., temperature > 2.0)
**Then** field shows error styling
**And** Save is disabled

### AC-7.14.8: Settings API endpoint
**Given** I call PUT /api/v1/knowledge-bases/{id}/settings
**Then** settings JSONB is updated
**And** audit log entry created

## Tasks / Subtasks

- [ ] Task 1: Create tab structure in KB settings modal (AC: 1)
  - [ ] 1.1 Add Tabs component to `kb-settings-modal.tsx`
  - [ ] 1.2 Create General tab as default tab
  - [ ] 1.3 Create Models tab (move existing model selection content)
  - [ ] 1.4 Create Advanced tab placeholder
  - [ ] 1.5 Create Prompts tab placeholder

- [ ] Task 2: Create KB Settings types for frontend (AC: 2,3,4)
  - [ ] 2.1 Create `frontend/src/types/kb-settings.ts` with TypeScript interfaces
  - [ ] 2.2 Add ChunkingConfig, RetrievalConfig, GenerationConfig types
  - [ ] 2.3 Add enum types for ChunkingStrategy, RetrievalMethod, CitationStyle
  - [ ] 2.4 Add KBSettings composite type mirroring backend schema

- [ ] Task 3: Create Chunking section component (AC: 2)
  - [ ] 3.1 Create `frontend/src/components/kb/settings/chunking-section.tsx`
  - [ ] 3.2 Add strategy dropdown (Fixed, Recursive, Semantic)
  - [ ] 3.3 Add chunk size slider with range 100-2000 (default 512)
  - [ ] 3.4 Add chunk overlap slider with range 0-500 (default 50)
  - [ ] 3.5 Add form validation using zod schema

- [ ] Task 4: Create Retrieval section component (AC: 3)
  - [ ] 4.1 Create `frontend/src/components/kb/settings/retrieval-section.tsx`
  - [ ] 4.2 Add Top K slider with range 1-100 (default 10)
  - [ ] 4.3 Add Similarity threshold slider with range 0.0-1.0 (default 0.7)
  - [ ] 4.4 Add Method dropdown (Vector, Hybrid, HyDE)
  - [ ] 4.5 Add MMR enabled toggle
  - [ ] 4.6 Add MMR lambda slider (0.0-1.0), visible only when MMR enabled

- [ ] Task 5: Create Generation section component (AC: 4)
  - [ ] 5.1 Create `frontend/src/components/kb/settings/generation-section.tsx`
  - [ ] 5.2 Add Temperature slider with range 0.0-2.0 (default 0.7)
  - [ ] 5.3 Add Top P slider with range 0.0-1.0 (default 1.0)
  - [ ] 5.4 Add Max tokens input with range 100-16000

- [ ] Task 6: Implement General tab with all sections (AC: 2,3,4,5,7)
  - [ ] 6.1 Create `frontend/src/components/kb/settings/general-panel.tsx`
  - [ ] 6.2 Integrate ChunkingSection, RetrievalSection, GenerationSection
  - [ ] 6.3 Add form state management with react-hook-form
  - [ ] 6.4 Add validation feedback (error styling, disable Save)
  - [ ] 6.5 Add Reset to Defaults button with confirmation dialog

- [ ] Task 7: Create useKBSettings hook (AC: 6,8)
  - [ ] 7.1 Create `frontend/src/hooks/useKBSettings.ts`
  - [ ] 7.2 Implement GET /api/v1/knowledge-bases/{id}/settings query
  - [ ] 7.3 Implement PUT /api/v1/knowledge-bases/{id}/settings mutation
  - [ ] 7.4 Add React Query caching (5min stale time)
  - [ ] 7.5 Add optimistic updates with rollback

- [ ] Task 8: Backend - KB Settings API endpoint (AC: 8)
  - [ ] 8.1 Add GET /api/v1/knowledge-bases/{id}/settings endpoint
  - [ ] 8.2 Add PUT /api/v1/knowledge-bases/{id}/settings endpoint
  - [ ] 8.3 Validate settings against KBSettings schema
  - [ ] 8.4 Call KBConfigResolver.invalidate_kb_settings_cache() on update
  - [ ] 8.5 Add audit log entry on settings change

- [ ] Task 9: Unit tests - Frontend components (AC: 1-7)
  - [ ] 9.1 Create `frontend/src/components/kb/settings/__tests__/chunking-section.test.tsx`
  - [ ] 9.2 Create `frontend/src/components/kb/settings/__tests__/retrieval-section.test.tsx`
  - [ ] 9.3 Create `frontend/src/components/kb/settings/__tests__/generation-section.test.tsx`
  - [ ] 9.4 Create `frontend/src/components/kb/settings/__tests__/general-panel.test.tsx`
  - [ ] 9.5 Test validation error display
  - [ ] 9.6 Test Reset to Defaults flow

- [ ] Task 10: Unit tests - useKBSettings hook (AC: 6)
  - [ ] 10.1 Create `frontend/src/hooks/__tests__/useKBSettings.test.ts`
  - [ ] 10.2 Test GET settings query
  - [ ] 10.3 Test PUT settings mutation
  - [ ] 10.4 Test optimistic updates
  - [ ] 10.5 Test error handling

- [ ] Task 11: Integration tests - Backend API (AC: 8)
  - [ ] 11.1 Create `backend/tests/integration/test_kb_settings_api.py`
  - [ ] 11.2 Test GET /settings returns KB settings
  - [ ] 11.3 Test PUT /settings updates KB settings
  - [ ] 11.4 Test PUT /settings validates against schema
  - [ ] 11.5 Test PUT /settings creates audit log entry
  - [ ] 11.6 Test PUT /settings invalidates cache

## Dev Notes

### Architecture Pattern

This story extends the existing KB settings modal with a tabbed interface and comprehensive configuration forms:

```
┌───────────────────────────────────────────────────────────────┐
│                    KB Settings Modal                          │
│  ┌──────────┬───────────┬───────────┬───────────┐            │
│  │ General  │  Models   │ Advanced  │  Prompts  │  (tabs)    │
│  └──────────┴───────────┴───────────┴───────────┘            │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CHUNKING                                                │  │
│  │  Strategy: [Fixed ▼]  Size: [──●──512──]  Overlap: [50] │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  RETRIEVAL                                               │  │
│  │  Top K: [──●──10──]  Threshold: [0.7]  Method: [Vector▼] │  │
│  │  [✓] MMR  Lambda: [──●──0.5──]                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  GENERATION                                              │  │
│  │  Temperature: [──●──0.7──]  Top P: [1.0]  Max: [4096]   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  [Reset to Defaults]                    [Cancel] [Save]       │
└───────────────────────────────────────────────────────────────┘
```

### Learnings from Previous Story

**From Story 7-13-kb-config-resolver-service (Status: done)**

**Files Created - INTEGRATE with these:**
- `backend/app/services/kb_config_resolver.py` (382 lines) - Config resolution service with caching
- `backend/tests/unit/test_kb_config_resolver.py` (1264 lines, 38 tests)
- `backend/tests/integration/test_kb_config_resolver_api.py` (583 lines, 18 tests)

**Key Methods to Use:**
- `KBConfigResolver.invalidate_kb_settings_cache(kb_id)` - Call after PUT /settings to clear cache
- `get_kb_config_resolver()` - Factory function for dependency injection

**Architecture Established:**
- Three-layer resolution: Request → KB → System defaults
- Redis caching with 5min TTL
- Graceful degradation on cache failures

**Code Review Outcome:** APPROVED (56/56 tests passing)

[Source: docs/sprint-artifacts/7-13-kb-config-resolver-service.md#Dev-Agent-Record]

**From Story 7-12-kb-settings-schema (Status: done)**

**Schemas Available - IMPORT these:**
- `ChunkingConfig` - chunking settings with strategy, chunk_size, chunk_overlap
- `RetrievalConfig` - retrieval settings with top_k, similarity_threshold, method, mmr_*
- `GenerationConfig` - generation settings with temperature, top_p, max_tokens
- `KBSettings` - composite schema for KB.settings JSONB

**Enums to Mirror in Frontend:**
- `ChunkingStrategy`: fixed, recursive, semantic
- `RetrievalMethod`: vector, hybrid, hyde

**Default Values (from schemas):**
- chunk_size: 512, chunk_overlap: 50, strategy: recursive
- top_k: 10, similarity_threshold: 0.7, method: vector
- temperature: 0.7, top_p: 1.0, max_tokens: 4096

[Source: docs/sprint-artifacts/7-12-kb-settings-schema.md#Dev-Agent-Record]

### Existing Modal Structure

The current `kb-settings-modal.tsx` (251 lines) contains model selection (embedding + generation). This will be moved to the "Models" tab while adding the new General, Advanced, and Prompts tabs.

Current features to preserve:
- Embedding model selection with dimension mismatch warning
- Generation model selection
- Form state management with react-hook-form + zod

### Project Structure Notes

Frontend files to create:
```
frontend/src/components/kb/settings/
├── chunking-section.tsx
├── retrieval-section.tsx
├── generation-section.tsx
├── general-panel.tsx
└── __tests__/
    ├── chunking-section.test.tsx
    ├── retrieval-section.test.tsx
    ├── generation-section.test.tsx
    └── general-panel.test.tsx

frontend/src/types/
└── kb-settings.ts

frontend/src/hooks/
├── useKBSettings.ts
└── __tests__/
    └── useKBSettings.test.ts
```

Backend files to modify:
```
backend/app/api/v1/knowledge_bases.py  # Add GET/PUT /settings endpoints
backend/tests/integration/test_kb_settings_api.py  # New integration tests
```

### UI Component Selection

Use shadcn/ui components:
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` - Tab navigation
- `Slider` - Range inputs (chunk_size, temperature, etc.)
- `Select` - Dropdown for strategy/method enums
- `Switch` - Toggle for MMR enabled
- `Input` - Numeric input for max_tokens
- `AlertDialog` - Reset to defaults confirmation
- `Form` components - Already used in existing modal

### API Contract

```typescript
// GET /api/v1/knowledge-bases/{id}/settings
interface KBSettingsResponse {
  chunking: ChunkingConfig;
  retrieval: RetrievalConfig;
  generation: GenerationConfig;
  // ... other configs from KBSettings
}

// PUT /api/v1/knowledge-bases/{id}/settings
interface KBSettingsUpdate {
  chunking?: Partial<ChunkingConfig>;
  retrieval?: Partial<RetrievalConfig>;
  generation?: Partial<GenerationConfig>;
}
```

### Testing Guidelines

Follow testing patterns from `docs/testing-guideline.md`:
- Use React Testing Library for component tests
- Test user interactions (slider changes, dropdown selections)
- Test form validation error display
- Mock API calls with MSW or vitest mocking
- Test confirmation dialog flow for Reset to Defaults

[Source: docs/testing-guideline.md]

### References

- [Source: docs/sprint-artifacts/correct-course-kb-level-config.md#Story-7.14] - Primary requirements source
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md] - Technical architecture
- [Source: docs/sprint-artifacts/7-13-kb-config-resolver-service.md#Dev-Agent-Record] - Previous story learnings
- [Source: docs/sprint-artifacts/7-12-kb-settings-schema.md#Dev-Agent-Record] - Schema definitions
- [Source: frontend/src/components/kb/kb-settings-modal.tsx] - Existing modal to extend
- [Source: backend/app/schemas/kb_settings.py] - Backend schema imports
- [Source: docs/testing-guideline.md] - Testing standards

## Dev Agent Record

### Context Reference

- [7-14-kb-settings-ui-general.context.xml](7-14-kb-settings-ui-general.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-09 | Story drafted from correct-course requirements | SM Agent |
