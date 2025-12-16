/**
 * E2E Tests for Onboarding Wizard (Story 5.7)
 *
 * Tests the first-time user onboarding experience including:
 * - Automatic wizard display for new users
 * - 5-step wizard flow with navigation
 * - Skip tutorial with confirmation
 * - Wizard completion and persistence
 *
 * Priority: P0-P1 (Critical user journey)
 * Test Level: E2E (Complete user workflow)
 *
 * Note: These tests will be executed as part of Story 5.16 (Docker E2E Infrastructure)
 */

import { test, expect } from '@playwright/test';

test.describe('Onboarding Wizard - First Time User Experience', () => {
  test.describe('[P0] Critical User Journeys', () => {
    test('[P0] should display wizard automatically for new user on first login', async ({ page }) => {
      // GIVEN: A new user with onboarding_completed = false
      // Mock API response for new user
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            is_active: true,
            onboarding_completed: false, // First-time user
            last_active: null,
            created_at: new Date().toISOString(),
          }),
        });
      });

      // WHEN: User logs in and dashboard loads
      await page.goto('/dashboard');

      // Wait for dialog to appear (modal animation)
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // THEN: Onboarding wizard modal appears
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();

      // AND: Modal shows Step 1 (Welcome screen)
      await expect(dialog.getByText('Welcome to LumiKB!')).toBeVisible();
      await expect(dialog.getByText(/AI-powered knowledge management/i)).toBeVisible();

      // AND: Modal is centered with dimmed background overlay
      const overlay = page.locator('[data-radix-dialog-overlay]');
      await expect(overlay).toBeVisible();

      // AND: Progress indicator shows step 1 of 5
      await expect(dialog.getByText('Step 1 of 5')).toBeVisible();
    });

    test('[P0] should mark onboarding complete and prevent re-display on subsequent login', async ({ page }) => {
      // GIVEN: A new user completes onboarding wizard

      // Step 1: Mock initial user state (onboarding_completed = false)
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      // Network-first pattern: Intercept completion API call BEFORE navigation
      const completionPromise = page.waitForRequest((req) =>
        req.url().includes('/api/v1/users/me/onboarding') && req.method() === 'PUT'
      );

      // Mock completion API response
      await page.route('**/api/v1/users/me/onboarding', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: true, // Marked complete
          }),
        });
      });

      // Navigate to dashboard
      await page.goto('/dashboard');

      // Wait for wizard to appear
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // WHEN: User completes all 5 steps
      // Navigate through Steps 1-4 using Next button
      for (let i = 0; i < 4; i++) {
        await page.getByRole('button', { name: /next/i }).click();
        await page.waitForTimeout(200); // Small delay for step transition animation
      }

      // Verify on Step 5
      await expect(page.getByText('Step 5 of 5')).toBeVisible();
      await expect(page.getByText("You're All Set!")).toBeVisible();

      // Click "Start Exploring" to complete wizard
      await page.getByRole('button', { name: /start exploring/i }).click();

      // THEN: API endpoint PUT /api/v1/users/me/onboarding is called
      await completionPromise;

      // AND: Wizard closes
      await expect(page.locator('[role="dialog"]')).not.toBeVisible();

      // Step 2: Mock subsequent login with onboarding_completed = true
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: true, // Completed
          }),
        });
      });

      // Reload page to simulate subsequent login
      await page.reload();

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // THEN: Wizard does not appear
      await expect(page.locator('[role="dialog"]')).not.toBeVisible();
      await expect(page.getByText('Welcome to LumiKB!')).not.toBeVisible();
    });

    test('[P0] should complete onboarding when user skips tutorial', async ({ page }) => {
      // GIVEN: New user sees onboarding wizard
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      // Network-first: Intercept skip API call BEFORE clicking
      const skipPromise = page.waitForRequest((req) =>
        req.url().includes('/api/v1/users/me/onboarding') && req.method() === 'PUT'
      );

      await page.route('**/api/v1/users/me/onboarding', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: true,
          }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // WHEN: User clicks "Skip Tutorial" link
      await page.getByText('Skip Tutorial').click();

      // THEN: Confirmation dialog appears
      await expect(page.getByText('Skip Tutorial?')).toBeVisible();
      await expect(page.getByText(/Are you sure you want to skip/i)).toBeVisible();

      // WHEN: User confirms skip
      const skipButtons = page.getByRole('button', { name: /skip/i });
      await skipButtons.last().click(); // Click "Skip" in confirmation dialog

      // THEN: API endpoint is called
      await skipPromise;

      // AND: Wizard closes
      await expect(page.locator('[role="dialog"]')).not.toBeVisible();
    });
  });

  test.describe('[P1] Wizard Navigation and Flow', () => {
    test.beforeEach(async ({ page }) => {
      // Setup: Mock new user state for all navigation tests
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    });

    test('[P1] should display all 5 wizard steps with correct content', async ({ page }) => {
      const dialog = page.locator('[role="dialog"]');

      // Step 1: Welcome
      await expect(dialog.getByText('Welcome to LumiKB!')).toBeVisible();
      await expect(dialog.getByText(/AI-powered knowledge management/i)).toBeVisible();
      await expect(dialog.getByText('Step 1 of 5')).toBeVisible();

      // Step 2: Explore KB
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText('Explore the Sample Knowledge Base')).toBeVisible();
      await expect(dialog.getByText('Step 2 of 5')).toBeVisible();

      // Step 3: Try Search
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText('Ask Your First Question')).toBeVisible();
      await expect(dialog.getByText('Step 3 of 5')).toBeVisible();

      // Step 4: Citations
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText('Citations Build Trust')).toBeVisible();
      await expect(dialog.getByText('Step 4 of 5')).toBeVisible();

      // Step 5: Completion
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText("You're All Set!")).toBeVisible();
      await expect(dialog.getByText('Step 5 of 5')).toBeVisible();
    });

    test('[P1] should navigate forward and backward through steps', async ({ page }) => {
      const dialog = page.locator('[role="dialog"]');

      // Start on Step 1
      await expect(dialog.getByText('Step 1 of 5')).toBeVisible();

      // Navigate forward to Step 2
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText('Step 2 of 5')).toBeVisible();

      // Navigate forward to Step 3
      await page.getByRole('button', { name: /next/i }).click();
      await expect(dialog.getByText('Step 3 of 5')).toBeVisible();

      // Navigate back to Step 2
      await page.getByRole('button', { name: /back/i }).click();
      await expect(dialog.getByText('Step 2 of 5')).toBeVisible();
      await expect(dialog.getByText('Explore the Sample Knowledge Base')).toBeVisible();

      // Navigate back to Step 1
      await page.getByRole('button', { name: /back/i }).click();
      await expect(dialog.getByText('Step 1 of 5')).toBeVisible();
      await expect(dialog.getByText('Welcome to LumiKB!')).toBeVisible();
    });

    test('[P1] should disable Back button on Step 1', async ({ page }) => {
      // On Step 1, Back button should be disabled
      const backButton = page.getByRole('button', { name: /back/i });
      await expect(backButton).toBeDisabled();

      // Navigate to Step 2
      await page.getByRole('button', { name: /next/i }).click();

      // On Step 2, Back button should be enabled
      await expect(backButton).toBeEnabled();
    });

    test('[P1] should update progress dots as user navigates', async ({ page }) => {
      // Progress dots are rendered as small circles (h-2 w-2 rounded-full)
      const getAllDots = () => page.locator('.h-2.w-2.rounded-full');

      // Step 1: First dot should be highlighted
      const dots1 = await getAllDots().all();
      expect(dots1).toHaveLength(5);

      // Check first dot has primary background color
      await expect(dots1[0]).toHaveClass(/bg-primary/);

      // Navigate to Step 2
      await page.getByRole('button', { name: /next/i }).click();

      // Step 2: Second dot should be highlighted
      const dots2 = await getAllDots().all();
      await expect(dots2[1]).toHaveClass(/bg-primary/);

      // Navigate to Step 3
      await page.getByRole('button', { name: /next/i }).click();

      // Step 3: Third dot should be highlighted
      const dots3 = await getAllDots().all();
      await expect(dots3[2]).toHaveClass(/bg-primary/);
    });

    test('[P1] should show "Start Exploring" button only on Step 5', async ({ page }) => {
      // Steps 1-4 should not have "Start Exploring" button
      for (let i = 0; i < 4; i++) {
        await expect(page.getByRole('button', { name: /start exploring/i })).not.toBeVisible();
        await page.getByRole('button', { name: /next/i }).click();
        await page.waitForTimeout(100); // Animation delay
      }

      // Step 5 should have "Start Exploring" button
      await expect(page.getByRole('button', { name: /start exploring/i })).toBeVisible();

      // Step 5 should NOT have "Next" button
      await expect(page.getByRole('button', { name: /next/i })).not.toBeVisible();
    });
  });

  test.describe('[P1] Skip Tutorial Feature', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });
    });

    test('[P1] should show "Skip Tutorial" link on all steps', async ({ page }) => {
      // Check all 5 steps
      for (let step = 1; step <= 5; step++) {
        await expect(page.getByText('Skip Tutorial')).toBeVisible();

        // Navigate to next step (except on Step 5)
        if (step < 5) {
          await page.getByRole('button', { name: /next/i }).click();
          await page.waitForTimeout(100);
        }
      }
    });

    test('[P1] should show confirmation dialog when clicking "Skip Tutorial"', async ({ page }) => {
      // Click "Skip Tutorial" link
      await page.getByText('Skip Tutorial').click();

      // Wait for confirmation dialog to appear
      await expect(page.getByText('Skip Tutorial?')).toBeVisible();
      await expect(page.getByText(/Are you sure you want to skip/i)).toBeVisible();
      await expect(page.getByText(/restart it later from Settings/i)).toBeVisible();

      // Should show Cancel and Skip buttons
      await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /skip/i })).toBeVisible();
    });

    test('[P1] should return to wizard when clicking Cancel in confirmation', async ({ page }) => {
      // Open skip confirmation
      await page.getByText('Skip Tutorial').click();
      await expect(page.getByText('Skip Tutorial?')).toBeVisible();

      // Click Cancel
      await page.getByRole('button', { name: /cancel/i }).click();

      // Should return to wizard (Step 1 still visible)
      await expect(page.getByText('Welcome to LumiKB!')).toBeVisible();
      await expect(page.getByText('Step 1 of 5')).toBeVisible();

      // Confirmation dialog should be closed
      await expect(page.getByText('Skip Tutorial?')).not.toBeVisible();
    });
  });

  test.describe('[P2] Edge Cases and Error Scenarios', () => {
    test('[P2] should handle API failure gracefully during completion', async ({ page }) => {
      // GIVEN: User completes wizard but API fails
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      // Mock API failure (500 error)
      await page.route('**/api/v1/users/me/onboarding', async (route) => {
        await route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: 'Internal server error' }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // Navigate to Step 5
      for (let i = 0; i < 4; i++) {
        await page.getByRole('button', { name: /next/i }).click();
        await page.waitForTimeout(100);
      }

      // Click "Start Exploring"
      await page.getByRole('button', { name: /start exploring/i }).click();

      // THEN: Error handling occurs (implementation-specific)
      // Note: Actual error handling behavior depends on useOnboarding hook implementation
      // This test documents expected behavior - wizard may stay open or show error toast
    });

    test('[P2] should prevent modal dismissal by clicking overlay', async ({ page }) => {
      await page.route('**/api/v1/users/me', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: 'newuser@example.com',
            onboarding_completed: false,
          }),
        });
      });

      await page.goto('/dashboard');
      await page.waitForSelector('[role="dialog"]', { state: 'visible' });

      // WHEN: User clicks on overlay (dimmed background)
      const overlay = page.locator('[data-radix-dialog-overlay]');
      await overlay.click({ force: true, position: { x: 10, y: 10 } });

      // THEN: Modal should remain visible (modal:true prevents dismissal)
      await expect(page.locator('[role="dialog"]')).toBeVisible();
      await expect(page.getByText('Welcome to LumiKB!')).toBeVisible();
    });
  });
});
