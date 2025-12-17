/**
 * Unit tests for useLLMConfig hook
 * Story 7-2: Centralized LLM Configuration (AC-7.2.1 through AC-7.2.4)
 *
 * Tests:
 * - Fetching LLM configuration
 * - Updating LLM configuration with hot-reload
 * - Testing model health status
 * - Error handling for API calls
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useLLMConfig } from '../useLLMConfig';
import type { LLMConfig, LLMConfigUpdateResponse, LLMHealthResponse } from '@/types/llm-config';

// Mock fetch
global.fetch = vi.fn();

// Mock data
const mockConfig: LLMConfig = {
  embedding_model: {
    model_id: 'emb-001',
    name: 'text-embedding-3-small',
    provider: 'openai',
    model_identifier: 'text-embedding-3-small',
    api_endpoint: null,
    is_default: true,
    status: 'active',
  },
  generation_model: {
    model_id: 'gen-001',
    name: 'Claude 3 Sonnet',
    provider: 'anthropic',
    model_identifier: 'claude-3-sonnet',
    api_endpoint: null,
    is_default: true,
    status: 'active',
  },
  generation_settings: {
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 1.0,
  },
  litellm_base_url: 'http://localhost:4000',
  last_modified: '2024-01-15T10:30:00Z',
  last_modified_by: 'admin@example.com',
};

const mockUpdateResponse: LLMConfigUpdateResponse = {
  config: {
    ...mockConfig,
    generation_settings: {
      ...mockConfig.generation_settings,
      temperature: 0.5,
    },
  },
  hot_reload_applied: true,
  dimension_warning: null,
};

const mockHealthResponse: LLMHealthResponse = {
  embedding_health: {
    model_type: 'embedding',
    model_name: 'text-embedding-3-small',
    is_healthy: true,
    latency_ms: 150,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  generation_health: {
    model_type: 'generation',
    model_name: 'Claude 3 Sonnet',
    is_healthy: true,
    latency_ms: 320,
    error_message: null,
    last_checked: '2024-01-15T10:35:00Z',
  },
  overall_healthy: true,
};

describe('useLLMConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Initial Fetch', () => {
    it('should fetch config on mount', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());

      // Assert - wait for initial fetch
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(result.current.config).toEqual(mockConfig);
      expect(result.current.error).toBeNull();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/llm/config'),
        expect.objectContaining({
          credentials: 'include',
        })
      );

      unmount();
    });

    it('should set lastFetched after successful fetch', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());

      // Assert
      await waitFor(() => expect(result.current.lastFetched).not.toBeNull());
      expect(result.current.lastFetched).toBeInstanceOf(Date);

      unmount();
    });

    it('should handle 401 Unauthorized error', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());

      // Assert
      await waitFor(() => expect(result.current.error).not.toBeNull());
      expect(result.current.error?.message).toContain('Authentication required');

      unmount();
    });

    it('should handle 403 Forbidden error', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());

      // Assert
      await waitFor(() => expect(result.current.error).not.toBeNull());
      expect(result.current.error?.message).toContain('Admin access required');

      unmount();
    });

    it('should handle generic error with detail', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());

      // Assert
      await waitFor(() => expect(result.current.error).not.toBeNull());
      expect(result.current.error?.message).toContain('Internal server error');

      unmount();
    });
  });

  describe('Update Config', () => {
    it('should update config successfully', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdateResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let updateResult: LLMConfigUpdateResponse | undefined;
      await act(async () => {
        updateResult = await result.current.updateConfig({
          generation_settings: { temperature: 0.5 },
        });
      });

      // Assert
      expect(updateResult?.hot_reload_applied).toBe(true);
      expect(result.current.config?.generation_settings.temperature).toBe(0.5);
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/v1/admin/llm/config'),
        expect.objectContaining({
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      unmount();
    });

    it('should update embedding model ID', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdateResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.updateConfig({ embedding_model_id: 'new-emb-001' });
      });

      // Assert
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ embedding_model_id: 'new-emb-001' }),
        })
      );

      unmount();
    });

    it('should handle update error', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid model ID' }),
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Assert - call updateConfig and expect it to throw
      let caughtError: unknown = null;
      await act(async () => {
        try {
          await result.current.updateConfig({ embedding_model_id: 'invalid' });
        } catch (err) {
          caughtError = err;
        }
      });

      expect(caughtError).not.toBeNull();
      expect(caughtError).toBeInstanceOf(Error);
      expect((caughtError as Error).message).toContain('Invalid model ID');
      expect(result.current.updateError).not.toBeNull();
      expect(result.current.updateError?.message).toContain('Invalid model ID');

      unmount();
    });

    it('should track isUpdating state', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdateResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Start update
      await act(async () => {
        await result.current.updateConfig({ generation_settings: { temperature: 0.5 } });
      });

      // After update completes, isUpdating should be false
      expect(result.current.isUpdating).toBe(false);

      unmount();
    });
  });

  describe('Test Health', () => {
    it('should test health successfully', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHealthResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let healthResult: LLMHealthResponse | undefined;
      await act(async () => {
        healthResult = await result.current.testHealth();
      });

      // Assert
      expect(healthResult?.overall_healthy).toBe(true);
      expect(healthResult?.embedding_health?.is_healthy).toBe(true);
      expect(healthResult?.generation_health?.is_healthy).toBe(true);
      expect(result.current.health).toEqual(mockHealthResponse);

      unmount();
    });

    it('should handle unhealthy model', async () => {
      // Arrange
      const unhealthyResponse: LLMHealthResponse = {
        embedding_health: {
          model_type: 'embedding',
          model_name: 'text-embedding-3-small',
          is_healthy: false,
          latency_ms: null,
          error_message: 'Connection refused',
          last_checked: '2024-01-15T10:35:00Z',
        },
        generation_health: mockHealthResponse.generation_health,
        overall_healthy: false,
      };

      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => unhealthyResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let healthResult: LLMHealthResponse | undefined;
      await act(async () => {
        healthResult = await result.current.testHealth();
      });

      // Assert
      expect(healthResult?.overall_healthy).toBe(false);
      expect(healthResult?.embedding_health?.error_message).toBe('Connection refused');

      unmount();
    });

    it('should handle health check error', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Health check failed' }),
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Assert
      await expect(
        act(async () => {
          await result.current.testHealth();
        })
      ).rejects.toThrow('Health check failed');

      unmount();
    });

    it('should track isTestingHealth state', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHealthResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      await act(async () => {
        await result.current.testHealth();
      });

      // After health check completes, isTestingHealth should be false
      expect(result.current.isTestingHealth).toBe(false);

      unmount();
    });
  });

  describe('Refetch', () => {
    it('should refetch config when called', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockConfig,
            generation_settings: { ...mockConfig.generation_settings, temperature: 0.9 },
          }),
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));
      expect(result.current.config?.generation_settings.temperature).toBe(0.7);

      await act(async () => {
        await result.current.refetch();
      });

      // Assert - should have called twice (initial + refetch)
      expect(global.fetch).toHaveBeenCalledTimes(2);

      unmount();
    });
  });

  describe('Dimension Mismatch Warning', () => {
    it('should return dimension warning in update response', async () => {
      // Arrange
      const warningResponse: LLMConfigUpdateResponse = {
        config: mockConfig,
        hot_reload_applied: true,
        dimension_warning: {
          has_mismatch: true,
          current_dimensions: 768,
          new_dimensions: 1536,
          affected_kbs: ['KB-001', 'KB-002'],
          warning_message: 'Dimension mismatch detected',
        },
      };

      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => warningResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let updateResult: LLMConfigUpdateResponse | undefined;
      await act(async () => {
        updateResult = await result.current.updateConfig({ embedding_model_id: 'new-emb' });
      });

      // Assert
      expect(updateResult?.dimension_warning?.has_mismatch).toBe(true);
      expect(updateResult?.dimension_warning?.affected_kbs).toHaveLength(2);

      unmount();
    });
  });

  describe('Hot Reload', () => {
    it('should indicate hot_reload_applied in response', async () => {
      // Arrange
      (global.fetch as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockConfig,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdateResponse,
        });

      // Act
      const { result, unmount } = renderHook(() => useLLMConfig());
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      let updateResult: LLMConfigUpdateResponse | undefined;
      await act(async () => {
        updateResult = await result.current.updateConfig({
          generation_settings: { temperature: 0.5 },
        });
      });

      // Assert
      expect(updateResult?.hot_reload_applied).toBe(true);

      unmount();
    });
  });
});
