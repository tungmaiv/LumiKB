/**
 * Unit tests for useUsers hook
 * Story 5.18: User Management UI
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUsers } from '../useUsers';
import type { PaginatedResponse, UserRead, PermissionLevel } from '@/types/user';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockUser: UserRead = {
  id: 'user-1',
  email: 'test@example.com',
  is_active: true,
  is_superuser: false,
  is_verified: true,
  permission_level: 1 as PermissionLevel, // User
  created_at: '2025-01-01T00:00:00Z',
  onboarding_completed: true,
  last_active: '2025-01-02T00:00:00Z',
};

const mockPaginatedResponse: PaginatedResponse<UserRead> = {
  data: [mockUser],
  meta: {
    total: 1,
    page: 1,
    per_page: 20,
    total_pages: 1,
  },
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  function TestWrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }
  TestWrapper.displayName = 'TestWrapper';
  return TestWrapper;
}

describe('useUsers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetching users', () => {
    it('fetches users successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.users).toEqual([mockUser]);
      expect(result.current.pagination).toEqual(mockPaginatedResponse.meta);
      expect(result.current.error).toBeNull();
    });

    it('calculates skip parameter from page', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      renderHook(() => useUsers({ page: 3, pageSize: 20 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      // Page 3, pageSize 20 -> skip = (3-1) * 20 = 40
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('skip=40'),
        expect.any(Object)
      );
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=20'),
        expect.any(Object)
      );
    });

  });

  describe('createUser', () => {
    it('creates user successfully', async () => {
      // First fetch for initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const newUser = { ...mockUser, id: 'user-2', email: 'new@example.com' };

      // Mock create user response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(newUser),
      });

      // Mock refetch after invalidation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockPaginatedResponse,
            data: [mockUser, newUser],
          }),
      });

      await act(async () => {
        const created = await result.current.createUser({
          email: 'new@example.com',
          password: 'password123',
          is_superuser: false,
        });
        expect(created.email).toBe('new@example.com');
      });
    });

    it('handles 409 conflict error for duplicate email', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        statusText: 'Conflict',
      });

      await expect(
        act(async () => {
          await result.current.createUser({
            email: 'existing@example.com',
            password: 'password123',
          });
        })
      ).rejects.toThrow('Email already exists');
    });
  });

  describe('updateUser', () => {
    it('updates user with optimistic update', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.users).toHaveLength(1);
      });

      const updatedUser = { ...mockUser, is_active: false };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedUser),
      });

      // Mock refetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockPaginatedResponse,
            data: [updatedUser],
          }),
      });

      await act(async () => {
        await result.current.updateUser('user-1', { is_active: false });
      });

      // After optimistic update, user should be inactive
      await waitFor(() => {
        expect(result.current.users[0]?.is_active).toBe(false);
      });
    });

    it('rolls back on update error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.users).toHaveLength(1);
      });

      // Verify initial state
      expect(result.current.users[0]?.is_active).toBe(true);

      // Mock failed update
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      // Mock refetch (returns original data)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      await expect(
        act(async () => {
          await result.current.updateUser('user-1', { is_active: false });
        })
      ).rejects.toThrow();

      // After rollback, user should be active again
      await waitFor(() => {
        expect(result.current.users[0]?.is_active).toBe(true);
      });
    });

    it('handles 404 not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      // Mock refetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      await expect(
        act(async () => {
          await result.current.updateUser('non-existent', { is_active: false });
        })
      ).rejects.toThrow('User not found');
    });
  });

  describe('refetch', () => {
    it('refetches data when called', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });

      const { result } = renderHook(() => useUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.users[0]?.email).toBe('test@example.com');

      const updatedResponse = {
        ...mockPaginatedResponse,
        data: [{ ...mockUser, email: 'updated@example.com' }],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedResponse),
      });

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });
  });
});
