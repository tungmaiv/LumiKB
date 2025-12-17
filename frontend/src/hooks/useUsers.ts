/**
 * Hook for fetching and managing users (admin only)
 * Story 5.18: User Management UI
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  UserRead,
  UserCreate,
  AdminUserUpdate,
  PaginatedResponse,
  PaginationMeta,
} from '@/types/user';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseUsersOptions {
  page?: number;
  pageSize?: number;
  search?: string;
  isActive?: boolean | null; // Filter by active status (true/false/null for all)
}

export interface UseUsersReturn {
  users: UserRead[];
  pagination: PaginationMeta | null;
  isLoading: boolean;
  error: Error | null;
  createUser: (data: UserCreate) => Promise<UserRead>;
  updateUser: (id: string, data: AdminUserUpdate) => Promise<UserRead>;
  refetch: () => void;
  isCreating: boolean;
  isUpdating: boolean;
}

async function fetchUsers(
  page: number,
  pageSize: number,
  isActive?: boolean | null
): Promise<PaginatedResponse<UserRead>> {
  const skip = (page - 1) * pageSize;
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(pageSize),
  });

  // Add is_active filter if specified (not null/undefined)
  if (isActive !== null && isActive !== undefined) {
    params.append('is_active', String(isActive));
  }

  const res = await fetch(`${API_BASE_URL}/api/v1/admin/users?${params}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    throw new Error(`Failed to fetch users: ${res.statusText}`);
  }

  return res.json();
}

async function createUserApi(data: UserCreate): Promise<UserRead> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 409) {
      throw new Error('Email already exists');
    }
    if (res.status === 400) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || 'Invalid user data');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to create user: ${res.statusText}`);
  }

  return res.json();
}

async function updateUserApi(id: string, data: AdminUserUpdate): Promise<UserRead> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/users/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('User not found');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to update user: ${res.statusText}`);
  }

  return res.json();
}

export function useUsers({
  page = 1,
  pageSize = 20,
  isActive = null,
}: UseUsersOptions = {}): UseUsersReturn {
  const queryClient = useQueryClient();

  const queryKey = ['admin', 'users', page, pageSize, isActive];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchUsers(page, pageSize, isActive),
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const createMutation = useMutation({
    mutationFn: createUserApi,
    onSuccess: () => {
      // Invalidate users list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: AdminUserUpdate }) => updateUserApi(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<PaginatedResponse<UserRead>>(queryKey);

      // Optimistically update
      if (previousData) {
        queryClient.setQueryData<PaginatedResponse<UserRead>>(queryKey, {
          ...previousData,
          data: previousData.data.map((user) => (user.id === id ? { ...user, ...data } : user)),
        });
      }

      return { previousData };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  return {
    users: data?.data ?? [],
    pagination: data?.meta ?? null,
    isLoading,
    error: error as Error | null,
    createUser: createMutation.mutateAsync,
    updateUser: (id: string, updateData: AdminUserUpdate) =>
      updateMutation.mutateAsync({ id, data: updateData }),
    refetch,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
  };
}
