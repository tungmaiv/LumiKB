/**
 * E2E tests for Observability Dashboard.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * RED PHASE: All tests are designed to FAIL until implementation is complete.
 */

import { test, expect } from "@playwright/test";

test.describe("Observability Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "admin@lumikb.local");
    await page.fill('[data-testid="password-input"]', "adminpass123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL(/dashboard/);
  });

  test.describe("AC8: Widget click navigation", () => {
    test("navigates_to_trace_view_from_llm_widget", async ({ page }) => {
      // Navigate to admin observability dashboard
      await page.goto("/admin/observability");

      // Wait for dashboard to load
      await expect(page.getByTestId("observability-dashboard")).toBeVisible();

      // Click on LLM usage widget
      await page.getByTestId("llm-usage-widget").click();

      // Should navigate to trace view
      await expect(page).toHaveURL(/\/admin\/observability\/llm/);
    });

    test("navigates_to_document_timeline_from_processing_widget", async ({
      page,
    }) => {
      await page.goto("/admin/observability");

      await expect(page.getByTestId("observability-dashboard")).toBeVisible();

      // Click on processing widget
      await page.getByTestId("processing-widget").click();

      // Should navigate to document timeline
      await expect(page).toHaveURL(/\/admin\/observability\/documents/);
    });

    test("navigates_to_chat_history_from_chat_widget", async ({ page }) => {
      await page.goto("/admin/observability");

      await expect(page.getByTestId("observability-dashboard")).toBeVisible();

      // Click on chat activity widget
      await page.getByTestId("chat-activity-widget").click();

      // Should navigate to chat history
      await expect(page).toHaveURL(/\/admin\/observability\/chat/);
    });

    test("navigates_to_trace_list_from_health_widget", async ({ page }) => {
      await page.goto("/admin/observability");

      await expect(page.getByTestId("observability-dashboard")).toBeVisible();

      // Click on system health widget
      await page.getByTestId("system-health-widget").click();

      // Should navigate to trace list
      await expect(page).toHaveURL(/\/admin\/observability\/traces/);
    });
  });

  test.describe("AC5: Time period selection", () => {
    test("period_selector_shows_all_options", async ({ page }) => {
      await page.goto("/admin/observability");

      // Click time period selector
      await page.getByTestId("time-period-selector").click();

      // Should show all period options
      await expect(page.getByRole("option", { name: "Last Hour" })).toBeVisible();
      await expect(page.getByRole("option", { name: "Today" })).toBeVisible();
      await expect(page.getByRole("option", { name: "This Week" })).toBeVisible();
      await expect(page.getByRole("option", { name: "This Month" })).toBeVisible();
    });

    test("changing_period_updates_widgets", async ({ page }) => {
      await page.goto("/admin/observability");

      // Wait for initial load
      await expect(page.getByTestId("llm-usage-widget")).toBeVisible();

      // Change to week view
      await page.getByTestId("time-period-selector").click();
      await page.getByRole("option", { name: "This Week" }).click();

      // Widgets should update (show loading state briefly)
      // Then show updated data
      await expect(page.getByTestId("llm-usage-widget")).not.toHaveAttribute(
        "data-loading",
        "true"
      );
    });
  });

  test.describe("AC6: Auto-refresh", () => {
    test("refresh_button_reloads_data", async ({ page }) => {
      await page.goto("/admin/observability");

      await expect(page.getByTestId("observability-dashboard")).toBeVisible();

      // Find and click refresh button
      await page.getByTestId("refresh-button").click();

      // Should show loading state
      await expect(page.getByTestId("llm-usage-widget")).toHaveAttribute(
        "data-loading",
        "true"
      );

      // Then complete loading
      await expect(page.getByTestId("llm-usage-widget")).not.toHaveAttribute(
        "data-loading",
        "true",
        { timeout: 5000 }
      );
    });
  });

  test.describe("Widget data display", () => {
    test("all_widgets_render_on_dashboard", async ({ page }) => {
      await page.goto("/admin/observability");

      // All four widgets should be visible
      await expect(page.getByTestId("llm-usage-widget")).toBeVisible();
      await expect(page.getByTestId("processing-widget")).toBeVisible();
      await expect(page.getByTestId("chat-activity-widget")).toBeVisible();
      await expect(page.getByTestId("system-health-widget")).toBeVisible();
    });

    test("llm_widget_shows_token_and_cost", async ({ page }) => {
      await page.goto("/admin/observability");

      const widget = page.getByTestId("llm-usage-widget");
      await expect(widget).toBeVisible();

      // Should show total tokens
      await expect(widget.getByTestId("llm-total-tokens")).toBeVisible();

      // Should show total cost
      await expect(widget.getByTestId("llm-total-cost")).toBeVisible();
    });

    test("processing_widget_shows_metrics", async ({ page }) => {
      await page.goto("/admin/observability");

      const widget = page.getByTestId("processing-widget");
      await expect(widget).toBeVisible();

      // Should show documents processed
      await expect(widget.getByTestId("processing-docs-count")).toBeVisible();

      // Should show error rate
      await expect(widget.getByTestId("processing-error-rate")).toBeVisible();
    });

    test("chat_widget_shows_activity", async ({ page }) => {
      await page.goto("/admin/observability");

      const widget = page.getByTestId("chat-activity-widget");
      await expect(widget).toBeVisible();

      // Should show message count
      await expect(widget.getByTestId("chat-message-count")).toBeVisible();

      // Should show active sessions
      await expect(widget.getByTestId("chat-active-sessions")).toBeVisible();
    });

    test("health_widget_shows_status", async ({ page }) => {
      await page.goto("/admin/observability");

      const widget = page.getByTestId("system-health-widget");
      await expect(widget).toBeVisible();

      // Should show success rate
      await expect(widget.getByTestId("health-success-rate")).toBeVisible();

      // Should show health indicator
      await expect(widget.getByTestId("health-status-indicator")).toBeVisible();
    });
  });
});
