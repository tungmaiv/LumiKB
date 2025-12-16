/**
 * Hook for fetching and managing groups (admin only)
 * Story 5.19: Group Management (AC-5.19.2, AC-5.19.3, AC-5.19.4)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  Group,
  GroupWithMembers,
  GroupCreate,
  GroupUpdate,
  GroupMemberAddResponse,
  PaginatedGroupResponse,
} from '@/types/group';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseGroupsOptions {
  page?: number;
  pageSize?: number;
  search?: string;
}

export interface UseGroupsReturn {
  groups: Group[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  isLoading: boolean;
  error: Error | null;
  createGroup: (data: GroupCreate) => Promise<Group>;
  updateGroup: (id: string, data: GroupUpdate) => Promise<Group>;
  deleteGroup: (id: string) => Promise<void>;
  refetch: () => void;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
}

export interface UseGroupReturn {
  group: GroupWithMembers | null;
  isLoading: boolean;
  error: Error | null;
  addMembers: (userIds: string[]) => Promise<GroupMemberAddResponse>;
  removeMember: (userId: string) => Promise<void>;
  refetch: () => void;
  isAddingMembers: boolean;
  isRemovingMember: boolean;
}

// API functions
async function fetchGroups(
  page: number,
  pageSize: number,
  search?: string
): Promise<PaginatedGroupResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (search) {
    params.append('search', search);
  }

  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups?${params}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    if (res.status === 401) throw new Error('Authentication required');
    throw new Error(`Failed to fetch groups: ${res.statusText}`);
  }

  return res.json();
}

async function fetchGroup(groupId: string): Promise<GroupWithMembers> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups/${groupId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 404) throw new Error('Group not found');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    if (res.status === 401) throw new Error('Authentication required');
    throw new Error(`Failed to fetch group: ${res.statusText}`);
  }

  return res.json();
}

async function createGroupApi(data: GroupCreate): Promise<Group> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 409) throw new Error('Group name already exists');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to create group: ${res.statusText}`);
  }

  return res.json();
}

async function updateGroupApi(id: string, data: GroupUpdate): Promise<Group> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 404) throw new Error('Group not found');
    if (res.status === 409) throw new Error('Group name already exists');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    throw new Error(`Failed to update group: ${res.statusText}`);
  }

  return res.json();
}

async function deleteGroupApi(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 404) throw new Error('Group not found');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    throw new Error(`Failed to delete group: ${res.statusText}`);
  }
}

async function addMembersApi(
  groupId: string,
  userIds: string[]
): Promise<GroupMemberAddResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/groups/${groupId}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ user_ids: userIds }),
  });

  if (!res.ok) {
    if (res.status === 404) throw new Error('Group not found');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    throw new Error(`Failed to add members: ${res.statusText}`);
  }

  return res.json();
}

async function removeMemberApi(groupId: string, userId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/admin/groups/${groupId}/members/${userId}`,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    }
  );

  if (!res.ok) {
    if (res.status === 404) throw new Error('Group or membership not found');
    if (res.status === 403) throw new Error('Unauthorized: Admin access required');
    throw new Error(`Failed to remove member: ${res.statusText}`);
  }
}

// Hook for listing groups
export function useGroups({
  page = 1,
  pageSize = 20,
  search,
}: UseGroupsOptions = {}): UseGroupsReturn {
  const queryClient = useQueryClient();
  const queryKey = ['admin', 'groups', page, pageSize, search];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchGroups(page, pageSize, search),
    staleTime: 30 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const createMutation = useMutation({
    mutationFn: createGroupApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: GroupUpdate }) =>
      updateGroupApi(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<PaginatedGroupResponse>(queryKey);

      if (previousData) {
        queryClient.setQueryData<PaginatedGroupResponse>(queryKey, {
          ...previousData,
          items: previousData.items.map((group) =>
            group.id === id ? { ...group, ...data } : group
          ),
        });
      }

      return { previousData };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteGroupApi,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<PaginatedGroupResponse>(queryKey);

      if (previousData) {
        queryClient.setQueryData<PaginatedGroupResponse>(queryKey, {
          ...previousData,
          items: previousData.items.filter((group) => group.id !== id),
          total: previousData.total - 1,
        });
      }

      return { previousData };
    },
    onError: (_err, _id, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
    },
  });

  return {
    groups: data?.items ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? pageSize,
    totalPages: data?.total_pages ?? 1,
    isLoading,
    error: error as Error | null,
    createGroup: createMutation.mutateAsync,
    updateGroup: (id: string, updateData: GroupUpdate) =>
      updateMutation.mutateAsync({ id, data: updateData }),
    deleteGroup: deleteMutation.mutateAsync,
    refetch,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

// Hook for single group with members
export function useGroup(groupId: string | null): UseGroupReturn {
  const queryClient = useQueryClient();
  const queryKey = ['admin', 'group', groupId];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => (groupId ? fetchGroup(groupId) : Promise.resolve(null)),
    enabled: !!groupId,
    staleTime: 30 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const addMembersMutation = useMutation({
    mutationFn: (userIds: string[]) =>
      groupId ? addMembersApi(groupId, userIds) : Promise.reject(new Error('No group')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) =>
      groupId ? removeMemberApi(groupId, userId) : Promise.reject(new Error('No group')),
    onMutate: async (userId) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<GroupWithMembers>(queryKey);

      if (previousData) {
        queryClient.setQueryData<GroupWithMembers>(queryKey, {
          ...previousData,
          members: previousData.members.filter((m) => m.id !== userId),
          member_count: previousData.member_count - 1,
        });
      }

      return { previousData };
    },
    onError: (_err, _userId, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
    },
  });

  return {
    group: data ?? null,
    isLoading,
    error: error as Error | null,
    addMembers: addMembersMutation.mutateAsync,
    removeMember: removeMemberMutation.mutateAsync,
    refetch,
    isAddingMembers: addMembersMutation.isPending,
    isRemovingMember: removeMemberMutation.isPending,
  };
}
