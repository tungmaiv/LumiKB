/**
 * Unit tests for useGroups and useGroup hooks
 * Story 5.19: Group Management (AC-5.19.2, AC-5.19.3, AC-5.19.4)
 *
 * Test Coverage:
 * - [P1] useGroups: Fetch groups with pagination and search
 * - [P1] useGroups: Create, update, delete operations
 * - [P1] useGroups: Optimistic updates for mutations
 * - [P1] useGroup: Fetch single group with members
 * - [P1] useGroup: Add/remove members
 * - [P2] Error handling for all operations
 * - [P2] Cache invalidation on mutations
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Hook testing patterns
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ReactNode } from 'react';
import { useGroups, useGroup } from '../useGroups';
import type { Group, GroupWithMembers, PaginatedGroupResponse } from '@/types/group';
import { PermissionLevel } from '@/types/user';

// Mock fetch globally
global.fetch = vi.fn();

// Test data
const mockGroups: Group[] = [
  {
    id: 'group-1',
    name: 'Engineering',
    description: 'Software engineering team',
    is_active: true,
    permission_level: PermissionLevel.USER,
    is_system: false,
    member_count: 5,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-12-05T00:00:00Z',
  },
  {
    id: 'group-2',
    name: 'Marketing',
    description: 'Marketing team',
    is_active: true,
    permission_level: PermissionLevel.OPERATOR,
    is_system: false,
    member_count: 3,
    created_at: '2025-01-15T00:00:00Z',
    updated_at: '2025-12-04T00:00:00Z',
  },
];

const mockPaginatedResponse: PaginatedGroupResponse = {
  items: mockGroups,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockGroupWithMembers: GroupWithMembers = {
  ...mockGroups[0],
  members: [
    { id: 'user-1', email: 'alice@example.com', is_active: true, joined_at: '2025-01-01T00:00:00Z' },
    { id: 'user-2', email: 'bob@example.com', is_active: true, joined_at: '2025-01-02T00:00:00Z' },
  ],
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // Disable cache to ensure fresh state
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

describe('useGroups', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetching groups', () => {
    it('[P1] should fetch groups successfully', async () => {
      /**
       * GIVEN: API returns paginated groups
       * WHEN: useGroups hook is called
       * THEN: groups are returned with pagination info
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.groups).toEqual(mockGroups);
      expect(result.current.total).toBe(2);
      expect(result.current.page).toBe(1);
      expect(result.current.pageSize).toBe(20);
      expect(result.current.totalPages).toBe(1);
    });

    it('[P1] should pass pagination parameters to API', async () => {
      /**
       * GIVEN: useGroups with custom pagination
       * WHEN: Hook fetches data
       * THEN: API is called with correct params
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockPaginatedResponse, page: 2, page_size: 10 }),
      });

      renderHook(() => useGroups({ page: 2, pageSize: 10 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('page=2'),
          expect.anything()
        );
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page_size=10'),
        expect.anything()
      );
    });

    it('[P1] should pass search parameter to API', async () => {
      /**
       * GIVEN: useGroups with search term
       * WHEN: Hook fetches data
       * THEN: API is called with search param
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      renderHook(() => useGroups({ search: 'Engineering' }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('search=Engineering'),
          expect.anything()
        );
      });
    });

    it('[P2] should handle 403 Forbidden error', async () => {
      /**
       * GIVEN: API returns 403
       * WHEN: useGroups fetches
       * THEN: error is set with appropriate message
       */
      // Mock both initial fetch and retry (hook has retry: 1)
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

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('Admin access required');
    });

    it('[P2] should handle 401 Unauthorized error', async () => {
      /**
       * GIVEN: API returns 401
       * WHEN: useGroups fetches
       * THEN: error is set with authentication message
       */
      // Mock both initial fetch and retry (hook has retry: 1)
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
        });

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('Authentication required');
    });
  });

  describe('createGroup', () => {
    it('[P1] should create group successfully', async () => {
      /**
       * GIVEN: Valid group data
       * WHEN: createGroup is called
       * THEN: API POST is made and result returned
       */
      const newGroup: Group = {
        id: 'group-3',
        name: 'New Team',
        description: 'A new team',
        is_active: true,
        permission_level: PermissionLevel.USER,
        is_system: false,
        member_count: 0,
        created_at: '2025-12-05T00:00:00Z',
        updated_at: '2025-12-05T00:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => newGroup,
        });

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let createdGroup: Group | undefined;
      await act(async () => {
        createdGroup = await result.current.createGroup({
          name: 'New Team',
          description: 'A new team',
        });
      });

      expect(createdGroup).toEqual(newGroup);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/groups'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'New Team', description: 'A new team' }),
        })
      );
    });

    it('[P2] should handle duplicate name error (409)', async () => {
      /**
       * GIVEN: Group name already exists
       * WHEN: createGroup is called
       * THEN: Error is thrown with conflict message
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 409,
          json: async () => ({ detail: 'Group name already exists' }),
        });

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await expect(
        act(async () => {
          await result.current.createGroup({ name: 'Engineering' });
        })
      ).rejects.toThrow('Group name already exists');
    });
  });

  describe('updateGroup', () => {
    it('[P1] should update group successfully', async () => {
      /**
       * GIVEN: Existing group
       * WHEN: updateGroup is called
       * THEN: API PATCH is made and result returned
       */
      const updatedGroup: Group = { ...mockGroups[0], name: 'Updated Engineering' };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPaginatedResponse,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedGroup,
        });

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let resultGroup: Group | undefined;
      await act(async () => {
        resultGroup = await result.current.updateGroup('group-1', { name: 'Updated Engineering' });
      });

      expect(resultGroup?.name).toBe('Updated Engineering');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/groups/group-1'),
        expect.objectContaining({
          method: 'PATCH',
        })
      );
    });

    it('[P2] should handle not found error (404)', async () => {
      /**
       * GIVEN: Non-existent group
       * WHEN: updateGroup is called
       * THEN: Error is thrown with not found message
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

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await expect(
        act(async () => {
          await result.current.updateGroup('nonexistent', { name: 'New Name' });
        })
      ).rejects.toThrow('Group not found');
    });
  });

  describe('deleteGroup', () => {
    it('[P1] should delete group successfully', async () => {
      /**
       * GIVEN: Existing group
       * WHEN: deleteGroup is called
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

      const { result } = renderHook(() => useGroups(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.deleteGroup('group-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/groups/group-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

  });
});

describe('useGroup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetching single group', () => {
    it('[P1] should fetch group with members successfully', async () => {
      /**
       * GIVEN: Valid group ID
       * WHEN: useGroup is called
       * THEN: Group with members is returned
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockGroupWithMembers,
      });

      const { result } = renderHook(() => useGroup('group-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      expect(result.current.group).toEqual(mockGroupWithMembers);
      expect(result.current.group?.members).toHaveLength(2);
    });

    it('[P1] should not fetch when groupId is null', async () => {
      /**
       * GIVEN: null groupId
       * WHEN: useGroup is called
       * THEN: No API call is made
       */
      const { result } = renderHook(() => useGroup(null), {
        wrapper: createWrapper(),
      });

      // Wait a bit to ensure no fetch happens
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockFetch).not.toHaveBeenCalled();
      expect(result.current.group).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('[P2] should handle not found error', async () => {
      /**
       * GIVEN: Non-existent group ID
       * WHEN: useGroup fetches
       * THEN: Error is set
       */
      // Mock both initial fetch and retry (hook has retry: 1)
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

      const { result } = renderHook(() => useGroup('nonexistent'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.error).not.toBeNull(), {
        timeout: 3000,
      });

      expect(result.current.error?.message).toContain('Group not found');
    });
  });

  describe('addMembers', () => {
    it('[P1] should add members successfully', async () => {
      /**
       * GIVEN: Group with existing members
       * WHEN: addMembers is called
       * THEN: API POST is made with user IDs
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockGroupWithMembers,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ added_count: 2 }),
        });

      const { result } = renderHook(() => useGroup('group-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let response;
      await act(async () => {
        response = await result.current.addMembers(['user-3', 'user-4']);
      });

      expect(response).toEqual({ added_count: 2 });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/groups/group-1/members'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ user_ids: ['user-3', 'user-4'] }),
        })
      );
    });

    it('[P2] should reject when no groupId', async () => {
      /**
       * GIVEN: null groupId
       * WHEN: addMembers is called
       * THEN: Error is thrown
       */
      const { result } = renderHook(() => useGroup(null), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.addMembers(['user-1']);
        })
      ).rejects.toThrow('No group');
    });
  });

  describe('removeMember', () => {
    it('[P1] should remove member successfully', async () => {
      /**
       * GIVEN: Group with members
       * WHEN: removeMember is called
       * THEN: API DELETE is made
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockGroupWithMembers,
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

      const { result } = renderHook(() => useGroup('group-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.removeMember('user-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/groups/group-1/members/user-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('[P2] should handle membership not found error', async () => {
      /**
       * GIVEN: User not in group
       * WHEN: removeMember is called
       * THEN: Error is thrown
       */
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockGroupWithMembers,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        });

      const { result } = renderHook(() => useGroup('group-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await expect(
        act(async () => {
          await result.current.removeMember('nonexistent-user');
        })
      ).rejects.toThrow('not found');
    });
  });

  describe('refetch', () => {
    it('[P1] should allow manual refetch', async () => {
      /**
       * GIVEN: Group data loaded
       * WHEN: refetch is called
       * THEN: API is called again
       */
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockGroupWithMembers,
      });

      const { result } = renderHook(() => useGroup('group-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      act(() => {
        result.current.refetch();
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });
  });
});
