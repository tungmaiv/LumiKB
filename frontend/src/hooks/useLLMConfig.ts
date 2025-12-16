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

  // Track if initial fetch is in progress to prevent duplicate calls
  const fetchingRef = useRef(false);
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
        throw new Error(
          errorData?.detail || `Failed to fetch LLM config: ${response.status}`
        );
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
          throw new Error(
            errorData?.detail || `Failed to update LLM config: ${response.status}`
          );
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
        throw new Error(
          errorData?.detail || `Failed to test LLM health: ${response.status}`
        );
      }

      const data: LLMHealthResponse = await response.json();
      setHealth(data);
      return data;
    } finally {
      setIsTestingHealth(false);
    }
  }, []);

  // Auto-fetch on mount and setup polling
  useEffect(() => {
    mountedRef.current = true;

    // Initial fetch
    if (!config && !isLoading && !error) {
      fetchConfig();
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
  }, [config, isLoading, error, isUpdating, fetchConfig]);

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
  };
}
