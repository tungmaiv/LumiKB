/**
 * Unit tests for useKBActions hook
 * Story 7-26: KB Archive/Delete/Restore UI (AC-7.26.1-5)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useKBActions } from '../useKBActions';

// Mock kb-store
const mockFetchKbs = vi.fn();
const mockSetActiveKb = vi.fn();

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: () => ({
    fetchKbs: mockFetchKbs,
    activeKb: null,
    setActiveKb: mockSetActiveKb,
  }),
}));

// Mock API functions
const mockArchiveKB = vi.fn();
const mockRestoreKB = vi.fn();
const mockDeleteKB = vi.fn();

vi.mock('@/lib/api/knowledge-bases', () => ({
  archiveKnowledgeBase: (...args: unknown[]) => mockArchiveKB(...args),
  restoreKnowledgeBase: (...args: unknown[]) => mockRestoreKB(...args),
  deleteKnowledgeBase: (...args: unknown[]) => mockDeleteKB(...args),
}));

// Mock toast
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();

vi.mock('sonner', () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

// Mock ApiError
vi.mock('@/lib/api/client', () => ({
  ApiError: class ApiError extends Error {
    detail?: string;
    constructor(message: string, detail?: string) {
      super(message);
      this.detail = detail;
    }
  },
}));

describe('useKBActions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchKbs.mockResolvedValue(undefined);
  });

  describe('archive', () => {
    it('[P0] calls archiveKnowledgeBase API with correct id', async () => {
      mockArchiveKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.archive('kb-1', 'Test KB');
      });

      expect(mockArchiveKB).toHaveBeenCalledWith('kb-1');
    });

    it('[P0] shows success toast on successful archive', async () => {
      mockArchiveKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.archive('kb-1', 'Test KB');
      });

      expect(mockToastSuccess).toHaveBeenCalledWith('"Test KB" has been archived');
    });

    it('[P0] refreshes KB list after successful archive', async () => {
      mockArchiveKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.archive('kb-1', 'Test KB');
      });

      expect(mockFetchKbs).toHaveBeenCalled();
    });

    it('[P0] returns true on successful archive', async () => {
      mockArchiveKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.archive('kb-1', 'Test KB');
      });

      expect(success).toBe(true);
    });

    it('[P1] shows error toast on archive failure', async () => {
      mockArchiveKB.mockRejectedValueOnce(new Error('Archive failed'));

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.archive('kb-1', 'Test KB');
      });

      expect(mockToastError).toHaveBeenCalled();
    });

    it('[P1] returns false on archive failure', async () => {
      mockArchiveKB.mockRejectedValueOnce(new Error('Archive failed'));

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.archive('kb-1', 'Test KB');
      });

      expect(success).toBe(false);
    });

    it('[P1] sets isArchiving to true while archiving', async () => {
      let resolveArchive: (value: unknown) => void;
      mockArchiveKB.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveArchive = resolve;
          })
      );

      const { result } = renderHook(() => useKBActions());

      expect(result.current.isArchiving).toBe(false);

      act(() => {
        result.current.archive('kb-1', 'Test KB');
      });

      await waitFor(() => {
        expect(result.current.isArchiving).toBe(true);
      });

      await act(async () => {
        resolveArchive!({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });
      });

      await waitFor(() => {
        expect(result.current.isArchiving).toBe(false);
      });
    });
  });

  describe('restore', () => {
    it('[P0] calls restoreKnowledgeBase API with correct id', async () => {
      mockRestoreKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: null });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.restore('kb-1', 'Test KB');
      });

      expect(mockRestoreKB).toHaveBeenCalledWith('kb-1');
    });

    it('[P0] shows success toast on successful restore', async () => {
      mockRestoreKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: null });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.restore('kb-1', 'Test KB');
      });

      expect(mockToastSuccess).toHaveBeenCalledWith('"Test KB" has been restored');
    });

    it('[P0] refreshes KB list after successful restore', async () => {
      mockRestoreKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: null });

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.restore('kb-1', 'Test KB');
      });

      expect(mockFetchKbs).toHaveBeenCalled();
    });

    it('[P0] returns true on successful restore', async () => {
      mockRestoreKB.mockResolvedValueOnce({ id: 'kb-1', archived_at: null });

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.restore('kb-1', 'Test KB');
      });

      expect(success).toBe(true);
    });

    it('[P1] shows error toast on restore failure', async () => {
      mockRestoreKB.mockRejectedValueOnce(new Error('Restore failed'));

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.restore('kb-1', 'Test KB');
      });

      expect(mockToastError).toHaveBeenCalled();
    });

    it('[P1] returns false on restore failure', async () => {
      mockRestoreKB.mockRejectedValueOnce(new Error('Restore failed'));

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.restore('kb-1', 'Test KB');
      });

      expect(success).toBe(false);
    });

    it('[P1] sets isRestoring to true while restoring', async () => {
      let resolveRestore: (value: unknown) => void;
      mockRestoreKB.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveRestore = resolve;
          })
      );

      const { result } = renderHook(() => useKBActions());

      expect(result.current.isRestoring).toBe(false);

      act(() => {
        result.current.restore('kb-1', 'Test KB');
      });

      await waitFor(() => {
        expect(result.current.isRestoring).toBe(true);
      });

      await act(async () => {
        resolveRestore!({ id: 'kb-1', archived_at: null });
      });

      await waitFor(() => {
        expect(result.current.isRestoring).toBe(false);
      });
    });
  });

  describe('remove', () => {
    it('[P0] calls deleteKnowledgeBase API with correct id', async () => {
      mockDeleteKB.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.remove('kb-1', 'Test KB');
      });

      expect(mockDeleteKB).toHaveBeenCalledWith('kb-1');
    });

    it('[P0] shows success toast on successful delete', async () => {
      mockDeleteKB.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.remove('kb-1', 'Test KB');
      });

      expect(mockToastSuccess).toHaveBeenCalledWith('"Test KB" has been permanently deleted');
    });

    it('[P0] refreshes KB list after successful delete', async () => {
      mockDeleteKB.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.remove('kb-1', 'Test KB');
      });

      expect(mockFetchKbs).toHaveBeenCalled();
    });

    it('[P0] returns true on successful delete', async () => {
      mockDeleteKB.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.remove('kb-1', 'Test KB');
      });

      expect(success).toBe(true);
    });

    it('[P1] shows error toast on delete failure', async () => {
      mockDeleteKB.mockRejectedValueOnce(new Error('Delete failed'));

      const { result } = renderHook(() => useKBActions());

      await act(async () => {
        await result.current.remove('kb-1', 'Test KB');
      });

      expect(mockToastError).toHaveBeenCalled();
    });

    it('[P1] returns false on delete failure', async () => {
      mockDeleteKB.mockRejectedValueOnce(new Error('Delete failed'));

      const { result } = renderHook(() => useKBActions());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.remove('kb-1', 'Test KB');
      });

      expect(success).toBe(false);
    });

    it('[P1] sets isDeleting to true while deleting', async () => {
      let resolveDelete: (value: unknown) => void;
      mockDeleteKB.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveDelete = resolve;
          })
      );

      const { result } = renderHook(() => useKBActions());

      expect(result.current.isDeleting).toBe(false);

      act(() => {
        result.current.remove('kb-1', 'Test KB');
      });

      await waitFor(() => {
        expect(result.current.isDeleting).toBe(true);
      });

      await act(async () => {
        resolveDelete!(undefined);
      });

      await waitFor(() => {
        expect(result.current.isDeleting).toBe(false);
      });
    });
  });

  describe('isPending', () => {
    it('[P1] isPending is true when any action is in progress', async () => {
      let resolveArchive: (value: unknown) => void;
      mockArchiveKB.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveArchive = resolve;
          })
      );

      const { result } = renderHook(() => useKBActions());

      expect(result.current.isPending).toBe(false);

      act(() => {
        result.current.archive('kb-1', 'Test KB');
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });

      await act(async () => {
        resolveArchive!({ id: 'kb-1', archived_at: '2025-01-15T00:00:00Z' });
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });
  });
});
