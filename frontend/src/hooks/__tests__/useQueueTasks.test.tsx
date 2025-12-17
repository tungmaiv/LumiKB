/**
 * Unit tests for useQueueTasks hook
 * Story 5-4: Processing Queue Status
 *
 * Tests task list fetching (active and pending tasks) for queue monitoring.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, type Mock } from 'vitest';
import { ReactNode } from 'react';
import { useQueueTasks } from '../useQueueTasks';

// Mock fetch
global.fetch = vi.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useQueueTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('[P1] should fetch active tasks successfully - AC-5.4.3', async () => {
    // Arrange
    const mockTasks = [
      {
        task_id: 'task-1',
        task_name: 'process_document',
        status: 'STARTED',
        started_at: new Date().toISOString(),
        estimated_duration: 3500,
      },
      {
        task_id: 'task-2',
        task_name: 'generate_embeddings',
        status: 'STARTED',
        started_at: new Date().toISOString(),
        estimated_duration: 5000,
      },
    ];

    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockTasks,
    });

    // Act
    const { result } = renderHook(() => useQueueTasks('document_processing', 'PROCESSING'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockTasks);
    expect(result.current.data).toHaveLength(2);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/admin/queue/document_processing/tasks?document_status=PROCESSING',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P1] should fetch pending tasks successfully - AC-5.4.3', async () => {
    // Arrange
    const mockPendingTasks = [
      {
        task_id: 'task-3',
        task_name: 'process_document',
        status: 'PENDING',
        started_at: null,
        estimated_duration: null,
      },
      {
        task_id: 'task-4',
        task_name: 'export_document',
        status: 'PENDING',
        started_at: null,
        estimated_duration: null,
      },
    ];

    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPendingTasks,
    });

    // Act
    const { result } = renderHook(() => useQueueTasks('document_processing', 'PENDING'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockPendingTasks);
    expect(result.current.data).toHaveLength(2);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/admin/queue/document_processing/tasks?document_status=PENDING',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P1] should handle 403 Forbidden error - AC-5.4.6', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Admin access required' }),
    });

    // Act
    const { result } = renderHook(() => useQueueTasks('document_processing', 'PROCESSING'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('[P2] should handle network errors', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockRejectedValueOnce(new Error('Network error'));

    // Act
    const { result } = renderHook(() => useQueueTasks('document_processing', 'PROCESSING'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });
});
