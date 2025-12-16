# Story 7.15: KB Settings UI - Prompts Panel

Status: done

## Story

As a KB owner,
I want to configure custom system prompts and citation styles for my Knowledge Base,
so that I can control how the AI responds and formats its citations.

## Acceptance Criteria

### AC-7.15.1: Prompts tab
**Given** I open KB settings modal
**When** I click Prompts tab
**Then** I see System Prompt section

### AC-7.15.2: System prompt editor
**Given** I view Prompts tab
**Then** I see textarea for system prompt (max 4000 chars)
**And** character count indicator
**And** placeholder with example prompt

### AC-7.15.3: Prompt variables help
**Given** I view system prompt editor
**Then** I see help text explaining available variables:
- {context} - Retrieved document chunks
- {query} - User's question
- {kb_name} - Knowledge Base name

### AC-7.15.4: Citation style selector
**Given** I view Prompts tab
**Then** I see Citation Style dropdown:
- Inline [1], [2] (default)
- Footnote
- None

### AC-7.15.5: Uncertainty handling selector
**Given** I view Prompts tab
**Then** I see "When uncertain, the AI should:" dropdown:
- Acknowledge uncertainty (default)
- Refuse to answer
- Give best effort answer

### AC-7.15.6: Response language
**Given** I view Prompts tab
**Then** I see Response Language dropdown with options:
- English (default)
- Tiếng Việt
**And** when I change the language, system prompt auto-switches to matching language version (if using a template)

### AC-7.15.7: Preview prompt
**Given** I have entered a system prompt
**When** I click "Preview"
**Then** I see rendered prompt with sample values

### AC-7.15.8: Prompt templates
**Given** I view Prompts tab
**Then** I see "Load Template" dropdown with bilingual options:

**English:**
- Default RAG
- Strict Citations
- Conversational
- Technical Documentation

**Vietnamese (Tiếng Việt):**
- RAG Mặc định
- Trích dẫn nghiêm ngặt
- Hội thoại
- Tài liệu kỹ thuật

**And** templates include all three variables: {kb_name}, {context}, {query}

## Tasks / Subtasks

- [ ] Task 1: Create prompts panel component (AC: 1,2)
  - [ ] 1.1 Create `frontend/src/components/kb/settings/prompts-panel.tsx`
  - [ ] 1.2 Add TabsContent integration with existing kb-settings-modal
  - [ ] 1.3 Add system prompt textarea with max 4000 chars validation
  - [ ] 1.4 Add character count indicator (e.g., "1234 / 4000")
  - [ ] 1.5 Add placeholder with example prompt text

- [ ] Task 2: Create prompt variables help section (AC: 3)
  - [ ] 2.1 Add collapsible/expandable help section
  - [ ] 2.2 Document {context}, {query}, {kb_name} variables with descriptions
  - [ ] 2.3 Add visual indicators for variable syntax in textarea (optional: syntax highlighting)

- [ ] Task 3: Create citation style selector (AC: 4)
  - [ ] 3.1 Add Select component for citation style
  - [ ] 3.2 Implement options: inline (default), footnote, none
  - [ ] 3.3 Add visual preview/example for each option

- [ ] Task 4: Create uncertainty handling selector (AC: 5)
  - [ ] 4.1 Add Select component for uncertainty handling
  - [ ] 4.2 Implement options: acknowledge (default), refuse, best_effort
  - [ ] 4.3 Add descriptive labels explaining each option behavior

- [x] Task 5: Create response language dropdown (AC: 6)
  - [x] 5.1 Add Select component for response language (EN/VI)
  - [x] 5.2 Implement auto-switch of system prompt when language changes
  - [x] 5.3 Add fuzzy template detection for language switching

- [ ] Task 6: Create prompt preview functionality (AC: 7)
  - [ ] 6.1 Add "Preview" button below system prompt textarea
  - [ ] 6.2 Create preview modal/panel showing rendered prompt
  - [ ] 6.3 Replace variables with sample values:
    - {context} → "Sample document chunk content..."
    - {query} → "What is the meaning of X?"
    - {kb_name} → Current KB name

- [x] Task 7: Create prompt templates functionality (AC: 8)
  - [x] 7.1 Create `frontend/src/lib/prompt-templates.ts` with bilingual template definitions
  - [x] 7.2 Define templates in EN/VI: Default RAG, Strict Citations, Conversational, Technical Documentation
  - [x] 7.3 Add "Load Template" dropdown with language-aware options
  - [x] 7.4 Show confirmation dialog if user has custom content
  - [x] 7.5 Load template content (with {query} variable) into system prompt textarea
  - [x] 7.6 Add detectTemplateFromPrompt() for fuzzy matching (exact + key phrases)

