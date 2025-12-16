# Story 7.16: KB Settings Presets

Status: done

## Story

As a KB owner,
I want preset configurations so I can quickly optimize my KB for common use cases,
without manually configuring each individual setting.

## Acceptance Criteria

### AC-7.16.1: Preset selector in settings
**Given** I open KB settings modal
**Then** I see "Quick Preset" dropdown at top with options:
- Custom (current)
- Legal
- Technical
- Creative
- Code
- General

### AC-7.16.2: Legal preset
**Given** I select "Legal" preset
**Then** settings are populated with:
- temperature: 0.3
- chunk_size: 1000
- chunk_overlap: 200
- citation_style: footnote
- uncertainty_handling: acknowledge
- System prompt emphasizes accuracy and citations

### AC-7.16.3: Technical preset
**Given** I select "Technical" preset
**Then** settings are populated with:
- temperature: 0.5
- chunk_size: 800
- chunk_overlap: 100
- citation_style: inline
- System prompt emphasizes precision and code examples

### AC-7.16.4: Creative preset
**Given** I select "Creative" preset
**Then** settings are populated with:
- temperature: 0.9
- top_p: 0.95
- chunk_size: 500
- uncertainty_handling: best_effort
- System prompt allows creative interpretation

### AC-7.16.5: Code preset
**Given** I select "Code" preset
**Then** settings are populated with:
- temperature: 0.2
- chunk_size: 600
- chunk_overlap: 50
- System prompt emphasizes code accuracy and syntax

### AC-7.16.6: General preset
**Given** I select "General" preset
**Then** settings are populated with system defaults

### AC-7.16.7: Preset confirmation
**Given** I have custom settings
**When** I select a preset
**Then** confirmation dialog warns about overwriting
**And** I can cancel or proceed

### AC-7.16.8: Preset indicator
**Given** settings match a preset exactly
**Then** that preset is shown as selected
**When** I modify any setting
**Then** preset shows as "Custom"

## Tasks / Subtasks

- [ ] Task 1: Create backend preset definitions (AC: 2-6)
  - [ ] 1.1 Create `backend/app/core/kb_presets.py`
  - [ ] 1.2 Define KB_PRESETS dict with legal, technical, creative, code, general
  - [ ] 1.3 Each preset includes: chunking, retrieval, generation, prompts configs
  - [ ] 1.4 Define system prompts for each preset type
  - [ ] 1.5 Add get_preset(name) and list_presets() helper functions

- [ ] Task 2: Create backend presets API endpoint (AC: 1)
  - [ ] 2.1 Add GET /api/v1/kb-presets endpoint to knowledge_bases.py
  - [ ] 2.2 Return list of presets with names, descriptions, and config previews
  - [ ] 2.3 Add PresetInfo and PresetListResponse schemas

- [ ] Task 3: Create frontend preset types (AC: 1-8)
  - [ ] 3.1 Create `frontend/src/lib/kb-presets.ts`
  - [ ] 3.2 Mirror backend preset definitions in TypeScript
  - [ ] 3.3 Add KBPreset type with name, description, settings
  - [ ] 3.4 Export PRESET_OPTIONS for dropdown use

- [ ] Task 4: Create preset selector component (AC: 1, 7)
  - [ ] 4.1 Create `frontend/src/components/kb/settings/preset-selector.tsx`
  - [ ] 4.2 Add Select dropdown with preset options
  - [ ] 4.3 Show current preset name or "Custom" indicator
  - [ ] 4.4 Add confirmation dialog using AlertDialog component

- [ ] Task 5: Integrate preset selector with KB settings modal (AC: 1)
  - [ ] 5.1 Add PresetSelector at top of kb-settings-modal tabs
  - [ ] 5.2 Pass form setValue function for populating settings
  - [ ] 5.3 Wire up preset selection to update all form fields

- [ ] Task 6: Implement preset detection logic (AC: 8)
  - [ ] 6.1 Add usePresetDetection hook or utility function
  - [ ] 6.2 Compare current settings against all preset definitions
  - [ ] 6.3 Return matching preset name or "custom"
  - [ ] 6.4 Update selector display when settings change

- [ ] Task 7: Implement preset application logic (AC: 2-6, 7)
  - [ ] 7.1 On preset selection, check if settings are modified
  - [ ] 7.2 Show confirmation dialog if custom settings exist
  - [ ] 7.3 On confirm, apply all preset values to form state
  - [ ] 7.4 On cancel, keep current settings

- [ ] Task 8: Update KBSettings schema for preset tracking (AC: 8)
  - [ ] 8.1 Ensure preset field in KBSettings schema is persisted
  - [ ] 8.2 Update preset field when settings saved
  - [ ] 8.3 Auto-detect preset on settings load

