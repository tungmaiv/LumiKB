/**
 * Hook for fetching and managing KB permissions (users + groups)
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1, AC-5.20.2, AC-5.20.3)
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  PermissionExtended,
  PermissionCreate,
  PermissionUpdate,
  PaginatedPermissionResponse,
  EffectivePermission,
  EffectivePermissionListResponse,
} from "@/types/permission";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UseKBPermissionsOptions {
  kbId: string;
  page?: number;
  limit?: number;
  enabled?: boolean;
}

export interface UseKBPermissionsReturn {
  permissions: PermissionExtended[];
  total: number;
  page: number;
  limit: number;
  isLoading: boolean;
  error: Error | null;
  grantPermission: (data: PermissionCreate) => Promise<PermissionExtended>;
  updatePermission: (id: string, data: PermissionUpdate) => Promise<PermissionExtended>;
  revokeUserPermission: (userId: string) => Promise<void>;
  revokeGroupPermission: (groupId: string) => Promise<void>;
  refetch: () => void;
  isGranting: boolean;
  isUpdating: boolean;
  isRevoking: boolean;
}

export interface UseEffectivePermissionsReturn {
  effectivePermissions: EffectivePermission[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

// API functions
async function fetchPermissions(
  kbId: string,
  page: number,
  limit: number
): Promise<PaginatedPermissionResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
  });

  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/all?${params}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) throw new Error("Knowledge Base not found");
    if (res.status === 401) throw new Error("Authentication required");
    throw new Error(`Failed to fetch permissions: ${res.statusText}`);
  }

  return res.json();
}

async function fetchEffectivePermissions(
  kbId: string
): Promise<EffectivePermissionListResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/effective`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) throw new Error("Knowledge Base not found");
    if (res.status === 401) throw new Error("Authentication required");
    throw new Error(`Failed to fetch effective permissions: ${res.statusText}`);
  }

  return res.json();
}

async function grantPermissionApi(
  kbId: string,
  data: PermissionCreate
): Promise<PermissionExtended> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/extended`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || "Resource not found");
    }
    if (res.status === 422) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail?.[0]?.msg || "Validation error");
    }
    throw new Error(`Failed to grant permission: ${res.statusText}`);
  }

  return res.json();
}

async function updatePermissionApi(
  kbId: string,
  permissionId: string,
  data: PermissionUpdate
): Promise<PermissionExtended> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/${permissionId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data),
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) throw new Error("Permission not found");
    throw new Error(`Failed to update permission: ${res.statusText}`);
  }

  return res.json();
}

async function revokeUserPermissionApi(kbId: string, userId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/${userId}`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) throw new Error("Permission not found");
    throw new Error(`Failed to revoke permission: ${res.statusText}`);
  }
}

async function revokeGroupPermissionApi(kbId: string, groupId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/permissions/groups/${groupId}`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    }
  );

  if (!res.ok) {
    if (res.status === 403) throw new Error("ADMIN permission required");
    if (res.status === 404) throw new Error("Permission not found");
    throw new Error(`Failed to revoke group permission: ${res.statusText}`);
  }
}

/**
 * Hook for listing and managing KB permissions (users + groups)
 */
export function useKBPermissions({
  kbId,
  page = 1,
  limit = 20,
  enabled = true,
}: UseKBPermissionsOptions): UseKBPermissionsReturn {
  const queryClient = useQueryClient();
  const queryKey = ["kb", kbId, "permissions", page, limit];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchPermissions(kbId, page, limit),
    enabled: enabled && !!kbId,
    staleTime: 30 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const grantMutation = useMutation({
    mutationFn: (grantData: PermissionCreate) => grantPermissionApi(kbId, grantData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "permissions"] });
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "effective-permissions"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data: updateData }: { id: string; data: PermissionUpdate }) =>
      updatePermissionApi(kbId, id, updateData),
    onMutate: async ({ id, data: updateData }) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<PaginatedPermissionResponse>(queryKey);

      if (previousData) {
        queryClient.setQueryData<PaginatedPermissionResponse>(queryKey, {
          ...previousData,
          data: previousData.data.map((perm) =>
            perm.id === id ? { ...perm, ...updateData } : perm
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
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "permissions"] });
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "effective-permissions"] });
    },
  });

  const revokeUserMutation = useMutation({
    mutationFn: (userId: string) => revokeUserPermissionApi(kbId, userId),
    onMutate: async (userId) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<PaginatedPermissionResponse>(queryKey);

      if (previousData) {
        queryClient.setQueryData<PaginatedPermissionResponse>(queryKey, {
          ...previousData,
          data: previousData.data.filter(
            (perm) => !(perm.entity_type === "user" && perm.entity_id === userId)
          ),
          total: previousData.total - 1,
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
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "permissions"] });
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "effective-permissions"] });
    },
  });

  const revokeGroupMutation = useMutation({
    mutationFn: (groupId: string) => revokeGroupPermissionApi(kbId, groupId),
    onMutate: async (groupId) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<PaginatedPermissionResponse>(queryKey);

      if (previousData) {
        queryClient.setQueryData<PaginatedPermissionResponse>(queryKey, {
          ...previousData,
          data: previousData.data.filter(
            (perm) => !(perm.entity_type === "group" && perm.entity_id === groupId)
          ),
          total: previousData.total - 1,
        });
      }

      return { previousData };
    },
    onError: (_err, _groupId, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "permissions"] });
      queryClient.invalidateQueries({ queryKey: ["kb", kbId, "effective-permissions"] });
    },
  });

  return {
    permissions: data?.data ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? page,
    limit: data?.limit ?? limit,
    isLoading,
    error: error as Error | null,
    grantPermission: grantMutation.mutateAsync,
    updatePermission: (id: string, updateData: PermissionUpdate) =>
      updateMutation.mutateAsync({ id, data: updateData }),
    revokeUserPermission: revokeUserMutation.mutateAsync,
    revokeGroupPermission: revokeGroupMutation.mutateAsync,
    refetch,
    isGranting: grantMutation.isPending,
    isUpdating: updateMutation.isPending,
    isRevoking: revokeUserMutation.isPending || revokeGroupMutation.isPending,
  };
}

/**
 * Hook for fetching effective permissions (computed from direct + group)
 */
export function useEffectivePermissions(
  kbId: string,
  enabled = true
): UseEffectivePermissionsReturn {
  const queryKey = ["kb", kbId, "effective-permissions"];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchEffectivePermissions(kbId),
    enabled: enabled && !!kbId,
    staleTime: 30 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  return {
    effectivePermissions: data?.data ?? [],
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