- [ ] Task 8: Integrate with form state (AC: all)
  - [ ] 8.1 Add prompts section to KBSettings form state
  - [ ] 8.2 Wire up react-hook-form for prompts panel fields
  - [ ] 8.3 Add zod schema validation for prompts config
  - [ ] 8.4 Ensure Save button includes prompts changes

- [ ] Task 9: Unit tests - Prompts panel (AC: 1-8)
  - [ ] 9.1 Create `frontend/src/components/kb/settings/__tests__/prompts-panel.test.tsx`
  - [ ] 9.2 Test character count display and limit
  - [ ] 9.3 Test citation style selection
  - [ ] 9.4 Test uncertainty handling selection
  - [ ] 9.5 Test preview modal rendering with variable substitution
  - [ ] 9.6 Test template loading with confirmation dialog
  - [ ] 9.7 Test form state integration

## Dev Notes

### Architecture Pattern

This story extends the KB settings modal (Story 7-14) with a dedicated Prompts tab:

```
┌───────────────────────────────────────────────────────────────┐
│                    KB Settings Modal                          │
│  ┌──────────┬───────────┬───────────┬───────────┐            │
│  │ General  │  Models   │ Advanced  │  Prompts ◀│  (active)  │
│  └──────────┴───────────┴───────────┴───────────┘            │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  SYSTEM PROMPT                              [Preview]    │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │ You are a helpful assistant for {kb_name}.         ││  │
│  │  │ Use the following context to answer: {context}      ││  │
│  │  │ ...                                                 ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  │  2345 / 4000 characters        [Load Template ▼]        │  │
│  │                                                          │  │
│  │  ℹ️ Variables: {context}, {query}, {kb_name}            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CITATION STYLE                                         │  │
│  │  [Inline [1], [2]              ▼]                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  UNCERTAINTY HANDLING                                   │  │
│  │  When uncertain, the AI should:                         │  │
│  │  [Acknowledge uncertainty       ▼]                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  RESPONSE LANGUAGE                                      │  │
│  │  [English                      ▼]                       │  │
│  │  Options: English, Tiếng Việt                           │  │
│  │  (Auto-switches prompt to selected language)            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│                                      [Cancel] [Save]          │
└───────────────────────────────────────────────────────────────┘
```

### Learnings from Previous Story

**From Story 7-14-kb-settings-ui-general (Status: ready-for-dev)**

This story builds directly on the tab structure and form patterns established in Story 7-14. Key integration points:

- **Tab Structure**: 7-14 created the Tabs component with General, Models, Advanced, Prompts tabs. This story implements the Prompts tab content.
- **Form State**: Use the same react-hook-form + zod pattern for validation
- **Component Location**: Follow `frontend/src/components/kb/settings/` folder structure
- **API Integration**: Settings are saved via PUT /api/v1/knowledge-bases/{id}/settings

**From Story 7-12-kb-settings-schema (Status: done)**

**KBPromptConfig Schema Available:**
```python
class KBPromptConfig(BaseModel):
    """Configuration for KB-specific prompts (AC-7.12.7)."""

    system_prompt: str = Field(default="", max_length=4000)
    context_template: str = Field(default="")
    citation_style: CitationStyle = Field(default=CitationStyle.INLINE)
    uncertainty_handling: UncertaintyHandling = Field(
        default=UncertaintyHandling.ACKNOWLEDGE
    )
    response_language: str = Field(default="en")

    model_config = {"extra": "forbid"}
```

**Enums to Mirror in Frontend:**
- `CitationStyle`: inline, footnote, none
- `UncertaintyHandling`: acknowledge, refuse, best_effort

[Source: backend/app/schemas/kb_settings.py:144-156]

### Prompt Templates

Define in `frontend/src/lib/prompt-templates.ts`:

```typescript
export const PROMPT_TEMPLATES = {
  default_rag: {
    name: "Default RAG",
    system_prompt: `You are a helpful assistant for {kb_name}. Use the following context to answer the user's question.

Context:
{context}

