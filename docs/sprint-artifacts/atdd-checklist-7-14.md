# ATDD Checklist: Story 7-14 - KB Settings UI - General Panel

**Story**: 7-14 KB Settings UI - General Panel
**Generated**: 2025-12-09
**Status**: Tests Generated - Implementation Required

## Overview

This checklist tracks the implementation of Story 7-14 following ATDD (Acceptance Test-Driven Development) methodology. All tests are written to FAIL until implementation is complete.

## Acceptance Criteria Coverage

| AC | Description | E2E | Component | Hook | API | Status |
|----|-------------|-----|-----------|------|-----|--------|
| AC-7.14.1 | General Tab with configuration sections | ✅ | ✅ | - | - | ❌ Failing |
| AC-7.14.2 | Chunking configuration controls | ✅ | ✅ | - | - | ❌ Failing |
| AC-7.14.3 | Retrieval configuration controls | ✅ | ✅ | - | - | ❌ Failing |
| AC-7.14.4 | Generation configuration controls | ✅ | ✅ | - | - | ❌ Failing |
| AC-7.14.5 | Reset to Defaults functionality | ✅ | ✅ | - | - | ❌ Failing |
| AC-7.14.6 | Save Settings with feedback | ✅ | - | ✅ | ✅ | ❌ Failing |
| AC-7.14.7 | Form validation with error messages | ✅ | ✅ | - | ✅ | ❌ Failing |
| AC-7.14.8 | Settings API endpoints | - | - | ✅ | ✅ | ❌ Failing |

## Test Files Generated

### Backend Tests
- [x] `backend/tests/integration/test_kb_settings_api.py` - 18 test cases

### Frontend Tests
- [x] `frontend/e2e/tests/kb/kb-settings-general.spec.ts` - 14 test cases
- [x] `frontend/src/components/kb/settings/__tests__/chunking-section.test.tsx` - 8 test cases
- [x] `frontend/src/components/kb/settings/__tests__/retrieval-section.test.tsx` - 9 test cases
- [x] `frontend/src/components/kb/settings/__tests__/generation-section.test.tsx` - 8 test cases
- [x] `frontend/src/components/kb/settings/__tests__/general-panel.test.tsx` - 11 test cases
- [x] `frontend/src/hooks/__tests__/useKBSettings.test.ts` - 11 test cases

### Test Data Factories
- [x] `frontend/e2e/fixtures/kb-settings.factory.ts`

## Implementation Checklist

### Phase 1: Backend API (Priority: P0)

#### 1.1 Add Settings Endpoints to KB Router
**File**: `backend/app/api/v1/knowledge_bases.py`

```python
# Add these endpoints:
@router.get("/{kb_id}/settings", response_model=KBSettings)
async def get_kb_settings(kb_id: UUID, ...) -> KBSettings:
    """AC-7.14.8: GET /settings returns KB settings."""
    pass

@router.put("/{kb_id}/settings", response_model=KBSettings)
async def update_kb_settings(kb_id: UUID, settings: KBSettingsUpdate, ...) -> KBSettings:
    """AC-7.14.6 & AC-7.14.8: PUT /settings updates KB settings."""
    pass
```

**Requirements**:
- [ ] Return default settings when KB has no custom settings
- [ ] Validate against KBSettings schema (chunk_size: 100-2000, temperature: 0-2.0, etc.)
- [ ] Create audit log entry on update (`action="settings_updated"`)
- [ ] Invalidate KBConfigResolver cache on update
- [ ] Check KB access permissions (GET: read, PUT: admin)
- [ ] Support partial updates (merge with existing settings)

#### 1.2 Add KBSettingsUpdate Schema
**File**: `backend/app/schemas/kb_settings.py`

```python
class KBSettingsUpdate(BaseModel):
    """Partial update schema for KB settings."""
    chunking: Optional[ChunkingConfigUpdate] = None
    retrieval: Optional[RetrievalConfigUpdate] = None
    generation: Optional[GenerationConfigUpdate] = None
```

### Phase 2: Frontend Hook (Priority: P0)

#### 2.1 Create useKBSettings Hook
**File**: `frontend/src/hooks/useKBSettings.ts`

```typescript
export function useKBSettings(kbId: string | undefined) {
  // Returns:
  return {
    settings: KBSettings | undefined,
    isLoading: boolean,
    isSuccess: boolean,
    isError: boolean,
    error: Error | undefined,
    updateSettings: (settings: KBSettings) => Promise<void>,
    isUpdating: boolean,
    updateError: Error | undefined,
  };
}
```

**Requirements**:
- [ ] GET query to `/api/v1/knowledge-bases/{id}/settings`
- [ ] PUT mutation to `/api/v1/knowledge-bases/{id}/settings`
- [ ] 5-minute stale time for caching
- [ ] Optimistic updates with rollback on failure
- [ ] Skip query when kbId is undefined

### Phase 3: Frontend Components (Priority: P0)

#### 3.1 ChunkingSection Component
**File**: `frontend/src/components/kb/settings/chunking-section.tsx`

**Required data-testid attributes**:
```
chunking-section
chunking-strategy-select
chunking-size-slider
chunking-size-value
chunking-overlap-slider
chunking-overlap-value
```

**Requirements**:
- [ ] Strategy dropdown: fixed, recursive, semantic
- [ ] Chunk Size slider: 100-2000, default 512
- [ ] Chunk Overlap slider: 0-500, default 50
- [ ] Display current values next to sliders
- [ ] Call onChange with updated config on any change

