/**
 * Unit tests for Time Period Selector.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * RED PHASE: All tests are designed to FAIL until implementation is complete.
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

describe("TimePeriodSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC5: Time period selector (hour/day/week/month)", () => {
    it("renders_all_period_options", async () => {
      // This will fail until TimePeriodSelector is implemented
      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(
        <TimePeriodSelector value="day" onChange={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByTestId("time-period-selector")).toBeInTheDocument();
      });

      expect(screen.getByTestId("period-option-hour")).toBeInTheDocument();
      expect(screen.getByTestId("period-option-day")).toBeInTheDocument();
      expect(screen.getByTestId("period-option-week")).toBeInTheDocument();
      expect(screen.getByTestId("period-option-month")).toBeInTheDocument();
    });

    it("calls_onChange_when_period_selected", async () => {
      const onChange = vi.fn();

      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(<TimePeriodSelector value="day" onChange={onChange} />);

      await waitFor(() => {
        expect(screen.getByTestId("period-option-week")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId("period-option-week"));

      expect(onChange).toHaveBeenCalledWith("week");
    });

    it("highlights_current_selection", async () => {
      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(<TimePeriodSelector value="day" onChange={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByTestId("period-option-day")).toHaveAttribute(
          "data-active",
          "true"
        );
      });
    });

    it("displays_human_readable_labels", async () => {
      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(<TimePeriodSelector value="day" onChange={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Hour")).toBeInTheDocument();
        expect(screen.getByText("Day")).toBeInTheDocument();
        expect(screen.getByText("Week")).toBeInTheDocument();
        expect(screen.getByText("Month")).toBeInTheDocument();
      });
    });
  });

  describe("Keyboard navigation", () => {
    it("supports_keyboard_navigation", async () => {
      const onChange = vi.fn();

      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(<TimePeriodSelector value="day" onChange={onChange} />);

      await waitFor(() => {
        expect(screen.getByTestId("period-option-day")).toBeInTheDocument();
      });

      const dayOption = screen.getByTestId("period-option-day");
      fireEvent.keyDown(dayOption, { key: "ArrowRight" });

      expect(onChange).toHaveBeenCalledWith("week");
    });
  });

  describe("Accessibility", () => {
    it("has_proper_aria_labels", async () => {
      const TimePeriodSelector = await import("../time-period-selector").then(
        (m) => m.TimePeriodSelector
      );

      render(<TimePeriodSelector value="day" onChange={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByTestId("time-period-selector")).toHaveAttribute(
          "role",
          "radiogroup"
        );
      });

      expect(screen.getByTestId("period-option-day")).toHaveAttribute(
        "role",
        "radio"
      );
    });
  });
});
