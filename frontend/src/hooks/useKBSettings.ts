/**
 * Hook for fetching and updating KB settings.
 * Story 7-14: KB Settings UI - General Panel (AC-7.14.6, AC-7.14.8)
 *
 * Provides access to KB-level configuration including chunking, retrieval,
 * and generation settings with optimistic updates and cache management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type {
  KBSettings,
  KBSettingsUpdate,
  KBSettingsResponse,
  DEFAULT_KB_SETTINGS,
} from '@/types/kb-settings';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Query Key Factory
// =============================================================================

export const kbSettingsKeys = {
  all: ['kb-settings'] as const,
  byId: (kbId: string) => [...kbSettingsKeys.all, kbId] as const,
};

// =============================================================================
// API Functions
// =============================================================================

async function fetchKBSettings(kbId: string): Promise<KBSettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/settings`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    if (res.status === 403) {
      throw new Error('You do not have permission to view these settings');
    }
    if (res.status === 404) {
      throw new Error('Knowledge base not found');
    }
    throw new Error(`Failed to fetch KB settings: ${res.statusText}`);
  }

  return res.json();
}

async function updateKBSettings(
  kbId: string,
  settings: KBSettingsUpdate
): Promise<KBSettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(settings),
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    if (res.status === 403) {
      throw new Error('You do not have permission to update these settings');
    }
    if (res.status === 404) {
      throw new Error('Knowledge base not found');
    }
    if (res.status === 422) {
      const error = await res.json();
      throw new Error(error.detail || 'Invalid settings values');
    }
    throw new Error(`Failed to update KB settings: ${res.statusText}`);
  }

  return res.json();
}

// =============================================================================
// Hook Return Types
// =============================================================================

export interface UseKBSettingsReturn {
  /** Current KB settings */
  settings: KBSettings | undefined;
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error if fetch failed */
  error: Error | null;
  /** Whether settings are being saved */
  isSaving: boolean;
  /** Update KB settings */
  updateSettings: (settings: KBSettingsUpdate) => Promise<void>;
  /** Refetch settings from server */
  refetch: () => void;
}

// =============================================================================
// Main Hook
// =============================================================================

/**
 * Hook for fetching and updating KB settings.
 *
 * Provides settings data with optimistic updates and automatic cache invalidation.
 * Uses 5-minute stale time to balance freshness with performance.
 *
 * @param kbId - Knowledge Base ID to fetch settings for
 *
 * @example
 * ```tsx
 * const { settings, isLoading, updateSettings, isSaving } = useKBSettings(kbId);
 *
 * const handleSave = async (formData: KBSettingsFormData) => {
 *   await updateSettings({
 *     chunking: formData.chunking,
 *     retrieval: formData.retrieval,
 *     generation: formData.generation,
 *   });
 * };
 * ```
 */
export function useKBSettings(kbId: string): UseKBSettingsReturn {
  const queryClient = useQueryClient();

  // Fetch settings (AC-7.14.8)
  const {
    data: settings,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: kbSettingsKeys.byId(kbId),
    queryFn: () => fetchKBSettings(kbId),
    staleTime: 5 * 60 * 1000, // 5 minutes (AC-7.14 - React Query caching)
    enabled: !!kbId,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Update settings mutation with optimistic updates (AC-7.14.6)
  const mutation = useMutation({
    mutationFn: (newSettings: KBSettingsUpdate) => updateKBSettings(kbId, newSettings),
    onMutate: async (newSettings) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: kbSettingsKeys.byId(kbId) });

      // Snapshot the previous value
      const previousSettings = queryClient.getQueryData<KBSettings>(kbSettingsKeys.byId(kbId));

      // Optimistically update to the new value
      if (previousSettings) {
        const mergedSettings: KBSettings = {
          ...previousSettings,
          chunking: { ...previousSettings.chunking, ...newSettings.chunking },
          retrieval: { ...previousSettings.retrieval, ...newSettings.retrieval },
          generation: { ...previousSettings.generation, ...newSettings.generation },
          reranking: { ...previousSettings.reranking, ...newSettings.reranking },
          ner: { ...previousSettings.ner, ...newSettings.ner },
          processing: { ...previousSettings.processing, ...newSettings.processing },
          prompts: { ...previousSettings.prompts, ...newSettings.prompts },
          embedding: { ...previousSettings.embedding, ...newSettings.embedding },
          preset: newSettings.preset !== undefined ? newSettings.preset : previousSettings.preset,
        };
        queryClient.setQueryData<KBSettings>(kbSettingsKeys.byId(kbId), mergedSettings);
      }

      return { previousSettings };
    },
    onError: (err, _newSettings, context) => {
      // Rollback on error
      if (context?.previousSettings) {
        queryClient.setQueryData(kbSettingsKeys.byId(kbId), context.previousSettings);
      }
      toast.error(err instanceof Error ? err.message : 'Failed to save settings');
    },
    onSuccess: () => {
      toast.success('Settings saved successfully');
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: kbSettingsKeys.byId(kbId) });
    },
  });

  const updateSettings = async (newSettings: KBSettingsUpdate): Promise<void> => {
    await mutation.mutateAsync(newSettings);
  };

  return {
    settings,
    isLoading,
    error: error as Error | null,
    isSaving: mutation.isPending,
    updateSettings,
    refetch,
  };
}
