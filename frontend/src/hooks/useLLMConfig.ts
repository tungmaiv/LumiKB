/**
 * Hook for fetching and updating LLM configuration settings.
 * Story 7-2: Centralized LLM Configuration
 *
 * Features:
 * - Fetches current LLM config (embedding/generation models, settings)
 * - Updates config with hot-reload (no restart required)
 * - Tests model health/connectivity
 * - Handles dimension mismatch warnings
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import type {
  LLMConfig,
  LLMConfigUpdateRequest,
  LLMConfigUpdateResponse,
  LLMHealthResponse,
  RewriterModelResponse,
} from '@/types/llm-config';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Stale time for config polling (30 seconds as per story requirements)
const STALE_TIME_MS = 30000;

interface UseLLMConfigReturn {
  config: LLMConfig | undefined;
  isLoading: boolean;
  error: Error | null;
  updateConfig: (request: LLMConfigUpdateRequest) => Promise<LLMConfigUpdateResponse>;
  isUpdating: boolean;
  updateError: Error | null;
  health: LLMHealthResponse | undefined;
  isTestingHealth: boolean;
  testHealth: () => Promise<LLMHealthResponse>;
  refetch: () => Promise<void>;
  lastFetched: Date | null;
  // Story 8-0: Query Rewriter Model Configuration
  rewriterModelId: string | null | undefined;
  isLoadingRewriterModel: boolean;
  rewriterModelError: Error | null;
  updateRewriterModel: (modelId: string | null) => Promise<void>;
  isUpdatingRewriterModel: boolean;
  fetchRewriterModel: () => Promise<void>;
}

export function useLLMConfig(): UseLLMConfigReturn {
  const [config, setConfig] = useState<LLMConfig | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<Error | null>(null);
  const [health, setHealth] = useState<LLMHealthResponse | undefined>();
  const [isTestingHealth, setIsTestingHealth] = useState(false);
  const [lastFetched, setLastFetched] = useState<Date | null>(null);

  // Story 8-0: Query Rewriter Model state
  const [rewriterModelId, setRewriterModelId] = useState<string | null | undefined>();
  const [isLoadingRewriterModel, setIsLoadingRewriterModel] = useState(false);
  const [rewriterModelError, setRewriterModelError] = useState<Error | null>(null);
  const [isUpdatingRewriterModel, setIsUpdatingRewriterModel] = useState(false);

  // Track if initial fetch is in progress to prevent duplicate calls
  const fetchingRef = useRef(false);
  const fetchingRewriterRef = useRef(false);
  const mountedRef = useRef(true);

  const fetchConfig = useCallback(async () => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/llm/config`, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Admin access required to view LLM configuration.');
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to fetch LLM config: ${response.status}`);
      }

      const data: LLMConfig = await response.json();
      if (mountedRef.current) {
        setConfig(data);
        setLastFetched(new Date());
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
      fetchingRef.current = false;
    }
  }, []);

  const updateConfig = useCallback(
    async (request: LLMConfigUpdateRequest): Promise<LLMConfigUpdateResponse> => {
      setIsUpdating(true);
      setUpdateError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/admin/llm/config`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Authentication required. Please log in again.');
          }
          if (response.status === 403) {
            throw new Error('Admin access required to update LLM configuration.');
          }
          const errorData = await response.json().catch(() => null);
          throw new Error(errorData?.detail || `Failed to update LLM config: ${response.status}`);
        }

        const data: LLMConfigUpdateResponse = await response.json();

        // Update local config
        setConfig(data.config);
        setLastFetched(new Date());

        return data;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setUpdateError(error);
        throw error;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  const testHealth = useCallback(async (): Promise<LLMHealthResponse> => {
    setIsTestingHealth(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/llm/health`, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Admin access required to test LLM health.');
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to test LLM health: ${response.status}`);
      }

      const data: LLMHealthResponse = await response.json();
      setHealth(data);
      return data;
    } finally {
      setIsTestingHealth(false);
    }
  }, []);

  // Story 8-0: Fetch query rewriter model configuration
  const fetchRewriterModel = useCallback(async () => {
    if (fetchingRewriterRef.current) return;
    fetchingRewriterRef.current = true;
    setIsLoadingRewriterModel(true);
    setRewriterModelError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/config/rewriter-model`, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Admin access required to view rewriter model configuration.');
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || `Failed to fetch rewriter model config: ${response.status}`
        );
      }

      const data: RewriterModelResponse = await response.json();
      if (mountedRef.current) {
        setRewriterModelId(data.model_id);
      }
    } catch (err) {
      if (mountedRef.current) {
        setRewriterModelError(err instanceof Error ? err : new Error('Unknown error'));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoadingRewriterModel(false);
      }
      fetchingRewriterRef.current = false;
    }
  }, []);

  // Story 8-0: Update query rewriter model configuration
  const updateRewriterModel = useCallback(async (modelId: string | null): Promise<void> => {
    setIsUpdatingRewriterModel(true);
    setRewriterModelError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/config/rewriter-model`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ model_id: modelId }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        }
        if (response.status === 403) {
          throw new Error('Admin access required to update rewriter model configuration.');
        }
        const errorData = await response.json().catch(() => null);
        // Handle Pydantic validation errors (detail is an array) and FastAPI errors (detail is a string)
        let errorMessage = `Failed to update rewriter model config: ${response.status}`;
        if (errorData?.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors are arrays of objects with 'msg' field
            errorMessage = errorData.detail
              .map((e: { msg?: string }) => e.msg || 'Validation error')
              .join(', ');
          }
        }
        throw new Error(errorMessage);
      }

      const data: RewriterModelResponse = await response.json();
      setRewriterModelId(data.model_id);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setRewriterModelError(error);
      throw error;
    } finally {
      setIsUpdatingRewriterModel(false);
    }
  }, []);

  // Auto-fetch on mount and setup polling
  useEffect(() => {
    mountedRef.current = true;

    // Initial fetch
    if (!config && !isLoading && !error) {
      fetchConfig();
    }

    // Story 8-0: Also fetch rewriter model config
    if (rewriterModelId === undefined && !isLoadingRewriterModel && !rewriterModelError) {
      fetchRewriterModel();
    }

    // Setup polling for stale time (30 seconds)
    const intervalId = setInterval(() => {
      if (mountedRef.current && !fetchingRef.current && !isUpdating) {
        fetchConfig();
      }
    }, STALE_TIME_MS);

    return () => {
      mountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [
    config,
    isLoading,
    error,
    isUpdating,
    fetchConfig,
    rewriterModelId,
    isLoadingRewriterModel,
    rewriterModelError,
    fetchRewriterModel,
  ]);

  return {
    config,
    isLoading,
    error,
    updateConfig,
    isUpdating,
    updateError,
    health,
    isTestingHealth,
    testHealth,
    refetch: fetchConfig,
    lastFetched,
    // Story 8-0: Query Rewriter Model
    rewriterModelId,
    isLoadingRewriterModel,
    rewriterModelError,
    updateRewriterModel,
    isUpdatingRewriterModel,
    fetchRewriterModel,
  };
}
