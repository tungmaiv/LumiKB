/**
 * Unit tests for Chat Activity Widget.
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
function createChatActivityData(overrides = {}) {
  return {
    messageCount: 423,
    activeSessionCount: 45,
    avgResponseTimeMs: 850,
    trend: Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
      value: Math.floor(Math.random() * 50) + 10,
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

describe("ChatActivityWidget", () => {
  const mockRouter = { push: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
  });

  describe("AC3: Messages today, active sessions, avg response time", () => {
    it("renders_message_count", async () => {
      const data = createChatActivityData();

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-message-count")).toBeInTheDocument();
      });

      expect(screen.getByTestId("chat-message-count")).toHaveTextContent("423");
    });

    it("renders_active_sessions", async () => {
      const data = createChatActivityData();

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-active-sessions")).toBeInTheDocument();
      });

      expect(screen.getByTestId("chat-active-sessions")).toHaveTextContent(
        "45"
      );
    });

    it("renders_avg_response_time", async () => {
      const data = createChatActivityData();

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(
          screen.getByTestId("chat-avg-response-time")
        ).toBeInTheDocument();
      });

      expect(screen.getByTestId("chat-avg-response-time")).toHaveTextContent(
        "850ms"
      );
    });

    it("formats_response_time_in_seconds_when_over_1000ms", async () => {
      const data = createChatActivityData({ avgResponseTimeMs: 2500 });

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-avg-response-time")).toHaveTextContent(
          "2.5s"
        );
      });
    });
  });

  describe("AC7: Sparkline charts for trends", () => {
    it("renders_sparkline_for_trend", async () => {
      const data = createChatActivityData();

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-sparkline")).toBeInTheDocument();
      });
    });
  });

  describe("AC8: Click navigation", () => {
    it("navigates_to_chat_history_on_click", async () => {
      const data = createChatActivityData();

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-activity-widget")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId("chat-activity-widget"));

      expect(mockRouter.push).toHaveBeenCalledWith("/admin/observability/chat");
    });
  });

  describe("Edge cases", () => {
    it("handles_zero_active_sessions", async () => {
      const data = createChatActivityData({
        activeSessionCount: 0,
        messageCount: 0,
      });

      const ChatActivityWidget = await import("../chat-activity-widget").then(
        (m) => m.ChatActivityWidget
      );

      renderWithProviders(<ChatActivityWidget data={data} period="day" />);

      await waitFor(() => {
        expect(screen.getByTestId("chat-active-sessions")).toHaveTextContent(
          "0"
        );
      });
    });
  });
});