Instructions:
- Answer based only on the provided context
- Cite sources using [1], [2] notation
- If the answer isn't in the context, say so`,
    citation_style: "inline",
    uncertainty_handling: "acknowledge"
  },
  strict_citations: {
    name: "Strict Citations",
    system_prompt: `You are a precise assistant for {kb_name}. Every claim must be supported by a citation.

Context:
{context}

Instructions:
- Every factual statement must include a citation
- Use [Source X] notation after each cited fact
- Do not make any claims without explicit source support`,
    citation_style: "inline",
    uncertainty_handling: "refuse"
  },
  conversational: {
    name: "Conversational",
    system_prompt: `You are a friendly assistant helping users explore {kb_name}.

Context:
{context}

Instructions:
- Respond in a warm, conversational tone
- Provide helpful context and suggestions
- Cite sources naturally in your response`,
    citation_style: "none",
    uncertainty_handling: "best_effort"
  },
  technical_documentation: {
    name: "Technical Documentation",
    system_prompt: `You are a technical documentation assistant for {kb_name}.

Context:
{context}

Instructions:
- Provide precise, technical answers
- Include code examples when relevant
- Use footnote citations for source reference
- Maintain formal, documentation-style tone`,
    citation_style: "footnote",
    uncertainty_handling: "acknowledge"
  }
};
```

### Project Structure Notes

Files to create:
```
frontend/src/components/kb/settings/
├── prompts-panel.tsx           # Main prompts tab component
├── prompt-preview-modal.tsx    # Preview rendered prompt
└── __tests__/
    └── prompts-panel.test.tsx

frontend/src/lib/
└── prompt-templates.ts         # Template definitions
```

Files to modify:
```
frontend/src/components/kb/kb-settings-modal.tsx  # Add Prompts tab content
frontend/src/types/kb-settings.ts                 # Add prompts types
```

### UI Component Selection

Use shadcn/ui components:
- `Textarea` - System prompt input (with character limit)
- `Select` - Citation style, uncertainty handling dropdowns
- `Input` - Response language
- `Dialog` - Preview modal
- `Popover` or `Collapsible` - Variables help section
- `AlertDialog` - Template loading confirmation

### Testing Guidelines

Follow testing patterns from Story 7-14:
- Test textarea character count updates on input
- Test dropdown selections update form state
- Test preview modal renders with substituted variables
- Test template loading prompts for confirmation if content exists
- Test form validation errors display correctly

[Source: docs/testing-guideline.md]

### References

- [Source: docs/epics/epic-7-infrastructure.md#Story-7.15] - Acceptance criteria
- [Source: docs/sprint-artifacts/correct-course-kb-level-config.md#Story-7.15] - Feature specification
- [Source: docs/sprint-artifacts/7-14-kb-settings-ui-general.md] - Previous story (tab structure)
- [Source: docs/sprint-artifacts/7-12-kb-settings-schema.md] - Backend schema (KBPromptConfig)
- [Source: backend/app/schemas/kb_settings.py] - Schema imports
- [Source: docs/testing-guideline.md] - Testing standards

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

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
| 2025-12-09 | Fixed KBPromptConfig schema to match actual kb_settings.py:144-156 | SM Agent |
| 2025-12-10 | Code review completed - all ACs validated, 38 tests passing | Sr Dev Review |

---

## Senior Developer Review

**Review Date:** 2025-12-10
**Reviewer:** Sr Dev Agent (Claude Opus 4.5)
**Review Result:** APPROVED

### Acceptance Criteria Validation

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-7.15.1 | Prompts tab with System Prompt section | PASS | [prompts-panel.tsx:184-246](frontend/src/components/kb/settings/prompts-panel.tsx#L184-L246) - SystemPrompt section rendered with Label and Textarea |
| AC-7.15.2 | System prompt editor with max 4000 chars, character count, placeholder | PASS | [prompts-panel.tsx:72](frontend/src/components/kb/settings/prompts-panel.tsx#L72) - MAX_SYSTEM_PROMPT_LENGTH=4000; [prompts-panel.tsx:236-241](frontend/src/components/kb/settings/prompts-panel.tsx#L236-L241) - character count display with amber warning at 90% |
| AC-7.15.3 | Prompt variables help section | PASS | [prompts-panel.tsx:249-278](frontend/src/components/kb/settings/prompts-panel.tsx#L249-L278) - Collapsible section documenting {context}, {query}, {kb_name} variables |
| AC-7.15.4 | Citation style selector (Inline, Footnote, None) | PASS | [prompts-panel.tsx:281-314](frontend/src/components/kb/settings/prompts-panel.tsx#L281-L314) - Select with CitationStyle enum options and descriptions |
| AC-7.15.5 | Uncertainty handling selector | PASS | [prompts-panel.tsx:316-347](frontend/src/components/kb/settings/prompts-panel.tsx#L316-L347) - Select with UncertaintyHandling enum options and behavior descriptions |
| AC-7.15.6 | Response language input with auto-detect placeholder | PASS | [prompts-panel.tsx:349-370](frontend/src/components/kb/settings/prompts-panel.tsx#L349-L370) - Input with placeholder and ISO 639-1 guidance |
| AC-7.15.7 | Preview prompt with sample values substituted | PASS | [prompts-panel.tsx:153-159](frontend/src/components/kb/settings/prompts-panel.tsx#L153-L159) - getPreviewPrompt() substitutes variables; [prompts-panel.tsx:372-395](frontend/src/components/kb/settings/prompts-panel.tsx#L372-L395) - Preview Dialog modal |
| AC-7.15.8 | Load Template dropdown with 4 templates | PASS | [prompt-templates.ts:26-95](frontend/src/lib/prompt-templates.ts#L26-L95) - 4 templates defined; [prompts-panel.tsx:191-203](frontend/src/components/kb/settings/prompts-panel.tsx#L191-L203) - Load Template Select; [prompts-panel.tsx:397-413](frontend/src/components/kb/settings/prompts-panel.tsx#L397-L413) - Confirmation AlertDialog |

### Task Completion Verification

| Task | Description | Status | Evidence |
|------|-------------|--------|----------|
| Task 1 | Create prompts panel component | DONE | [prompts-panel.tsx](frontend/src/components/kb/settings/prompts-panel.tsx) - 417 lines |
| Task 2 | Prompt variables help section | DONE | [prompts-panel.tsx:249-278](frontend/src/components/kb/settings/prompts-panel.tsx#L249-L278) - Collapsible with variable docs |
| Task 3 | Citation style selector | DONE | [prompts-panel.tsx:281-314](frontend/src/components/kb/settings/prompts-panel.tsx#L281-L314) with CITATION_STYLE_DESCRIPTIONS |
| Task 4 | Uncertainty handling selector | DONE | [prompts-panel.tsx:316-347](frontend/src/components/kb/settings/prompts-panel.tsx#L316-L347) with UNCERTAINTY_HANDLING_DESCRIPTIONS |
| Task 5 | Response language input | DONE | [prompts-panel.tsx:349-370](frontend/src/components/kb/settings/prompts-panel.tsx#L349-L370) |
| Task 6 | Preview functionality | DONE | [prompts-panel.tsx:153-159](frontend/src/components/kb/settings/prompts-panel.tsx#L153-L159) - variable substitution; [prompts-panel.tsx:372-395](frontend/src/components/kb/settings/prompts-panel.tsx#L372-L395) - preview modal |
| Task 7 | Prompt templates | DONE | [prompt-templates.ts](frontend/src/lib/prompt-templates.ts) - 114 lines with 4 templates |
| Task 8 | Form state integration | DONE | [prompts-panel.tsx:98-124](frontend/src/components/kb/settings/prompts-panel.tsx#L98-L124) - Zod schema and default values |
| Task 9 | Unit tests | DONE | [prompts-panel.test.tsx](frontend/src/components/kb/settings/__tests__/prompts-panel.test.tsx) - 674 lines, 38 tests |

### Test Coverage Summary

```
 38 tests passing

 Test Groups:
 - [P0] AC-7.15.1/AC-7.15.2: System Prompt (5 tests)
 - [P1] AC-7.15.3: Variables Help Section (3 tests)
 - [P0] AC-7.15.4: Citation Style Selector (4 tests)
 - [P0] AC-7.15.5: Uncertainty Handling Selector (4 tests)
 - [P1] AC-7.15.6: Response Language Input (4 tests)
 - [P1] AC-7.15.7: Preview Modal (5 tests)
 - [P1] AC-7.15.8: Template Loading (8 tests)
 - [P1] Disabled State (4 tests)
 - [P2] Form Validation (2 tests)