- [ ] Task 9: Unit tests - Backend presets (AC: 2-6)
  - [ ] 9.1 Create `backend/tests/unit/test_kb_presets.py`
  - [ ] 9.2 Test each preset has required config values
  - [ ] 9.3 Test get_preset() returns correct preset
  - [ ] 9.4 Test list_presets() returns all presets

- [ ] Task 10: Unit tests - Frontend preset selector (AC: 1, 7, 8)
  - [ ] 10.1 Create `frontend/src/components/kb/settings/__tests__/preset-selector.test.tsx`
  - [ ] 10.2 Test dropdown renders all preset options
  - [ ] 10.3 Test confirmation dialog appears on selection
  - [ ] 10.4 Test preset detection shows correct indicator
  - [ ] 10.5 Test settings are populated on preset application

- [ ] Task 11: Integration tests - Presets API (AC: 1)
  - [ ] 11.1 Create `backend/tests/integration/test_kb_presets_api.py`
  - [ ] 11.2 Test GET /kb-presets returns all presets
  - [ ] 11.3 Test preset definitions are valid KBSettings

## Dev Notes

### Architecture Pattern

This story adds a preset layer on top of the KB settings UI (Stories 7-14, 7-15):

```
┌───────────────────────────────────────────────────────────────┐
│                    KB Settings Modal                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  QUICK PRESET: [Custom ▼]  ◀── Preset selector          │  │
│  │                                                          │  │
│  │  Options: Custom | Legal | Technical | Creative |       │  │
│  │           Code | General                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────┬───────────┬───────────┬───────────┐            │
│  │ General ◀│  Models   │ Advanced  │  Prompts  │  (tabs)    │
│  └──────────┴───────────┴───────────┴───────────┘            │
│                                                                │
│  [When preset selected, all tabs populated automatically]     │
│                                                                │
│                                      [Cancel] [Save]          │
└───────────────────────────────────────────────────────────────┘
```

### Learnings from Previous Stories

**From Story 7-14-kb-settings-ui-general (Status: ready-for-dev)**

- Tab structure and form patterns established in 7-14
- react-hook-form + zod validation pattern
- Chunking, Retrieval, Generation sections
- Reset to Defaults functionality (similar to preset application)

**From Story 7-15-kb-settings-ui-prompts (Status: drafted)**

- Prompts panel with system_prompt, citation_style, uncertainty_handling
- Prompt templates (Default RAG, Strict Citations, etc.)
- Prompt templates conceptually similar to presets but scoped to prompts only

**From Story 7-12-kb-settings-schema (Status: done)**

**KBSettings Schema Already Has preset Field:**
```python
class KBSettings(BaseModel):
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    # ... other configs ...
    preset: str | None = Field(
        default=None,
        description="Preset name used for configuration"
    )
```

This field should be updated when a preset is applied.

[Source: backend/app/schemas/kb_settings.py:261-264]

### Preset Definitions

Define in `backend/app/core/kb_presets.py`:

