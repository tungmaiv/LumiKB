/**
 * Unit tests for LLM Usage Widget.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * RED PHASE: All tests are designed to FAIL until implementation is complete.
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { useRouter } from "next/navigation";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

// Mock data factory
function createLLMUsageData(overrides = {}) {
  return {
    totalTokens: 125000,
    promptTokens: 100000,
    completionTokens: 25000,
    totalCostUsd: 5.75,
    byModel: [
      { model: "gpt-4", tokens: 80000, cost: 4.0 },
      { model: "gpt-3.5-turbo", tokens: 45000, cost: 1.75 },
    ],
    trend: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
      value: Math.floor(Math.random() * 1000) + 500,
    })),
    ...overrides,
  };
}

// Test wrapper with providers
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("LLMUsageWidget", () => {
  const mockRouter = { push: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
  });

  describe("AC1: Displays total tokens and cost", () => {
    it("renders_total_tokens_and_cost", async () => {
      const data = createLLMUsageData();

      // This will fail until LLMUsageWidget is implemented
      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("llm-total-tokens")).toBeInTheDocument();
        expect(screen.getByTestId("llm-total-cost")).toBeInTheDocument();
      });

      expect(screen.getByTestId("llm-total-tokens")).toHaveTextContent(
        "125,000"
      );
      expect(screen.getByTestId("llm-total-cost")).toHaveTextContent("$5.75");
    });

    it("renders_model_breakdown_table", async () => {
      const data = createLLMUsageData();

      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("llm-model-breakdown")).toBeInTheDocument();
      });

      // Should show model names
      expect(screen.getByText("gpt-4")).toBeInTheDocument();
      expect(screen.getByText("gpt-3.5-turbo")).toBeInTheDocument();
    });

    it("formats_large_numbers_correctly", async () => {
      const data = createLLMUsageData({ totalTokens: 1250000 });

      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("llm-total-tokens")).toHaveTextContent(
          "1,250,000"
        );
      });
    });
  });

  describe("AC7: Sparkline charts for trends", () => {
    it("renders_sparkline_for_trend", async () => {
      const data = createLLMUsageData();

      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("llm-sparkline")).toBeInTheDocument();
      });
    });

    it("sparkline_shows_correct_data_points", async () => {
      const trend = Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
        value: i * 100,
      }));
      const data = createLLMUsageData({ trend });

      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        const sparkline = screen.getByTestId("llm-sparkline");
        expect(
          sparkline.querySelector("svg") || sparkline.querySelector("canvas")
        ).toBeInTheDocument();
      });
    });
  });

  describe("AC8: Click navigation", () => {
    it("navigates_to_trace_view_on_click", async () => {
      const data = createLLMUsageData();

      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("llm-usage-widget")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId("llm-usage-widget"));

      expect(mockRouter.push).toHaveBeenCalledWith("/admin/observability/llm");
    });
  });

  describe("Loading and error states", () => {
    it("shows_loading_skeleton_when_loading", async () => {
      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(<LLMUsageWidget data={null} period="day" isLoading />);

      expect(screen.getByTestId("llm-usage-widget-skeleton")).toBeInTheDocument();
    });

    it("shows_error_state_on_error", async () => {
      const LLMUsageWidget = await import("../llm-usage-widget").then(
        (m) => m.LLMUsageWidget
      );

      renderWithProviders(
        <LLMUsageWidget data={null} period="day" error="Failed to load" />
      );

      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });
});
