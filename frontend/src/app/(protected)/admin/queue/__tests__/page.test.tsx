/**
 * Redirect Test: /admin/queue -> /operations/queue
 * Story 7.11: Navigation Restructure
 *
 * This test verifies the backwards compatibility redirect.
 * The actual queue status page tests are in /operations/queue/__tests__/
 */

import { describe, it, expect, vi } from 'vitest';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}));

import { redirect } from 'next/navigation';
import AdminQueueRedirectPage from '../page';

describe('AdminQueueRedirectPage (Story 7-11)', () => {
  it('[P0] should redirect to /operations/queue', () => {
    // Call the page component - it should call redirect
    AdminQueueRedirectPage();

    // Verify redirect was called with correct path
    expect(redirect).toHaveBeenCalledWith('/operations/queue');
  });
});
