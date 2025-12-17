/**
 * Unit tests for useKBPermissions and useEffectivePermissions hooks
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1, AC-5.20.2, AC-5.20.3)
 *
 * Test Coverage:
 * - [P1] useKBPermissions: Fetch permissions with pagination
 * - [P1] useKBPermissions: Grant, update, revoke user permissions
 * - [P1] useKBPermissions: Grant, revoke group permissions
 * - [P1] useKBPermissions: Optimistic updates for mutations
 * - [P1] useEffectivePermissions: Fetch computed permissions
 * - [P2] Error handling for all operations
 * - [P2] Cache invalidation on mutations
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Hook testing patterns
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ReactNode } from 'react';
import { useKBPermissions, useEffectivePermissions } from '../useKBPermissions';
import type {
  PermissionExtended,
  PaginatedPermissionResponse,
  EffectivePermission,
  EffectivePermissionListResponse,
} from '@/types/permission';

// Mock fetch globally
global.fetch = vi.fn();

// Test data
const mockUserPermission: PermissionExtended = {
  id: 'perm-1',
  entity_type: 'user',
  entity_id: 'user-1',
  entity_name: 'alice@example.com',
  kb_id: 'kb-1',
  permission_level: 'READ',
  created_at: '2025-01-01T00:00:00Z',
};

const mockGroupPermission: PermissionExtended = {
  id: 'perm-2',
  entity_type: 'group',
  entity_id: 'group-1',
  entity_name: 'Engineering',
  kb_id: 'kb-1',
  permission_level: 'WRITE',
  created_at: '2025-01-02T00:00:00Z',
};

const mockPermissions: PermissionExtended[] = [mockUserPermission, mockGroupPermission];

const mockPaginatedResponse: PaginatedPermissionResponse = {
  data: mockPermissions,
  total: 2,
  page: 1,
  limit: 20,
};

const mockEffectivePermissions: EffectivePermission[] = [
  {
    user_id: 'user-1',
    user_email: 'alice@example.com',
    effective_level: 'WRITE',
    sources: [
      {
        source_type: 'direct',
        source_id: 'user-1',
        source_name: 'alice@example.com',
        permission_level: 'READ',
      },
      {
        source_type: 'group',
        source_id: 'group-1',
        source_name: 'Engineering',
        permission_level: 'WRITE',
      },
    ],
  },
];

const mockEffectiveResponse: EffectivePermissionListResponse = {
  data: mockEffectivePermissions,
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Helper to setup mock fetch
const mockFetch = global.fetch as ReturnType<typeof vi.fn>;

describe('useKBPermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetching permissions', () => {
    it('[P1] should fetch permissions successfully', async () => {
      /**
       * GIVEN: API returns paginated permissions
       * WHEN: useKBPermissions hook is called
       * THEN: permissions are returned with pagination info
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.permissions).toEqual(mockPermissions);
      expect(result.current.total).toBe(2);
      expect(result.current.page).toBe(1);
      expect(result.current.limit).toBe(20);
    });

    it('[P1] should pass pagination parameters to API', async () => {
      /**
       * GIVEN: useKBPermissions with custom pagination
       * WHEN: Hook fetches data
       * THEN: API is called with correct params
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockPaginatedResponse, page: 2, limit: 10 }),
      });

      renderHook(() => useKBPermissions({ kbId: 'kb-1', page: 2, limit: 10 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('page=2'),
          expect.anything()
        );
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=10'),
        expect.anything()
      );
    });

    it('[P1] should not fetch when kbId is empty', async () => {
      /**
       * GIVEN: Empty kbId
       * WHEN: useKBPermissions is called
       * THEN: No API call is made
       */
      const { result } = renderHook(() => useKBPermissions({ kbId: '' }), {
        wrapper: createWrapper(),
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockFetch).not.toHaveBeenCalled();
      expect(result.current.permissions).toEqual([]);
      expect(result.current.isLoading).toBe(false);
    });

    it('[P2] should handle 403 Forbidden error', async () => {
      /**
       * GIVEN: API returns 403
       * WHEN: useKBPermissions fetches
       * THEN: error is set with appropriate message
       */
      // Hook has retry: 1, so mock both attempts
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('ADMIN permission required');
    });

    it('[P2] should handle 404 Not Found error', async () => {
      /**
       * GIVEN: API returns 404
       * WHEN: useKBPermissions fetches
       * THEN: error is set with not found message
       */
      // Hook has retry: 1, so mock both attempts
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('Knowledge Base not found');
    });
  });

  describe('grantPermission', () => {
    it('[P1] should grant user permission successfully', async () => {
      /**
       * GIVEN: Valid user permission data
       * WHEN: grantPermission is called
       * THEN: API POST is made and result returned
       */
      const newPermission: PermissionExtended = {
        id: 'perm-3',
        entity_type: 'user',
        entity_id: 'user-2',
        entity_name: 'bob@example.com',
        kb_id: 'kb-1',
        permission_level: 'WRITE',
        created_at: '2025-12-05T00:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => newPermission,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let grantedPermission: PermissionExtended | undefined;
      await act(async () => {
        grantedPermission = await result.current.grantPermission({
          user_id: 'user-2',
          permission_level: 'WRITE',
        });
      });

      expect(grantedPermission).toEqual(newPermission);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/permissions/extended'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ user_id: 'user-2', permission_level: 'WRITE' }),
        })
      );
    });

    it('[P1] should grant group permission successfully', async () => {
      /**
       * GIVEN: Valid group permission data
       * WHEN: grantPermission is called with group_id
       * THEN: API POST is made for group permission
       */
      const newGroupPerm: PermissionExtended = {
        id: 'perm-4',
        entity_type: 'group',
        entity_id: 'group-2',
        entity_name: 'Marketing',
        kb_id: 'kb-1',
        permission_level: 'READ',
        created_at: '2025-12-05T00:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => newGroupPerm,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let grantedPermission: PermissionExtended | undefined;
      await act(async () => {
        grantedPermission = await result.current.grantPermission({
          group_id: 'group-2',
          permission_level: 'READ',
        });
      });

      expect(grantedPermission?.entity_type).toBe('group');
      expect(grantedPermission?.entity_name).toBe('Marketing');
    });
  });

  describe('updatePermission', () => {
    it('[P1] should update permission level successfully', async () => {
      /**
       * GIVEN: Existing permission
       * WHEN: updatePermission is called
       * THEN: API PATCH is made and result returned
       */
      const updatedPermission: PermissionExtended = {
        ...mockUserPermission,
        permission_level: 'ADMIN',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedPermission,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let resultPerm: PermissionExtended | undefined;
      await act(async () => {
        resultPerm = await result.current.updatePermission('perm-1', {
          permission_level: 'ADMIN',
        });
      });

      expect(resultPerm?.permission_level).toBe('ADMIN');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/permissions/perm-1'),
        expect.objectContaining({
          method: 'PATCH',
        })
      );
    });

    it('[P2] should handle permission not found error', async () => {
      /**
       * GIVEN: Non-existent permission ID
       * WHEN: updatePermission is called
       * THEN: Error is thrown
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await expect(
        act(async () => {
          await result.current.updatePermission('nonexistent', {
            permission_level: 'WRITE',
          });
        })
      ).rejects.toThrow('Permission not found');
    });
  });

  describe('revokeUserPermission', () => {
    it('[P1] should revoke user permission successfully', async () => {
      /**
       * GIVEN: Existing user permission
       * WHEN: revokeUserPermission is called
       * THEN: API DELETE is made
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.revokeUserPermission('user-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/permissions/user-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('[P1] should apply optimistic update when revoking', async () => {
      /**
       * GIVEN: Existing permissions list
       * WHEN: revokeUserPermission is called
       * THEN: Permission is removed optimistically
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(result.current.permissions).toHaveLength(2);

      // Start the revoke mutation - optimistic update removes immediately
      act(() => {
        result.current.revokeUserPermission('user-1');
      });

      // The optimistic update should have removed the user permission
      await waitFor(() => {
        const userPerms = result.current.permissions.filter(
          (p) => p.entity_type === 'user' && p.entity_id === 'user-1'
        );
        expect(userPerms).toHaveLength(0);
      });
    });
  });

  describe('revokeGroupPermission', () => {
    it('[P1] should revoke group permission successfully', async () => {
      /**
       * GIVEN: Existing group permission
       * WHEN: revokeGroupPermission is called
       * THEN: API DELETE is made to groups endpoint
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

      const { result } = renderHook(() => useKBPermissions({ kbId: 'kb-1' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.revokeGroupPermission('group-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/permissions/groups/group-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });
});

describe('useEffectivePermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetching effective permissions', () => {
    it('[P1] should fetch effective permissions successfully', async () => {
      /**
       * GIVEN: API returns effective permissions
       * WHEN: useEffectivePermissions hook is called
       * THEN: computed permissions are returned
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockEffectiveResponse,
      });

      const { result } = renderHook(() => useEffectivePermissions('kb-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.effectivePermissions).toEqual(mockEffectivePermissions);
      expect(result.current.effectivePermissions[0].effective_level).toBe('WRITE');
      expect(result.current.effectivePermissions[0].sources).toHaveLength(2);
    });

    it('[P1] should not fetch when kbId is empty', async () => {
      /**
       * GIVEN: Empty kbId
       * WHEN: useEffectivePermissions is called
       * THEN: No API call is made
       */
      const { result } = renderHook(() => useEffectivePermissions('', false), {
        wrapper: createWrapper(),
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockFetch).not.toHaveBeenCalled();
      expect(result.current.effectivePermissions).toEqual([]);
    });

    it('[P2] should handle error responses', async () => {
      /**
       * GIVEN: API returns error
       * WHEN: useEffectivePermissions fetches
       * THEN: Error is set
       */
      // Hook has retry: 1, so mock both attempts
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
        });

      const { result } = renderHook(() => useEffectivePermissions('kb-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('ADMIN permission required');
    });
  });
});
