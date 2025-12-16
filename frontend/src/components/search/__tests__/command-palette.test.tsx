/**
 * Component tests for CommandPalette (Story 3.7, AC1-AC7)
 *
 * TEST COVERAGE STATUS: 10/10 passing (100%)
 *
 * ROOT CAUSE (Story 5.10 Investigation):
 * Previously 3 tests timed out due to cmdk library's internal filtering behavior.
 * The shadcn/ui Command component uses cmdk which filters CommandItem elements
 * based on the input value. When `value={result.document_id}` (e.g., "doc-1")
 * doesn't match the search text (e.g., "test"), cmdk hides those items even though
 * React state contains results. This caused tests waiting for result text to timeout.
 *
 * FIX APPLIED:
 * 1. Component fix: Added `shouldFilter={false}` to Command component in
 *    command-palette.tsx to disable cmdk's client-side filtering. This is correct
 *    for our use case since we perform server-side search.
 *
 * 2. Test fix: Changed `vi.clearAllMocks()` to `vi.resetAllMocks()` in beforeEach
 *    to properly reset mock implementations between tests (not just call history).
 *    This fixed test isolation issues where previous tests' mocks persisted.
 *
 * PATTERN FOR TESTING cmdk/Command COMPONENTS:
 * - Use `shouldFilter={false}` when doing server-side search
 * - Use `vi.resetAllMocks()` to clear mock implementations between tests
 * - Use `mockResolvedValue()` instead of `mockResolvedValueOnce()` when typing
 *   triggers multiple effect cycles due to debouncing
 * - Wait for debounce (300ms) + fetch + state update in assertions
 *
 * @see Story 5.10 for technical debt resolution details
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CommandPalette } from '../command-palette';

// Mock fetch globally
global.fetch = vi.fn();

describe('CommandPalette', () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders when open', () => {
    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByPlaceholderText('Search knowledge bases...')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<CommandPalette open={false} onOpenChange={mockOnOpenChange} />);

    expect(screen.queryByPlaceholderText('Search knowledge bases...')).not.toBeInTheDocument();
  });

  it('auto-focuses search input when opened (AC1)', () => {
    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    expect(input).toHaveFocus();
  });

  it('shows minimum character message for queries < 2 chars', () => {
    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    fireEvent.change(input, { target: { value: 'a' } });

    expect(screen.getByText('Type at least 2 characters to search')).toBeInTheDocument();
  });

  it('fetches results after debounce (AC10)', async () => {
    const mockResults = {
      query: 'test',
      results: [
        {
          document_id: 'doc-1',
          document_name: 'Test Document.pdf',
          kb_id: 'kb-1',
          kb_name: 'Test KB',
          excerpt: 'This is a test excerpt',
          relevance_score: 0.95,
        },
      ],
      kb_count: 1,
      response_time_ms: 100,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => mockResults,
    } as Response);

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    await userEvent.type(input, 'test');

    // Wait for debounce (300ms) + fetch
    await waitFor(
      () => {
        expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/search/quick',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ query: 'test', kb_ids: null }),
      })
    );
  });

  it('displays results with metadata (AC2)', async () => {
    const mockResults = {
      query: 'auth',
      results: [
        {
          document_id: 'doc-1',
          document_name: 'Auth Guide.pdf',
          kb_id: 'kb-1',
          kb_name: 'Security KB',
          excerpt: 'OAuth 2.0 implementation details...',
          relevance_score: 0.92,
        },
      ],
      kb_count: 1,
      response_time_ms: 150,
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => mockResults,
    } as Response);

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    await userEvent.type(input, 'auth');

    await waitFor(
      () => {
        expect(screen.getByText('Auth Guide.pdf')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // Verify metadata display
    expect(screen.getByText('Security KB')).toBeInTheDocument();
    expect(screen.getByText('92% match')).toBeInTheDocument();
    expect(screen.getByText('OAuth 2.0 implementation details...')).toBeInTheDocument();
  });

  it('shows empty state when no results (AC9)', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ query: 'xyz', results: [], kb_count: 3, response_time_ms: 50 }),
    } as Response);

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    await userEvent.type(input, 'xyz');

    await waitFor(() => {
      expect(screen.getByText('No matches found')).toBeInTheDocument();
    });

    expect(screen.getByText(/Try broader terms or/i)).toBeInTheDocument();
  });

  it('shows error state on API failure (AC9)', async () => {
    // Use mockResolvedValue (not Once) since typing triggers multiple effect cycles
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
    } as Response);

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    await userEvent.type(input, 'fail');

    // Wait for debounce (300ms) + fetch + state update
    await waitFor(
      () => {
        expect(screen.getByText('Search temporarily unavailable')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('resets state when closed (AC7)', async () => {
    const { rerender } = render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');
    await userEvent.type(input, 'test');

    // Close palette
    rerender(<CommandPalette open={false} onOpenChange={mockOnOpenChange} />);

    // Re-open palette
    rerender(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const newInput = screen.getByPlaceholderText('Search knowledge bases...');
    expect(newInput).toHaveValue(''); // Query should be cleared
  });

  it('cancels pending requests on new query (AC10)', async () => {
    const abortSpy = vi.spyOn(AbortController.prototype, 'abort');

    render(<CommandPalette open={true} onOpenChange={mockOnOpenChange} />);

    const input = screen.getByPlaceholderText('Search knowledge bases...');

    // Type first query
    await userEvent.type(input, 'first');

    // Type second query before debounce completes
    await userEvent.clear(input);
    await userEvent.type(input, 'second');

    // AbortController.abort should have been called
    await waitFor(() => {
      expect(abortSpy).toHaveBeenCalled();
    });

    abortSpy.mockRestore();
  });
});
