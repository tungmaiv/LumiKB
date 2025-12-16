/**
 * Hook for fetching available models for KB configuration.
 * Story 7-10: KB Model Configuration (AC-7.10.1, 7.10.6)
 *
 * Provides access to active models from the Model Registry for KB owners
 * to select embedding and generation models during KB creation and settings.
 */

import { useQuery } from '@tanstack/react-query';
import type { LLMModelSummary, ModelAvailableResponse } from '@/types/llm-model';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseAvailableModelsReturn {
  /** Available embedding models for KB document processing */
  embeddingModels: LLMModelSummary[];
  /** Available generation models for KB document generation */
  generationModels: LLMModelSummary[];
  /** Available NER models for entity extraction */
  nerModels: LLMModelSummary[];
  /** The default embedding model (is_default=true) */
  defaultEmbeddingModel: LLMModelSummary | null;
  /** The default generation model (is_default=true) */
  defaultGenerationModel: LLMModelSummary | null;
  /** Loading state */
  isLoading: boolean;
  /** Error if fetch failed */
  error: Error | null;
  /** Refetch models */
  refetch: () => void;
}

async function fetchAvailableModels(): Promise<ModelAvailableResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/models/available`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new Error('Authentication required');
    }
    throw new Error(`Failed to fetch available models: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Hook for fetching available models for KB configuration.
 *
 * Returns active embedding and generation models that can be selected
 * when creating or configuring a knowledge base.
 *
 * @example
 * ```tsx
 * const { embeddingModels, generationModels, isLoading } = useAvailableModels();
 *
 * // Use in a select dropdown
 * <Select>
 *   {embeddingModels.map(model => (
 *     <SelectItem key={model.id} value={model.id}>
 *       {model.name}
 *     </SelectItem>
 *   ))}
 * </Select>
 * ```
 */
export function useAvailableModels(): UseAvailableModelsReturn {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['models', 'available'],
    queryFn: fetchAvailableModels,
    staleTime: 5 * 60 * 1000, // 5 minutes - models don't change often
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Find default models for display in UI
  const embeddingModels = data?.embedding_models ?? [];
  const generationModels = data?.generation_models ?? [];
  const defaultEmbeddingModel = embeddingModels.find((m) => m.is_default) ?? null;
  const defaultGenerationModel = generationModels.find((m) => m.is_default) ?? null;

  return {
    embeddingModels,
    generationModels,
    nerModels: data?.ner_models ?? [],
    defaultEmbeddingModel,
    defaultGenerationModel,
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
