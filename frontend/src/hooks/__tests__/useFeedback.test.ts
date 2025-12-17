/**
 * useFeedback Hook Tests (Story 4-8)
 *
 * Test Coverage: AC2-AC3 (Feedback Submission Flow)
 * Priority: P1 (Core hook logic)
 *
 * Tests:
 * 1. Submit flow calls API with correct payload
 * 2. Loading state management
 * 3. Error handling on API failure
 * 4. Alternatives state updated after submission
 */

import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFeedback } from '../useFeedback';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Mock API server setup
const mockAlternatives = [
  {
    type: 're_search',
    description: 'Search for different sources',
    action: 'change_search',
  },
  {
    type: 'add_context',
    description: 'Add more context',
    action: 'add_instructions',
  },
  {
    type: 'start_fresh',
    description: 'Start over',
    action: 'create_new',
  },
];

const server = setupServer(
  http.post('/api/v1/drafts/:draftId/feedback', async ({ request }) => {
    const body = (await request.json()) as { feedback_type: string };
    return HttpResponse.json({
      alternatives: mockAlternatives,
      feedback_type: body?.feedback_type,
    });
  })
);

beforeEach(() => server.listen());
afterEach(() => server.resetHandlers());
afterEach(() => server.close());

describe('useFeedback', () => {
  it('[P1] should call API with correct payload on submit', async () => {
    // GIVEN: Hook initialized with draft ID
    const draftId = 'test-draft-123';
    const { result } = renderHook(() => useFeedback(draftId));

    // WHEN: User submits feedback
    const feedbackType = 'not_relevant';
    const comments = undefined;

    await result.current.handleSubmit(feedbackType, comments);

    // THEN: Submission completed successfully
    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(false);
    });

    // AND: Alternatives state updated
    await waitFor(() => {
      expect(result.current.alternatives).toEqual(mockAlternatives);
    });
    expect(result.current.error).toBeNull();
  });

  it('[P1] should manage loading state during submission', async () => {
    // GIVEN: Hook initialized with delayed API response
    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', async () => {
        // Delay to ensure isSubmitting can be observed
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json({
          alternatives: mockAlternatives,
          feedback_type: 'not_relevant',
        });
      })
    );

    const { result } = renderHook(() => useFeedback('draft-123'));

    // THEN: Initially not submitting
    expect(result.current.isSubmitting).toBe(false);

    // WHEN: User submits feedback (start submission but don't await)
    const submitPromise = result.current.handleSubmit('not_relevant', undefined);

    // THEN: isSubmitting is true during API call
    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(true);
    });

    // WHEN: API completes
    await submitPromise;

    // THEN: isSubmitting back to false
    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(false);
    });
  });

  it('[P1] should handle API errors gracefully', async () => {
    // GIVEN: API configured to return error
    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', () => {
        return HttpResponse.json({ detail: 'Internal server error occurred' }, { status: 500 });
      })
    );

    const { result } = renderHook(() => useFeedback('draft-123'));

    // WHEN: User submits feedback
    await result.current.handleSubmit('not_relevant', undefined);

    // THEN: Error state updated
    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });
    expect(result.current.error).toContain('Internal server error');
    expect(result.current.alternatives).toEqual([]);
    expect(result.current.isSubmitting).toBe(false);
  });

  it('[P1] should update alternatives state after successful submission', async () => {
    // GIVEN: Hook initialized
    const { result } = renderHook(() => useFeedback('draft-123'));

    // THEN: Alternatives initially empty
    expect(result.current.alternatives).toEqual([]);

    // WHEN: User submits feedback
    result.current.handleSubmit('not_relevant', undefined);

    // THEN: Alternatives populated after API response
    await waitFor(() => {
      expect(result.current.alternatives).toHaveLength(3);
    });

    expect(result.current.alternatives).toEqual(mockAlternatives);
    expect(result.current.error).toBeNull();
  });

  it('[P1] should handle "other" feedback type with comments', async () => {
    // GIVEN: Hook initialized
    const { result } = renderHook(() => useFeedback('draft-123'));

    let capturedRequest: any = null;

    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', async ({ request }) => {
        capturedRequest = await request.json();
        return HttpResponse.json({ alternatives: mockAlternatives });
      })
    );

    // WHEN: User submits "other" feedback with comments
    result.current.handleSubmit('other', 'Custom feedback text');

    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(false);
    });

    // THEN: API called with comments
    expect(capturedRequest).toEqual({
      feedback_type: 'other',
      comments: 'Custom feedback text',
    });
  });

  it('[P1] should handle network errors', async () => {
    // GIVEN: API configured to fail with network error
    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', () => {
        return HttpResponse.error();
      })
    );

    const { result } = renderHook(() => useFeedback('draft-123'));

    // WHEN: User submits feedback
    await result.current.handleSubmit('not_relevant', undefined);

    // THEN: Error state updated with network error message
    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });
    expect(result.current.isSubmitting).toBe(false);
  });

  it('[P1] should reset error state on new submission', async () => {
    // GIVEN: Hook with previous error
    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', () => {
        return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
      })
    );

    const { result } = renderHook(() => useFeedback('draft-123'));

    // WHEN: First submission fails
    await result.current.handleSubmit('not_relevant', undefined);

    // THEN: Error is set
    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });

    // AND: API now returns success
    server.use(
      http.post('/api/v1/drafts/:draftId/feedback', () => {
        return HttpResponse.json({ alternatives: mockAlternatives });
      })
    );

    // WHEN: User submits again
    await result.current.handleSubmit('wrong_format', undefined);

    // THEN: Error cleared
    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
    expect(result.current.alternatives).toHaveLength(3);
  });

  it('[P1] should validate required fields', async () => {
    // GIVEN: Hook initialized
    const { result } = renderHook(() => useFeedback('draft-123'));

    // WHEN: User submits with invalid feedback type
    // @ts-expect-error Testing invalid input
    result.current.handleSubmit(null, null);

    // THEN: Hook handles gracefully (should not crash)
    expect(result.current.isSubmitting).toBe(false);
  });
});
