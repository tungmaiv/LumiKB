/**
 * Unit tests for useModelRegistry hook
 * Story 7-9: LLM Model Registry (AC-7.9.4, AC-7.9.5, AC-7.9.6)
 *
 * Tests:
 * - Model listing with filters
 * - CRUD operations (create, update, delete)
 * - Set default model
 * - Connection testing
 * - Error handling
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ReactNode } from 'react';
import { useModelRegistry, useModel } from '../useModelRegistry';
import type {
  LLMModelSummary,
  LLMModelResponse,
  LLMModelList,
  ConnectionTestResult,
} from '@/types/llm-model';

// Mock fetch
global.fetch = vi.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
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

// Mock data
const mockEmbeddingModel: LLMModelSummary = {
  id: 'model-1',
  type: 'embedding',
  provider: 'openai',
  name: 'text-embedding-3-small',
  model_id: 'text-embedding-3-small',
  status: 'active',
  is_default: true,
  has_api_key: true,
};

const mockGenerationModel: LLMModelSummary = {
  id: 'model-2',
  type: 'generation',
  provider: 'anthropic',
  name: 'Claude 3 Sonnet',
  model_id: 'claude-3-sonnet',
  status: 'active',
  is_default: false,
  has_api_key: true,
};

const mockModelResponse: LLMModelResponse = {
  ...mockEmbeddingModel,
  config: { dimensions: 1536, max_tokens: 8192, normalize: true },
  api_endpoint: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockModelList: LLMModelList = {
  models: [mockEmbeddingModel, mockGenerationModel],
  total: 2,
};

describe('useModelRegistry', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('List Models', () => {
    it('should fetch models successfully', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockModelList,
      });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      // Assert
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(result.current.models).toEqual(mockModelList.models);
      expect(result.current.total).toBe(2);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/models'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
    });

    it('should fetch models with type filter', async () => {
      // Arrange
      const filteredList: LLMModelList = {
        models: [mockEmbeddingModel],
        total: 1,
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => filteredList,
      });

      // Act
      const { result } = renderHook(
        () => useModelRegistry({ type: 'embedding' }),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(result.current.models).toHaveLength(1);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('type=embedding'),
        expect.any(Object)
      );
    });

    it('should fetch models with provider filter', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ models: [mockEmbeddingModel], total: 1 }),
      });

      // Act
      const { result } = renderHook(
        () => useModelRegistry({ provider: 'openai' }),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('provider=openai'),
        expect.any(Object)
      );
    });

    it('should fetch models with status filter', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ models: [], total: 0 }),
      });

      // Act
      const { result } = renderHook(
        () => useModelRegistry({ status: 'deprecated' }),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=deprecated'),
        expect.any(Object)
      );
    });

    it('should handle 403 Forbidden error', async () => {
      // Arrange - mock twice because retry: 1
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      // Assert
      await waitFor(
        () => expect(result.current.error).not.toBeNull(),
        { timeout: 3000 }
      );
      expect(result.current.error?.message).toContain('Admin access required');
    });

    it('should handle 401 Unauthorized error', async () => {
      // Arrange - mock twice because retry: 1
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      // Assert
      await waitFor(
        () => expect(result.current.error).not.toBeNull(),
        { timeout: 3000 }
      );
      expect(result.current.error?.message).toContain('Authentication required');
    });
  });

  describe('Create Model', () => {
    it('should create model successfully', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelResponse,
        });

      const newModel = {
        type: 'embedding' as const,
        provider: 'openai' as const,
        name: 'New Model',
        model_id: 'new-model',
        config: { dimensions: 1536, max_tokens: 8192 },
      };

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Create model
      let createdModel: LLMModelResponse | undefined;
      await act(async () => {
        createdModel = await result.current.createModel(newModel);
      });

      // Assert
      expect(createdModel).toEqual(mockModelResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/models'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newModel),
        })
      );
    });

    it('should handle validation error on create', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid configuration' }),
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Assert
      await expect(
        act(async () => {
          await result.current.createModel({
            type: 'embedding',
            provider: 'openai',
            name: 'Test',
            model_id: 'test',
            config: {},
          });
        })
      ).rejects.toThrow('Invalid configuration');
    });
  });

  describe('Update Model', () => {
    it('should update model successfully', async () => {
      // Arrange
      const updatedModel = { ...mockModelResponse, name: 'Updated Name' };
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedModel,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let resultModel: LLMModelResponse | undefined;
      await act(async () => {
        resultModel = await result.current.updateModel('model-1', {
          name: 'Updated Name',
        });
      });

      // Assert
      expect(resultModel?.name).toBe('Updated Name');
    });

    it('should handle 404 error on update', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Assert
      await expect(
        act(async () => {
          await result.current.updateModel('non-existent', { name: 'Test' });
        })
      ).rejects.toThrow('Model not found');
    });
  });

  describe('Delete Model', () => {
    it('should delete model successfully', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.deleteModel('model-1');
      });

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/models/model-1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('should handle 404 error on delete', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Assert
      await expect(
        act(async () => {
          await result.current.deleteModel('non-existent');
        })
      ).rejects.toThrow('Model not found');
    });
  });

  describe('Set Default Model', () => {
    it('should set default model successfully', async () => {
      // Arrange
      const defaultModel = { ...mockModelResponse, is_default: true };
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => defaultModel,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let resultModel: LLMModelResponse | undefined;
      await act(async () => {
        resultModel = await result.current.setDefault('model-1');
      });

      // Assert
      expect(resultModel?.is_default).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/models/model-1/set-default'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('Test Connection', () => {
    it('should test connection successfully', async () => {
      // Arrange
      const testResult: ConnectionTestResult = {
        success: true,
        message: 'Connection successful',
        latency_ms: 150,
        details: { model_info: 'test' },
      };
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => testResult,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let connectionResult: ConnectionTestResult | undefined;
      await act(async () => {
        connectionResult = await result.current.testConnection('model-1');
      });

      // Assert
      expect(connectionResult?.success).toBe(true);
      expect(connectionResult?.latency_ms).toBe(150);
    });

    it('should handle failed connection test', async () => {
      // Arrange
      const testResult: ConnectionTestResult = {
        success: false,
        message: 'Connection refused',
        latency_ms: null,
        details: null,
      };
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => testResult,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let connectionResult: ConnectionTestResult | undefined;
      await act(async () => {
        connectionResult = await result.current.testConnection('model-1');
      });

      // Assert
      expect(connectionResult?.success).toBe(false);
      expect(connectionResult?.message).toBe('Connection refused');
    });
  });

  describe('Loading States', () => {
    it('should track creating state', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelResponse,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Start and complete creating
      await act(async () => {
        await result.current.createModel({
          type: 'embedding',
          provider: 'openai',
          name: 'Test',
          model_id: 'test',
          config: {},
        });
      });

      // After mutation completes, isCreating should be false
      expect(result.current.isCreating).toBe(false);
    });

    it('should track deleting state', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockModelList,
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Start and complete deleting
      await act(async () => {
        await result.current.deleteModel('model-1');
      });

      // After mutation completes, isDeleting should be false
      expect(result.current.isDeleting).toBe(false);
    });
  });

  describe('Refetch', () => {
    it('should refetch models when called', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => mockModelList,
      });

      // Act
      const { result } = renderHook(() => useModelRegistry(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isLoading).toBe(false));

      act(() => {
        result.current.refetch();
      });

      // Assert
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });
  });
});

describe('useModel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch single model by ID', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockModelResponse,
    });

    // Act
    const { result } = renderHook(() => useModel('model-1'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockModelResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/admin/models/model-1'),
      expect.any(Object)
    );
  });

  it('should not fetch when ID is null', async () => {
    // Act
    const { result } = renderHook(() => useModel(null), {
      wrapper: createWrapper(),
    });

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('should handle 404 error', async () => {
    // Arrange - mock twice because retry: 1
    (global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

    // Act
    const { result } = renderHook(() => useModel('non-existent'), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(
      () => expect(result.current.isError).toBe(true),
      { timeout: 3000 }
    );
    expect(result.current.error?.message).toContain('Model not found');
  });
});