#### 3.2 RetrievalSection Component
**File**: `frontend/src/components/kb/settings/retrieval-section.tsx`

**Required data-testid attributes**:
```
retrieval-section
retrieval-top-k-slider
retrieval-top-k-value
retrieval-threshold-slider
retrieval-threshold-value
retrieval-method-select
retrieval-mmr-toggle
retrieval-mmr-lambda-slider
retrieval-mmr-lambda-value
```

**Requirements**:
- [ ] Top K slider: 1-100, default 10
- [ ] Similarity Threshold slider: 0.0-1.0, default 0.7
- [ ] Method dropdown: vector, hybrid, hyde
- [ ] MMR toggle switch
- [ ] MMR Lambda slider (0.0-1.0): only visible when MMR enabled
- [ ] Call onChange with updated config on any change

#### 3.3 GenerationSection Component
**File**: `frontend/src/components/kb/settings/generation-section.tsx`

**Required data-testid attributes**:
```
generation-section
generation-temperature-slider
generation-temperature-value
generation-top-p-slider
generation-top-p-value
generation-max-tokens-input
```

**Requirements**:
- [ ] Temperature slider: 0.0-2.0, step 0.1, default 0.7
- [ ] Top P slider: 0.0-1.0, step 0.05, default 0.9
- [ ] Max Tokens number input: 100-16000, default 2048
- [ ] Display validation errors when values out of range
- [ ] Call onChange with updated config on any change

#### 3.4 GeneralPanel Component
**File**: `frontend/src/components/kb/settings/general-panel.tsx`

**Required data-testid attributes**:
```
general-panel
general-panel-loading
reset-defaults-button
```

**Requirements**:
- [ ] Compose ChunkingSection, RetrievalSection, GenerationSection
- [ ] Pass settings and onChange handlers to children
- [ ] Reset to Defaults button with confirmation dialog
- [ ] Show loading state while fetching settings
- [ ] Disable all controls when `disabled` prop is true
- [ ] Display validation errors from `errors` prop

### Phase 4: Settings Modal Integration (Priority: P1)

#### 4.1 Update KbSettingsModal
**File**: `frontend/src/components/kb/kb-settings-modal.tsx`

**Required data-testid attributes**:
```
kb-settings-modal
kb-settings-tabs
kb-settings-tab-general
kb-settings-tab-models
kb-settings-save-button
kb-settings-save-spinner
kb-settings-save-success
```

**Requirements**:
- [ ] Add Tabs component with "General" and "Models" tabs
- [ ] Integrate GeneralPanel in "General" tab
- [ ] Keep existing model configuration in "Models" tab
- [ ] Save button with loading spinner during save
- [ ] Success toast/indicator on successful save
- [ ] Disable save when no changes or validation errors

## Default Values Reference

From `backend/app/schemas/kb_settings.py`:

```python
# Chunking
strategy: "recursive"
chunk_size: 512  # Range: 100-2000
chunk_overlap: 50  # Range: 0-500

# Retrieval
top_k: 10  # Range: 1-100
similarity_threshold: 0.7  # Range: 0.0-1.0
method: "vector"  # Enum: vector, hybrid, hyde
mmr_enabled: False
mmr_lambda: 0.5  # Range: 0.0-1.0

# Generation
temperature: 0.7  # Range: 0.0-2.0
top_p: 0.9  # Range: 0.0-1.0
top_k: 40  # Range: 1-100
max_tokens: 2048  # Range: 100-16000
frequency_penalty: 0.0  # Range: 0.0-2.0
presence_penalty: 0.0  # Range: 0.0-2.0
```

## Validation Rules

| Field | Type | Min | Max | Default |
|-------|------|-----|-----|---------|
| chunk_size | int | 100 | 2000 | 512 |
| chunk_overlap | int | 0 | 500 | 50 |
| top_k (retrieval) | int | 1 | 100 | 10 |
| similarity_threshold | float | 0.0 | 1.0 | 0.7 |
| mmr_lambda | float | 0.0 | 1.0 | 0.5 |
| temperature | float | 0.0 | 2.0 | 0.7 |
| top_p | float | 0.0 | 1.0 | 0.9 |
| top_k (generation) | int | 1 | 100 | 40 |
| max_tokens | int | 100 | 16000 | 2048 |

## Implementation Order

1. **Backend API** (enables all other tests)
   - Add GET/PUT endpoints to knowledge_bases.py
   - Add audit logging
   - Add cache invalidation

2. **Frontend Hook** (enables component tests)
   - Create useKBSettings.ts
   - Implement query and mutation

3. **Section Components** (can be parallel)
   - ChunkingSection
   - RetrievalSection
   - GenerationSection

4. **GeneralPanel** (depends on sections)
   - Compose sections
   - Add reset functionality

5. **Modal Integration** (final step)
   - Add tabs to kb-settings-modal.tsx
   - Wire up save functionality

## Running Tests

```bash
# Backend tests
cd backend
.venv/bin/pytest tests/integration/test_kb_settings_api.py -v

# Frontend unit/component tests
cd frontend
npm run test:run -- src/components/kb/settings/__tests__/
npm run test:run -- src/hooks/__tests__/useKBSettings.test.ts

# E2E tests
cd frontend
npx playwright test e2e/tests/kb/kb-settings-general.spec.ts
```

## Definition of Done

- [ ] All 18 backend integration tests pass
- [ ] All 11 hook tests pass
- [ ] All 36 component tests pass
- [ ] All 14 E2E tests pass
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Code reviewed and approved
- [ ] Documentation updated if needed
