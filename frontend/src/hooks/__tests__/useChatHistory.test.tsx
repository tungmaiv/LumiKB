/**
 * Chat History Hooks Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 * AC9: Pagination for long histories
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import {
  useChatSessions,
  useChatMessages,
  useChatHistorySearch,
} from '../useChatHistory';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useChatSessions', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches chat sessions successfully', async () => {
    const mockData = {
      items: [
        {
          session_id: 'session-1',
          user_id: 'user-1',
          user_name: 'alice@example.com',
          kb_id: 'kb-1',
          kb_name: 'Tech Docs',
          message_count: 10,
          last_message_at: '2024-01-15T10:00:00Z',
          first_message_at: '2024-01-15T09:00:00Z',
        },
      ],
      total: 1,
      skip: 0,
      limit: 20,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(() => useChatSessions({}), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/observability/chat-sessions')
    );
  });

  it('applies filters to the request', async () => {
    const mockData = { items: [], total: 0, skip: 0, limit: 20 };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    renderHook(
      () =>
        useChatSessions({
          userId: 'user-123',
          kbId: 'kb-456',
          searchQuery: 'test query',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain('user_id=user-123');
    expect(url).toContain('kb_id=kb-456');
    expect(url).toContain('search_query=test+query');
  });

  it('handles fetch errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    const { result } = renderHook(() => useChatSessions({}), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
  });
});

describe('useChatMessages', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('does not fetch when sessionId is null', () => {
    renderHook(() => useChatMessages(null), {
      wrapper: createWrapper(),
    });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('fetches messages when sessionId is provided', async () => {
    const mockData = {
      items: [
        {
          id: 'msg-1',
          trace_id: 'trace-1',
          session_id: 'session-123',
          role: 'user',
          content: 'Hello',
          user_id: 'user-1',
          kb_id: 'kb-1',
          created_at: '2024-01-15T10:00:00Z',
          token_count: null,
          response_time_ms: null,
          citations: null,
        },
      ],
      total: 1,
      skip: 0,
      limit: 50,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(() => useChatMessages('session-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/observability/chat-history')
    );
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('session_id=session-123')
    );
  });

  it('supports pagination via getNextPageParam', async () => {
    const page1 = {
      items: Array.from({ length: 50 }, (_, i) => ({
        id: `msg-${i}`,
        trace_id: `trace-${i}`,
        session_id: 'session-123',
        role: 'user' as const,
        content: `Message ${i}`,
        user_id: 'user-1',
        kb_id: 'kb-1',
        created_at: '2024-01-15T10:00:00Z',
        token_count: null,
        response_time_ms: null,
        citations: null,
      })),
      total: 100,
      skip: 0,
      limit: 50,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(page1),
    });

    const { result } = renderHook(() => useChatMessages('session-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // hasNextPage should be true since total > skip + limit
    expect(result.current.hasNextPage).toBe(true);
  });
});

describe('useChatHistorySearch', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('does not fetch when filters are empty', () => {
    renderHook(() => useChatHistorySearch({}), {
      wrapper: createWrapper(),
    });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('fetches when filters are provided', async () => {
    const mockData = { items: [], total: 0, skip: 0, limit: 100 };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(
      () => useChatHistorySearch({ searchQuery: 'test' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalled();
  });

  it('applies date range filters', async () => {
    const mockData = { items: [], total: 0, skip: 0, limit: 100 };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    renderHook(
      () =>
        useChatHistorySearch({
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain('start_date=2024-01-01');
    expect(url).toContain('end_date=2024-01-31');
  });
});
