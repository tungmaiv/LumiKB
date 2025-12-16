/**
 * Hook for fetching and managing LLM models (admin only)
 * Story 7-9: LLM Model Registry (AC-7.9.4, AC-7.9.5, AC-7.9.6)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  LLMModelSummary,
  LLMModelResponse,
  LLMModelCreate,
  LLMModelUpdate,
  LLMModelList,
  ConnectionTestResult,
  ModelType,
  ModelProvider,
  ModelStatus,
} from '@/types/llm-model';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseModelRegistryOptions {
  type?: ModelType;
  provider?: ModelProvider;
  status?: ModelStatus;
  skip?: number;
  limit?: number;
}

export interface UseModelRegistryReturn {
  models: LLMModelSummary[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  createModel: (data: LLMModelCreate) => Promise<LLMModelResponse>;
  updateModel: (id: string, data: LLMModelUpdate) => Promise<LLMModelResponse>;
  deleteModel: (id: string) => Promise<void>;
  setDefault: (id: string) => Promise<LLMModelResponse>;
  testConnection: (id: string, testInput?: string) => Promise<ConnectionTestResult>;
  refetch: () => void;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  isTesting: boolean;
}

async function fetchModels(options: UseModelRegistryOptions): Promise<LLMModelList> {
  const params = new URLSearchParams();

  if (options.type) params.append('type', options.type);
  if (options.provider) params.append('provider', options.provider);
  if (options.status) params.append('status', options.status);
  if (options.skip !== undefined) params.append('skip', String(options.skip));
  if (options.limit !== undefined) params.append('limit', String(options.limit));

  const url = params.toString()
    ? `${API_BASE_URL}/api/v1/admin/models?${params}`
    : `${API_BASE_URL}/api/v1/admin/models`;

  const res = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    throw new Error(`Failed to fetch models: ${res.statusText}`);
  }

  return res.json();
}

async function fetchModel(id: string): Promise<LLMModelResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models/${id}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Model not found');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to fetch model: ${res.statusText}`);
  }

  return res.json();
}

async function createModelApi(data: LLMModelCreate): Promise<LLMModelResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 400) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || 'Invalid model data');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to create model: ${res.statusText}`);
  }

  return res.json();
}

async function updateModelApi(id: string, data: LLMModelUpdate): Promise<LLMModelResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Model not found');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to update model: ${res.statusText}`);
  }

  return res.json();
}

async function deleteModelApi(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Model not found');
    }
    if (res.status === 400) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || 'Cannot delete model');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to delete model: ${res.statusText}`);
  }
}

async function setDefaultApi(id: string): Promise<LLMModelResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models/${id}/set-default`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Model not found');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to set default model: ${res.statusText}`);
  }

  return res.json();
}

async function testConnectionApi(id: string, testInput?: string): Promise<ConnectionTestResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/admin/models/${id}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ test_input: testInput }),
  });

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Model not found');
    }
    if (res.status === 403) {
      throw new Error('Unauthorized: Admin access required');
    }
    throw new Error(`Failed to test connection: ${res.statusText}`);
  }

  return res.json();
}

export function useModelRegistry(options: UseModelRegistryOptions = {}): UseModelRegistryReturn {
  const queryClient = useQueryClient();

  const queryKey = ['admin', 'models', options];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: () => fetchModels(options),
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const createMutation = useMutation({
    mutationFn: createModelApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: LLMModelUpdate }) =>
      updateModelApi(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteModelApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: setDefaultApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
    },
  });

  const testMutation = useMutation({
    mutationFn: ({ id, testInput }: { id: string; testInput?: string }) =>
      testConnectionApi(id, testInput),
  });

  return {
    models: data?.models ?? [],
    total: data?.total ?? 0,
    isLoading,
    error: error as Error | null,
    createModel: createMutation.mutateAsync,
    updateModel: (id: string, updateData: LLMModelUpdate) =>
      updateMutation.mutateAsync({ id, data: updateData }),
    deleteModel: deleteMutation.mutateAsync,
    setDefault: setDefaultMutation.mutateAsync,
    testConnection: (id: string, testInput?: string) =>
      testMutation.mutateAsync({ id, testInput }),
    refetch,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isTesting: testMutation.isPending,
  };
}

/**
 * Hook for fetching a single model by ID
 */
export function useModel(id: string | null) {
  return useQuery({
    queryKey: ['admin', 'models', id],
    queryFn: () => fetchModel(id!),
    enabled: !!id,
    staleTime: 30 * 1000,
    retry: 1,
  });
}
