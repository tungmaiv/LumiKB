# Story 7-20: Feedback Button Integration

| Field | Value |
|-------|-------|
| **Story ID** | 7-20 |
| **Epic** | Epic 7 - Tech Debt Sprint (Pre-Epic 8) |
| **Priority** | MEDIUM |
| **Effort** | 4 hours |
| **Resolves** | TD-4.8-1 |
| **Status** | Done |
| **Context** | [7-20-feedback-button-integration.context.xml](7-20-feedback-button-integration.context.xml) |

## User Story

**As a** document author
**I want** to provide feedback on generated drafts directly from the editor
**So that** I can report quality issues and help improve the generation system

## Background

Story 4-8 (Generation Feedback & Recovery) created the `FeedbackModal` and `RecoveryModal` components, but the integration with `DraftEditor` was deferred. The feedback button exists but isn't wired up. This story completes that integration.

## Acceptance Criteria

### AC-7.20.1: Feedback Button Visible in DraftEditor
- **Given** a user is viewing a generated draft in the editor
- **When** the draft has completed generation
- **Then** a "Provide Feedback" button is visible in the editor toolbar

### AC-7.20.2: FeedbackModal Opens on Click
- **Given** the feedback button is visible
- **When** the user clicks it
- **Then** the FeedbackModal opens
- **And** it's pre-populated with the current draft_id

### AC-7.20.3: Feedback Submission Flow
- **Given** the FeedbackModal is open
- **When** the user selects a feedback type and submits
- **Then** feedback is sent to the API via `useFeedback` hook
- **And** a success toast is shown
- **And** the modal closes

### AC-7.20.4: Recovery Modal Trigger
- **Given** the user provides negative feedback (type: "poor_quality" or "incorrect")
- **When** feedback is submitted
- **Then** RecoveryModal is shown offering regeneration options

### AC-7.20.5: Button State Management
- **Given** the draft is still generating (streaming)
- **When** the editor is displayed
- **Then** the feedback button is disabled with tooltip "Wait for generation to complete"

### AC-7.20.6: Unit Test Coverage
- **Given** the implementation is complete
- **When** unit tests run
- **Then** feedback integration has ≥80% coverage

## Tasks

### Task 1: Add Feedback Button to DraftEditor
- [x] 1.1 Add "Provide Feedback" button to DraftEditor toolbar
- [x] 1.2 Style consistently with existing toolbar buttons
- [x] 1.3 Add disabled state during streaming
- [x] 1.4 Add tooltip for disabled state

### Task 2: Wire FeedbackModal
- [x] 2.1 Import FeedbackModal into DraftEditor
- [x] 2.2 Add state for modal visibility
- [x] 2.3 Pass draft_id to modal on open
- [x] 2.4 Handle modal close callback

### Task 3: Integrate RecoveryModal
- [x] 3.1 Add RecoveryModal import
- [x] 3.2 Show RecoveryModal on negative feedback submission
- [x] 3.3 Handle regeneration request from RecoveryModal
- [x] 3.4 Pass context (draft content, prompt) to regeneration

### Task 4: Toast Notifications
- [x] 4.1 Add success toast on feedback submission (via RecoveryModal flow)
- [x] 4.2 Add error toast on submission failure (handled by useFeedback hook)

### Task 5: Testing
- [x] 5.1 Unit test feedback button visibility
- [x] 5.2 Unit test modal open/close flow
- [x] 5.3 Unit test disabled state during streaming
- [x] 5.4 Unit test recovery modal trigger

## Dev Notes

### Implementation Pattern
```tsx
// In DraftEditor.tsx
import { FeedbackModal } from '@/components/generation/feedback-modal';
import { RecoveryModal } from '@/components/generation/recovery-modal';
import { useFeedback } from '@/hooks/useFeedback';

export function DraftEditor({ draftId, isStreaming, content }: Props) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [showRecovery, setShowRecovery] = useState(false);
  const { submitFeedback, isSubmitting } = useFeedback();

  const handleFeedbackSubmit = async (type: FeedbackType, comment?: string) => {
    await submitFeedback({ draftId, type, comment });
    setShowFeedback(false);

    if (type === 'poor_quality' || type === 'incorrect') {
      setShowRecovery(true);
    } else {
      toast.success('Thank you for your feedback!');
    }
  };

  return (
    <>
      <Toolbar>
        <Button
          onClick={() => setShowFeedback(true)}
          disabled={isStreaming}
          title={isStreaming ? 'Wait for generation to complete' : 'Provide Feedback'}
        >
          Provide Feedback
        </Button>
      </Toolbar>

      <FeedbackModal
        open={showFeedback}
        onClose={() => setShowFeedback(false)}
        onSubmit={handleFeedbackSubmit}
        draftId={draftId}
      />

      <RecoveryModal
        open={showRecovery}
        onClose={() => setShowRecovery(false)}
        draftContent={content}
        onRegenerate={handleRegenerate}
      />
    </>
  );
}
```

### Key Files
- `frontend/src/components/generation/draft-editor.tsx` - Add button and modals
- `frontend/src/components/generation/feedback-modal.tsx` - Existing component
- `frontend/src/components/generation/recovery-modal.tsx` - Existing component
- `frontend/src/hooks/useFeedback.ts` - Existing hook

### Dependencies
- FeedbackModal (Story 4-8) - COMPLETED
- RecoveryModal (Story 4-8) - COMPLETED
- useFeedback hook (Story 4-8) - COMPLETED

## Testing Strategy

### Unit Tests
- Mock useFeedback hook
- Test button renders when draft complete
- Test button disabled during streaming
- Test modal opens on click
- Test recovery modal on negative feedback

### E2E Tests (optional)
- Full feedback submission flow

## Definition of Done
- [x] All ACs pass
- [x] Unit tests ≥80% coverage on modified files (7 tests passing)
- [x] No eslint errors
- [x] Code reviewed

## Completion Notes

### Implementation Summary (2025-12-10)

**Files Modified:**
- `frontend/src/components/generation/draft-editor.tsx` - Added feedback button and modal wiring

**Files Created:**
- `frontend/src/components/generation/__tests__/draft-editor-feedback.test.tsx` - 7 unit tests

**Key Changes:**
1. Added `isStreaming` and `onRecoveryAction` props to DraftEditor
2. Imported and wired FeedbackModal and RecoveryModal
3. Added useFeedback hook integration
4. Feedback button with tooltip when disabled during streaming
5. Recovery flow triggers on feedback submission with alternatives

**Test Results:**
- 7/7 tests passing
- No ESLint errors on modified files
- TypeScript type checks pass
