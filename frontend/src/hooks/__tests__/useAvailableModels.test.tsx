/**
 * Tests for useAvailableModels hook
 * Story 7-10: KB Model Configuration (AC-7.10.1, 7.10.6)
 *
 * Tests the hook that fetches available models from the Model Registry
 * for KB owners to select during KB creation and settings.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useAvailableModels } from '../useAvailableModels';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Test data factories
function createEmbeddingModel(overrides = {}) {
  return {
    id: 'emb-model-1',
    name: 'text-embedding-3-small',
    model_id: 'text-embedding-3-small',
    model_type: 'embedding',
    is_active: true,
    ...overrides,
  };
}

function createGenerationModel(overrides = {}) {
  return {
    id: 'gen-model-1',
    name: 'gpt-4o-mini',
    model_id: 'gpt-4o-mini',
    model_type: 'generation',
    is_active: true,
    ...overrides,
  };
}

function createNerModel(overrides = {}) {
  return {
    id: 'ner-model-1',
    name: 'gpt-4o-ner',
    model_id: 'gpt-4o',
    model_type: 'ner',
    is_active: true,
    ...overrides,
  };
}

// Create wrapper with fresh QueryClient for each test
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useAvailableModels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Story 7-10: Model Fetching (AC-7.10.1, 7.10.6)', () => {
    it('should return empty arrays while loading', () => {
      /**
       * GIVEN: Hook is called before fetch completes
       * WHEN: Rendering the hook
       * THEN: Returns empty arrays and isLoading=true
       * AC: 7.10.6 - Model dropdown shows loading state
       */
      mockFetch.mockImplementation(
        () =>
          new Promise(() => {
            /* never resolves */
          })
      );

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      expect(result.current.embeddingModels).toEqual([]);
      expect(result.current.generationModels).toEqual([]);
      expect(result.current.nerModels).toEqual([]);
      expect(result.current.isLoading).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should fetch and return available models successfully', async () => {
      /**
       * GIVEN: API returns available models response
       * WHEN: Hook completes fetching
       * THEN: Returns categorized model arrays
       * AC: 7.10.1 - Model selection shows active models from registry
       */
      const mockResponse = {
        embedding_models: [
          createEmbeddingModel({ id: 'emb-1', name: 'Embedding Model 1' }),
          createEmbeddingModel({ id: 'emb-2', name: 'Embedding Model 2' }),
        ],
        generation_models: [
          createGenerationModel({ id: 'gen-1', name: 'Generation Model 1' }),
        ],
        ner_models: [createNerModel({ id: 'ner-1', name: 'NER Model 1' })],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.embeddingModels).toHaveLength(2);
      expect(result.current.generationModels).toHaveLength(1);
      expect(result.current.nerModels).toHaveLength(1);
      expect(result.current.error).toBeNull();
    });

    it('should call correct API endpoint with credentials', async () => {
      /**
       * GIVEN: Hook is rendered
       * WHEN: Fetch is called
       * THEN: Calls /api/v1/models/available with correct options
       * AC: 7.10.1 - Fetches from Model Registry endpoint
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          embedding_models: [],
          generation_models: [],
          ner_models: [],
        }),
      });

      renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/models/available'),
          expect.objectContaining({
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
          })
        );
      });
    });

    it('should handle empty model lists gracefully', async () => {
      /**
       * GIVEN: API returns empty arrays for all model types
       * WHEN: Hook completes fetching
       * THEN: Returns empty arrays without errors
       * AC: 7.10.6 - Handles no active models scenario
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          embedding_models: [],
          generation_models: [],
          ner_models: [],
        }),
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.embeddingModels).toEqual([]);
      expect(result.current.generationModels).toEqual([]);
      expect(result.current.nerModels).toEqual([]);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Story 7-10: Error Handling', () => {
    it('should handle authentication error (401)', async () => {
      /**
       * GIVEN: User is not authenticated
       * WHEN: API returns 401
       * THEN: Returns authentication required error
       * AC: 7.10.6 - Proper error handling for auth failures
       */
      // Use mockResolvedValue (not Once) since retry=1 means 2 calls
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.error?.message).toBe('Authentication required');
      expect(result.current.embeddingModels).toEqual([]);
      expect(result.current.generationModels).toEqual([]);
    });

    it('should handle server error (500)', async () => {
      /**
       * GIVEN: Server encounters an error
       * WHEN: API returns 500
       * THEN: Returns appropriate error message
       * AC: 7.10.6 - Proper error handling for server failures
       */
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.error?.message).toContain('Failed to fetch');
    });

    it('should handle network error', async () => {
      /**
       * GIVEN: Network is unavailable
       * WHEN: Fetch throws network error
       * THEN: Returns error state
       * AC: 7.10.6 - Handles network failures gracefully
       */
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Story 7-10: Refetch Functionality', () => {
    it('should provide refetch function', async () => {
      /**
       * GIVEN: Hook has completed initial fetch
       * WHEN: refetch is called
       * THEN: Fetches fresh data from API
       * AC: 7.10.6 - Supports manual refresh of model list
       */
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          embedding_models: [createEmbeddingModel()],
          generation_models: [],
          ner_models: [],
        }),
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(typeof result.current.refetch).toBe('function');

      // Call refetch
      result.current.refetch();

      await waitFor(() => {
        // Should have been called at least twice (initial + refetch)
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Story 7-10: Model Data Structure', () => {
    it('should return models with required fields for display', async () => {
      /**
       * GIVEN: API returns models with full details
       * WHEN: Hook completes fetching
       * THEN: Models have id and name for dropdown display
       * AC: 7.10.3 - Model info displayed in selection dropdown
       */
      const embeddingModel = createEmbeddingModel({
        id: 'test-emb-uuid',
        name: 'OpenAI text-embedding-3-small',
        model_id: 'text-embedding-3-small',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          embedding_models: [embeddingModel],
          generation_models: [],
          ner_models: [],
        }),
      });

      const { result } = renderHook(() => useAvailableModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const model = result.current.embeddingModels[0];
      expect(model).toHaveProperty('id', 'test-emb-uuid');
      expect(model).toHaveProperty('name', 'OpenAI text-embedding-3-small');
      expect(model).toHaveProperty('model_id', 'text-embedding-3-small');
    });
  });
});