```python
from app.schemas.kb_settings import (
    KBSettings, ChunkingConfig, RetrievalConfig, GenerationConfig,
    KBPromptConfig, CitationStyle, UncertaintyHandling, ChunkingStrategy
)

KB_PRESETS = {
    "legal": {
        "name": "Legal",
        "description": "Optimized for legal documents with strict citations",
        "settings": {
            "chunking": {
                "strategy": "recursive",
                "chunk_size": 1000,
                "chunk_overlap": 200,
            },
            "retrieval": {
                "top_k": 15,
                "similarity_threshold": 0.75,
                "method": "vector",
            },
            "generation": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 4096,
            },
            "prompts": {
                "system_prompt": """You are a precise legal document assistant for {kb_name}.

Context:
{context}

Instructions:
- Cite every claim with footnote notation
- Never speculate beyond the provided documents
- Emphasize accuracy and exact wording
- When uncertain, clearly state limitations
- Maintain formal, professional language""",
                "citation_style": "footnote",
                "uncertainty_handling": "acknowledge",
            },
            "preset": "legal",
        },
    },
    "technical": {
        "name": "Technical",
        "description": "Optimized for technical documentation with inline citations",
        "settings": {
            "chunking": {
                "strategy": "recursive",
                "chunk_size": 800,
                "chunk_overlap": 100,
            },
            "retrieval": {
                "top_k": 10,
                "similarity_threshold": 0.7,
                "method": "vector",
            },
            "generation": {
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 4096,
            },
            "prompts": {
                "system_prompt": """You are a technical documentation assistant for {kb_name}.

Context:
{context}

Instructions:
- Provide precise, technical answers
- Include code examples when relevant
- Use inline citations [1], [2] for sources
- Explain concepts clearly with examples
- Reference specific documentation sections""",
                "citation_style": "inline",
                "uncertainty_handling": "acknowledge",
            },
            "preset": "technical",
        },
    },
    "creative": {
        "name": "Creative",
        "description": "Higher creativity for brainstorming and exploration",
        "settings": {
            "chunking": {
                "strategy": "semantic",
                "chunk_size": 500,
                "chunk_overlap": 75,
            },
            "retrieval": {
                "top_k": 8,
                "similarity_threshold": 0.6,
                "method": "vector",
            },
            "generation": {
                "temperature": 0.9,
                "top_p": 0.95,
                "max_tokens": 4096,
            },
            "prompts": {
                "system_prompt": """You are a creative assistant exploring {kb_name}.

Context:
{context}

Instructions:
- Provide insightful, creative interpretations
- Make connections between different ideas
- Feel free to suggest new perspectives
- Be conversational and engaging
- Offer possibilities and alternatives""",
                "citation_style": "none",
                "uncertainty_handling": "best_effort",
            },
            "preset": "creative",
        },
    },
    "code": {
        "name": "Code",
        "description": "Optimized for code repositories and programming",
        "settings": {
            "chunking": {
                "strategy": "recursive",
                "chunk_size": 600,
                "chunk_overlap": 50,
            },
            "retrieval": {
                "top_k": 12,
                "similarity_threshold": 0.72,
                "method": "vector",
            },
            "generation": {
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 4096,
            },
            "prompts": {
                "system_prompt": """You are a code assistant for {kb_name}.

Context:
{context}

Instructions:
- Provide accurate code with correct syntax
- Explain code functionality clearly
- Reference specific files and line numbers
- Follow established patterns in the codebase
- Suggest best practices when relevant""",
                "citation_style": "inline",
                "uncertainty_handling": "refuse",
            },
            "preset": "code",
        },
    },
    "general": {
        "name": "General",
        "description": "Balanced defaults for general knowledge bases",
        "settings": {
            # Uses system defaults
            "preset": "general",
        },
    },
}

def get_preset(name: str) -> dict | None:
    """Get preset configuration by name."""
    return KB_PRESETS.get(name)

def list_presets() -> list[dict]:
    """List all available presets with metadata."""
    return [
        {
            "id": key,
            "name": preset["name"],
            "description": preset["description"],
        }
        for key, preset in KB_PRESETS.items()
    ]
```

### Frontend Mirror

Define in `frontend/src/lib/kb-presets.ts`:

```typescript
export interface KBPreset {
  id: string;
  name: string;
  description: string;
  settings: Partial<KBSettings>;
}

export const KB_PRESETS: Record<string, KBPreset> = {
  legal: {
    id: "legal",
    name: "Legal",
    description: "Optimized for legal documents with strict citations",
    settings: {
      chunking: {
        strategy: "recursive",
        chunk_size: 1000,
        chunk_overlap: 200,
      },
      generation: {
        temperature: 0.3,
        top_p: 0.9,
      },
      prompts: {
        citation_style: "footnote",
        uncertainty_handling: "acknowledge",
      },
      preset: "legal",
    },
  },
  // ... other presets
};

export const PRESET_OPTIONS = [
  { value: "custom", label: "Custom" },
  { value: "legal", label: "Legal" },
  { value: "technical", label: "Technical" },
  { value: "creative", label: "Creative" },
  { value: "code", label: "Code" },
  { value: "general", label: "General" },
];

export function detectPreset(settings: KBSettings): string {
  // Compare settings against each preset
  // Return matching preset id or "custom"
}
```

### Project Structure Notes

Files to create:
```
backend/app/core/
└── kb_presets.py              # Preset definitions and helpers

backend/tests/unit/
└── test_kb_presets.py         # Preset unit tests

backend/tests/integration/
└── test_kb_presets_api.py     # API integration tests

frontend/src/lib/
└── kb-presets.ts              # Frontend preset definitions

frontend/src/components/kb/settings/
├── preset-selector.tsx        # Preset dropdown component
└── __tests__/
    └── preset-selector.test.tsx
```

Files to modify:
```
backend/app/api/v1/knowledge_bases.py  # Add GET /kb-presets endpoint
frontend/src/components/kb/kb-settings-modal.tsx  # Add PresetSelector
```

### UI Component Selection

Use shadcn/ui components:
- `Select` - Preset dropdown
- `AlertDialog` - Confirmation before overwriting custom settings
- `Badge` - Optional indicator showing current preset

### Preset Detection Algorithm

```typescript
function detectPreset(currentSettings: KBSettings): string {
  for (const [presetId, preset] of Object.entries(KB_PRESETS)) {
    if (presetId === "general") continue; // Check general last
    if (settingsMatchPreset(currentSettings, preset.settings)) {
      return presetId;
    }
  }

  // Check if all defaults (general)
  if (isDefaultSettings(currentSettings)) {
    return "general";
  }

  return "custom";
}

function settingsMatchPreset(
  current: KBSettings,
  presetSettings: Partial<KBSettings>
): boolean {
  // Deep compare relevant fields
  // Return true if all preset fields match current values
}
```

