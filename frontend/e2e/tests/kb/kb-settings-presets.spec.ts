/**
 * Story 7-16 ATDD: KB Settings Presets E2E Tests
 * Generated: 2025-12-10
 *
 * Test Coverage:
 * - [P0] AC-7.16.1: Quick Preset dropdown at top of KB settings
 * - [P0] AC-7.16.2-6: Preset values for Legal, Technical, Creative, Code, General
 * - [P0] AC-7.16.7: Confirmation dialog when overwriting custom settings
 * - [P0] AC-7.16.8: Automatic preset detection indicator
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { createKBSettings, type KBSettings } from '../../fixtures/kb-settings.factory';

test.describe('Story 7-16: KB Settings Presets', () => {
  const mockKbId = 'kb-presets-test-uuid';
  const mockKb = {
    id: mockKbId,
    name: 'Test KB for Presets',
    description: 'KB for testing preset functionality',
    status: 'active',
    document_count: 5,
    permission_level: 'ADMIN',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  // Legal preset settings for detection testing
  const legalPresetSettings: KBSettings = {
    chunking: {
      strategy: 'recursive',
      chunk_size: 1000,
      chunk_overlap: 200,
    },
    retrieval: {
      top_k: 15,
      similarity_threshold: 0.75,
      method: 'vector',
      mmr_enabled: false,
      mmr_lambda: 0.5,
    },
    generation: {
      temperature: 0.3,
      top_p: 0.9,
      max_tokens: 4096,
    },
    prompts: {
      system_prompt: 'You are a precise legal document assistant.',
      citation_style: 'footnote',
      uncertainty_handling: 'acknowledge',
      response_language: '',
    },
    preset: 'legal',
  };

  test.beforeEach(async ({ authenticatedPage }) => {
    const page = authenticatedPage;

    // Intercept KB list endpoint
    await page.route('**/api/v1/knowledge-bases', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [mockKb], total: 1, page: 1, limit: 20 }),
      })
    );

    // Default settings response (custom settings)
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createKBSettings()),
        });
      }
      return route.continue();
    });

    // Intercept presets list endpoint
    await page.route('**/api/v1/kb-presets', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'legal', name: 'Legal', description: 'Strict citations, low temperature' },
          { id: 'technical', name: 'Technical', description: 'Balanced for documentation' },
          { id: 'creative', name: 'Creative', description: 'Higher temperature, flexible' },
          { id: 'code', name: 'Code', description: 'Precise code assistance' },
          { id: 'general', name: 'General', description: 'System defaults' },
        ]),
      })
    );
  });

  test.describe('[P0] AC-7.16.1: Quick Preset Dropdown', () => {
    test('displays preset selector at top of settings modal', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: Modal is displayed
       * THEN: Preset selector is visible at the top
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Open KB settings modal
      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Verify preset selector exists
      await expect(page.getByText('Quick Preset')).toBeVisible();
      await expect(page.getByText('Apply optimized settings for common use cases')).toBeVisible();
    });

    test('displays all preset options in dropdown', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User clicks preset dropdown
       * THEN: All five presets plus Custom are visible
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Open preset dropdown
      await page.locator('#preset-selector').click();

      // Verify all options
      await expect(page.getByRole('option', { name: 'Custom' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'Legal' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'Technical' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'Creative' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'Code' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'General' })).toBeVisible();
    });

    test('Custom option is disabled in dropdown', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens preset dropdown
       * WHEN: Viewing options
       * THEN: Custom option is visible but disabled
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      await page.locator('#preset-selector').click();

      const customOption = page.getByRole('option', { name: 'Custom' });
      await expect(customOption).toHaveAttribute('data-disabled');
    });
  });

  test.describe('[P0] AC-7.16.2-6: Preset Application', () => {
    test('applies Legal preset settings when selected', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User selects Legal preset
       * THEN: Form values update to Legal preset values
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Select Legal preset
      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Legal' }).click();

      // Verify temperature is set to 0.3 (Legal preset value)
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.3'
      );
    });

    test('applies Technical preset settings when selected', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User selects Technical preset
       * THEN: Form values update to Technical preset values
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Technical' }).click();

      // Verify Technical preset temperature (0.5)
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.5'
      );
    });

    test('applies Creative preset settings when selected', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User selects Creative preset
       * THEN: Form values update to Creative preset values (high temperature)
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Creative' }).click();

      // Verify Creative preset temperature (0.9)
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.9'
      );
    });

    test('applies Code preset settings when selected', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User selects Code preset
       * THEN: Form values update to Code preset values (very low temperature)
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Code' }).click();

      // Verify Code preset temperature (0.2)
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.2'
      );
    });
  });

  test.describe('[P0] AC-7.16.7: Confirmation Dialog', () => {
    test('shows confirmation when applying preset over custom changes', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User has made custom changes to settings
       * WHEN: User selects a preset
       * THEN: Confirmation dialog is displayed
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Make a custom change first
      const tempSlider = page.locator('[data-testid="generation-temperature-slider"]');
      await tempSlider.fill('0.8');

      // Now try to select a preset
      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Legal' }).click();

      // Confirmation dialog should appear
      await expect(page.getByRole('alertdialog')).toBeVisible();
      await expect(page.getByText('Apply Preset?')).toBeVisible();
      await expect(
        page.getByText(/custom settings that will be overwritten/)
      ).toBeVisible();
    });

    test('applies preset when user confirms', async ({ authenticatedPage }) => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User clicks Apply Preset
       * THEN: Preset is applied and dialog closes
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Make a custom change
      await page.locator('[data-testid="generation-temperature-slider"]').fill('0.8');

      // Select preset
      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Legal' }).click();

      // Confirm
      await page.getByRole('button', { name: 'Apply Preset' }).click();

      // Dialog should close
      await expect(page.getByRole('alertdialog')).not.toBeVisible();

      // Preset should be applied
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.3'
      );
    });

    test('cancels preset application when user cancels', async ({ authenticatedPage }) => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User clicks Cancel
       * THEN: Dialog closes and original values are preserved
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Make a custom change to 0.8
      await page.locator('[data-testid="generation-temperature-slider"]').fill('0.8');

      // Try to select preset
      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Legal' }).click();

      // Cancel
      await page.getByRole('button', { name: 'Cancel' }).click();

      // Dialog should close
      await expect(page.getByRole('alertdialog')).not.toBeVisible();

      // Original custom value should be preserved
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.8'
      );
    });

    test('applies preset directly when no custom changes exist', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User has not made any custom changes
       * WHEN: User selects a preset
       * THEN: Preset is applied directly without confirmation
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Select preset without making changes first
      await page.locator('#preset-selector').click();
      await page.getByRole('option', { name: 'Legal' }).click();

      // No dialog should appear
      await expect(page.getByRole('alertdialog')).not.toBeVisible();

      // Preset should be applied directly
      await expect(page.locator('[data-testid="generation-temperature-slider"]')).toHaveAttribute(
        'aria-valuenow',
        '0.3'
      );
    });
  });

  test.describe('[P0] AC-7.16.8: Preset Detection', () => {
    test('detects and displays Legal preset when settings match', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: KB has Legal preset settings
       * WHEN: User opens settings modal
       * THEN: Preset selector shows "Legal"
       */
      const page = authenticatedPage;

      // Override settings response with legal preset
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
        if (route.request().method() === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(legalPresetSettings),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Preset selector should show Legal
      await expect(page.locator('#preset-selector')).toContainText('Legal');
    });

    test('shows Custom when settings do not match any preset', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: KB has custom settings that don't match any preset
       * WHEN: User opens settings modal
       * THEN: Preset selector shows "Custom"
       */
      const page = authenticatedPage;

      // Override with truly custom settings
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
        if (route.request().method() === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
              createKBSettings({
                generation: { temperature: 0.42 }, // Non-standard value
                chunking: { chunk_size: 999 }, // Non-standard value
              })
            ),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Preset selector should show Custom
      await expect(page.locator('#preset-selector')).toContainText('Custom');
    });

    test('updates to Custom when user modifies preset settings', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User has applied Legal preset
       * WHEN: User modifies a setting value
       * THEN: Preset selector updates to show "Custom"
       */
      const page = authenticatedPage;

      // Start with legal preset
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
        if (route.request().method() === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(legalPresetSettings),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Initially should show Legal
      await expect(page.locator('#preset-selector')).toContainText('Legal');

      // Modify a setting
      await page.locator('[data-testid="generation-temperature-slider"]').fill('0.5');

      // Should now show Custom
      await expect(page.locator('#preset-selector')).toContainText('Custom');
    });
  });

  test.describe('[P1] Preset Selector Disabled State', () => {
    test('disables preset selector when form is saving', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is saving settings
       * WHEN: Save is in progress
       * THEN: Preset selector is disabled
       */
      const page = authenticatedPage;

      // Delay save response
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, async (route) => {
        if (route.request().method() === 'PUT') {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(createKBSettings()),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Make a change and save
      await page.locator('[data-testid="generation-temperature-slider"]').fill('0.5');
      await page.locator('[data-testid="save-settings-button"]').click();

      // Preset selector should be disabled during save
      await expect(page.locator('#preset-selector')).toBeDisabled();
    });
  });
});