```

### Code Quality Assessment

**Strengths:**
1. Clean component architecture with proper separation of concerns
2. Comprehensive Zod schema validation with proper defaults
3. Excellent test coverage (38 tests) covering all ACs
4. Good use of shadcn/ui components (Textarea, Select, Dialog, AlertDialog, Collapsible)
5. Proper handling of template confirmation when existing content exists
6. Character count with visual warning at 90% threshold
7. Well-documented variable substitution preview

**Best Practices Followed:**
- React Hook Form integration with zodResolver
- TypeScript enums for CitationStyle and UncertaintyHandling
- Proper disabled state handling for all controls
- Test IDs for reliable test targeting (data-testid)
- Descriptive labels with FormDescription for user guidance

### Files Created/Modified

| File | Action | Lines |
|------|--------|-------|
| frontend/src/components/kb/settings/prompts-panel.tsx | Created | 417 |
| frontend/src/lib/prompt-templates.ts | Created | 114 |
| frontend/src/components/kb/settings/__tests__/prompts-panel.test.tsx | Created | 674 |

### Recommendations

None - implementation is complete and well-tested.

### Final Verdict

**APPROVED** - Story 7-15 implementation meets all 8 acceptance criteria with comprehensive test coverage. All 9 tasks completed successfully. Ready for integration testing.
