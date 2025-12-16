/**
 * Unit tests for System Health Widget.
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
function createSystemHealthData(overrides = {}) {
  return {
    traceSuccessRate: 98.5,
    p95LatencyMs: 450,
    errorCount: 12,
    trend: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
      value: 95 + Math.random() * 5,
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

describe("SystemHealthWidget", () => {
  const mockRouter = { push: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
  });

  describe("AC4: Trace success rate and p95 latency", () => {
    it("renders_trace_success_rate", async () => {
      const data = createSystemHealthData();

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-success-rate")).toBeInTheDocument();
      });

      expect(screen.getByTestId("health-success-rate")).toHaveTextContent(
        "98.5%"
      );
    });

    it("renders_p95_latency", async () => {
      const data = createSystemHealthData();

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-p95-latency")).toBeInTheDocument();
      });

      expect(screen.getByTestId("health-p95-latency")).toHaveTextContent(
        "450ms"
      );
    });

    it("renders_error_count", async () => {
      const data = createSystemHealthData();

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-error-count")).toBeInTheDocument();
      });

      expect(screen.getByTestId("health-error-count")).toHaveTextContent("12");
    });

    it("shows_healthy_indicator_for_high_success_rate", async () => {
      const data = createSystemHealthData({ traceSuccessRate: 99.9 });

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-status-indicator")).toHaveClass(
          "text-green-500"
        );
      });
    });

    it("shows_warning_indicator_for_degraded_success_rate", async () => {
      const data = createSystemHealthData({ traceSuccessRate: 92.5 });

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-status-indicator")).toHaveClass(
          "text-yellow-500"
        );
      });
    });

    it("shows_critical_indicator_for_low_success_rate", async () => {
      const data = createSystemHealthData({ traceSuccessRate: 85.0 });

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-status-indicator")).toHaveClass(
          "text-destructive"
        );
      });
    });
  });

  describe("AC7: Sparkline charts for trends", () => {
    it("renders_sparkline_for_trend", async () => {
      const data = createSystemHealthData();

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("health-sparkline")).toBeInTheDocument();
      });
    });
  });

  describe("AC8: Click navigation", () => {
    it("navigates_to_system_metrics_on_click", async () => {
      const data = createSystemHealthData();

      const SystemHealthWidget = await import("../system-health-widget").then(
        (m) => m.SystemHealthWidget
      );

      renderWithProviders(<SystemHealthWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("system-health-widget")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId("system-health-widget"));

      expect(mockRouter.push).toHaveBeenCalledWith(
        "/admin/observability/system"
      );
    });
  });
});