### Testing Guidelines

Follow testing patterns from Story 7-14:
- Test preset definitions have required fields
- Test preset application populates all form fields
- Test confirmation dialog appears when modifying custom settings
- Test preset detection correctly identifies matching presets
- Test "Custom" indicator appears after any modification

[Source: docs/testing-guideline.md]

### References

- [Source: docs/epics/epic-7-infrastructure.md:905-983] - Story 7.16 acceptance criteria (AC-7.16.1 through AC-7.16.8)
- [Source: docs/sprint-artifacts/correct-course-kb-level-config.md#Story-7.16] - Feature specification with preset details
- [Source: docs/sprint-artifacts/7-14-kb-settings-ui-general.md:141-172] - Tab structure and form patterns
- [Source: docs/sprint-artifacts/7-15-kb-settings-ui-prompts.md:196-259] - Prompt templates pattern
- [Source: backend/app/schemas/kb_settings.py:18-65] - Enum types (ChunkingStrategy, CitationStyle, UncertaintyHandling)
- [Source: backend/app/schemas/kb_settings.py:72-119] - Sub-config schemas (ChunkingConfig, RetrievalConfig, GenerationConfig)
- [Source: backend/app/schemas/kb_settings.py:239-267] - KBSettings composite with preset field
- [Source: docs/testing-guideline.md] - Testing standards

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- `backend/app/core/kb_presets.py` (299 lines) - Core preset definitions
- `backend/app/api/v1/knowledge_bases.py:210-298` - Presets API endpoints
- `backend/tests/unit/test_kb_presets.py` (393 lines, 30 tests)
- `backend/tests/integration/test_kb_presets_api.py` (335 lines, 15 tests)
- `frontend/src/components/kb/settings/preset-selector.tsx` (296 lines)
- `frontend/src/components/kb/settings/__tests__/preset-selector.test.tsx`
- `frontend/src/lib/kb-presets.ts` - Frontend preset definitions
- `frontend/e2e/tests/kb/kb-settings-presets.spec.ts` (527 lines, 15 E2E tests)

---

## Code Review Notes

### Review Date: 2025-12-10

### Reviewer: Dev Agent (Claude Opus 4.5)

### Review Outcome: **APPROVED** ✅

### AC Validation Summary

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-7.16.1 | Quick Preset dropdown in settings | ✅ IMPLEMENTED | `frontend/src/components/kb/settings/preset-selector.tsx:234-267`, `backend/app/api/v1/knowledge_bases.py:210-234` |
| AC-7.16.2 | Legal preset values | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:40-79`, `backend/tests/unit/test_kb_presets.py:43-63` |
| AC-7.16.3 | Technical preset values | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:80-117`, `backend/tests/unit/test_kb_presets.py:65-81` |
| AC-7.16.4 | Creative preset values | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:118-159`, `backend/tests/unit/test_kb_presets.py:82-100` |
| AC-7.16.5 | Code preset values | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:160-200`, unit tests verify temp=0.2 |
| AC-7.16.6 | General preset (defaults) | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:201-218` |
| AC-7.16.7 | Confirmation dialog | ✅ IMPLEMENTED | `frontend/src/components/kb/settings/preset-selector.tsx:269-290`, E2E tests verify |
| AC-7.16.8 | Preset detection indicator | ✅ IMPLEMENTED | `backend/app/core/kb_presets.py:253-299`, `backend/app/api/v1/knowledge_bases.py:237-262` |

### Test Coverage

- **Unit Tests**: 30 tests in `test_kb_presets.py` covering preset definitions, retrieval, detection
- **Integration Tests**: 15 tests in `test_kb_presets_api.py` covering API endpoints
- **E2E Tests**: 15 tests in `kb-settings-presets.spec.ts` covering UI flows
- **Total**: 60 tests covering Story 7-16

### Findings

**Strengths:**
1. Complete implementation of all 5 presets (legal, technical, creative, code, general)
2. Comprehensive test coverage at all levels (unit, integration, E2E)
3. Clean separation of concerns: core preset logic in `kb_presets.py`, API in router, UI in component
4. Confirmation dialog properly warns users before overwriting custom settings
5. Preset detection correctly identifies matching presets and shows "Custom" for modified settings

**No Issues Found.**

### Recommendation

Story 7-16 meets all acceptance criteria with comprehensive test coverage. **APPROVED for DONE status.**

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-09 | Story drafted from correct-course requirements | SM Agent |
| 2025-12-09 | Added specific line number citations to References section | SM Agent |
| 2025-12-10 | Code review completed - APPROVED | Dev Agent |
