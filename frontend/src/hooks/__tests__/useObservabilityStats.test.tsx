/**
 * Unit tests for useObservabilityStats hook.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * RED PHASE: All tests are designed to FAIL until implementation is complete.
 */

import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import React from "react";

// Mock fetch
global.fetch = vi.fn();

// Test wrapper with providers
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// Mock API response
function createMockStatsResponse() {
  return {
    llmUsage: {
      totalTokens: 125000,
      promptTokens: 100000,
      completionTokens: 25000,
      totalCostUsd: 5.75,
      byModel: [
        { model: "gpt-4", tokens: 80000, cost: 4.0 },
        { model: "gpt-3.5-turbo", tokens: 45000, cost: 1.75 },
      ],
      trend: [],
    },
    processingPipeline: {
      documentsProcessed: 127,
      avgProcessingTimeMs: 8500,
      errorRate: 2.3,
      trend: [],
    },
    chatActivity: {
      messageCount: 423,
      activeSessionCount: 45,
      avgResponseTimeMs: 850,
      trend: [],
    },
    systemHealth: {
      traceSuccessRate: 98.5,
      p95LatencyMs: 450,
      errorCount: 12,
      trend: [],
    },
  };
}

describe("useObservabilityStats", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("AC5: Period parameter passed to API", () => {
    it("fetches_stats_for_selected_period", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      // This will fail until useObservabilityStats is implemented
      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "week" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=week"),
        expect.any(Object)
      );
    });

    it("refetches_when_period_changes", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result, rerender } = renderHook(
        ({ period }) => useObservabilityStats({ period }),
        {
          wrapper: createWrapper(),
          initialProps: { period: "day" as const },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      rerender({ period: "week" as const });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe("AC6: Auto-refresh every 30s", () => {
    it("auto_refreshes_at_configured_interval", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day", refreshInterval: 30000 }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // First fetch
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Advance time by 30 seconds
      act(() => {
        vi.advanceTimersByTime(30000);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });

    it("manual_refresh_triggers_refetch", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Manual refresh
      act(() => {
        result.current.refetch();
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe("AC9: Independent widget loading", () => {
    it("handles_parallel_widget_fetching", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should have data for all widget types
      expect(result.current.data?.llmUsage).toBeDefined();
      expect(result.current.data?.processingPipeline).toBeDefined();
      expect(result.current.data?.chatActivity).toBeDefined();
      expect(result.current.data?.systemHealth).toBeDefined();
    });

    it("handles_individual_widget_errors", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("Network error")
      );

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeDefined();
    });

    it("provides_loading_state_per_widget", async () => {
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as ReturnType<typeof vi.fn>).mockReturnValueOnce(promise);

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day" }),
        { wrapper: createWrapper() }
      );

      // Should be loading initially
      expect(result.current.isLoading).toBe(true);

      // Resolve the promise
      act(() => {
        resolvePromise!({
          ok: true,
          json: async () => createMockStatsResponse(),
        });
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe("Data transformation", () => {
    it("transforms_api_response_to_widget_format", async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => createMockStatsResponse(),
      });

      const { useObservabilityStats } = await import(
        "../../useObservabilityStats"
      );

      const { result } = renderHook(
        () => useObservabilityStats({ period: "day" }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const data = result.current.data;
      expect(data?.llmUsage.totalTokens).toBe(125000);
      expect(data?.processingPipeline.documentsProcessed).toBe(127);
      expect(data?.chatActivity.messageCount).toBe(423);
      expect(data?.systemHealth.traceSuccessRate).toBe(98.5);
    });
  });
});
