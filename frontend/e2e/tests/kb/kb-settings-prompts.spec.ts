/**
 * Story 7-15 ATDD: KB Settings UI - Prompts Panel E2E Tests
 * Generated: 2025-12-10
 *
 * FAILING TESTS - Implementation required to pass
 *
 * Test Coverage:
 * - [P0] AC-7.15.1: Prompts tab displays system prompt section
 * - [P0] AC-7.15.2: System prompt textarea with character count (max 4000)
 * - [P1] AC-7.15.3: Variables help section ({context}, {query}, {kb_name})
 * - [P0] AC-7.15.4: Citation style selector (Inline, Footnote, None)
 * - [P0] AC-7.15.5: Uncertainty handling selector
 * - [P1] AC-7.15.6: Response language input (optional, ISO 639-1)
 * - [P1] AC-7.15.7: Preview modal with variable substitution
 * - [P1] AC-7.15.8: Prompt templates loading
 *
 * Required data-testid attributes for implementation:
 * - kb-settings-tab-prompts
 * - system-prompt-textarea
 * - character-count
 * - variables-help-trigger
 * - citation-style-trigger
 * - uncertainty-handling-trigger
 * - response-language-input
 * - preview-button
 * - preview-modal
 * - load-template-trigger
 * - template-confirmation-dialog
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { createKBSettings, type KBSettings } from '../../fixtures/kb-settings.factory';

test.describe('Story 7-15: KB Settings UI - Prompts Panel', () => {
  const mockKbId = 'kb-settings-prompts-test-uuid';
  const mockKb = {
    id: mockKbId,
    name: 'Test KB for Prompts',
    description: 'KB for testing prompts settings UI',
    status: 'active',
    document_count: 5,
    permission_level: 'ADMIN',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  const mockSettings: KBSettings = createKBSettings({
    prompts: {
      system_prompt: 'You are a helpful assistant for {kb_name}.',
      context_template: '',
      citation_style: 'inline',
      uncertainty_handling: 'acknowledge',
      response_language: '',
    },
  });

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

    // Intercept KB settings GET endpoint
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockSettings),
        });
      }
      return route.continue();
    });
  });

  test.describe('[P0] AC-7.15.1: Prompts Tab', () => {
    test('navigates to Prompts tab and displays system prompt section', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User opens KB settings modal
       * WHEN: User clicks Prompts tab
       * THEN: System Prompt section is displayed
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Open KB settings modal
      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();

      // Click Prompts tab
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Verify system prompt section is visible
      await expect(page.locator('[data-testid="system-prompt-textarea"]')).toBeVisible();
      await expect(page.getByText(/system prompt/i)).toBeVisible();
    });
  });

  test.describe('[P0] AC-7.15.2: System Prompt with Character Count', () => {
    test('displays textarea with max 4000 characters', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: Viewing system prompt textarea
       * THEN: Textarea has maxLength of 4000 and shows character count
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await expect(textarea).toBeVisible();
      await expect(textarea).toHaveAttribute('maxLength', '4000');

      // Character count should be visible
      await expect(page.locator('[data-testid="character-count"]')).toBeVisible();
    });

    test('updates character count as user types', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User types in system prompt textarea
       * THEN: Character count updates dynamically
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await textarea.clear();
      await textarea.fill('Hello World');

      // Should show "11 / 4000"
      await expect(page.locator('[data-testid="character-count"]')).toContainText('11');
      await expect(page.locator('[data-testid="character-count"]')).toContainText('4000');
    });
  });

  test.describe('[P1] AC-7.15.3: Variables Help Section', () => {
    test('displays collapsible variables help', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User clicks variables help trigger
       * THEN: Variables {context}, {query}, {kb_name} are displayed
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Click to expand variables help
      await page.getByText(/available variables/i).click();

      // Verify variables are shown
      await expect(page.getByText('{context}')).toBeVisible();
      await expect(page.getByText('{query}')).toBeVisible();
      await expect(page.getByText('{kb_name}')).toBeVisible();
    });
  });

  test.describe('[P0] AC-7.15.4: Citation Style Selector', () => {
    test('displays citation style dropdown with all options', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User clicks citation style dropdown
       * THEN: Inline, Footnote, None options are available
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Open citation style dropdown
      await page.locator('[data-testid="citation-style-trigger"]').click();

      // Verify options
      await expect(page.getByRole('option', { name: /inline/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /footnote/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /none/i })).toBeVisible();
    });

    test('updates citation style when option selected', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is on Prompts tab with Inline selected
       * WHEN: User selects Footnote
       * THEN: Citation style updates to Footnote
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Open and select Footnote
      await page.locator('[data-testid="citation-style-trigger"]').click();
      await page.getByRole('option', { name: /footnote/i }).click();

      // Verify selection
      await expect(page.locator('[data-testid="citation-style-trigger"]')).toContainText(
        /footnote/i
      );
    });
  });

  test.describe('[P0] AC-7.15.5: Uncertainty Handling Selector', () => {
    test('displays uncertainty handling dropdown with all options', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User clicks uncertainty handling dropdown
       * THEN: Acknowledge, Refuse, Best Effort options are available
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Open uncertainty handling dropdown
      await page.locator('[data-testid="uncertainty-handling-trigger"]').click();

      // Verify options
      await expect(page.getByRole('option', { name: /acknowledge/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /refuse/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /best effort/i })).toBeVisible();
    });
  });

  test.describe('[P1] AC-7.15.6: Response Language Input', () => {
    test('displays response language input with placeholder', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: Viewing response language input
       * THEN: Input shows placeholder for auto-detect
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Verify input with placeholder
      await expect(
        page.getByPlaceholder(/leave empty for auto-detect/i)
      ).toBeVisible();
    });

    test('accepts ISO 639-1 language codes', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User types "en" in response language
       * THEN: Input accepts the value
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      const input = page.getByPlaceholder(/leave empty for auto-detect/i);
      await input.fill('en');

      await expect(input).toHaveValue('en');
    });
  });

  test.describe('[P1] AC-7.15.7: Preview Modal', () => {
    test('opens preview modal with variable substitution', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User has entered system prompt with variables
       * WHEN: User clicks Preview button
       * THEN: Preview modal shows prompt with substituted values
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Enter prompt with variable
      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await textarea.fill('Welcome to {kb_name}');

      // Click preview
      await page.getByRole('button', { name: /preview/i }).click();

      // Verify modal shows with substituted value
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/prompt preview/i)).toBeVisible();
      // KB name should be substituted
      await expect(page.getByRole('dialog')).toContainText('Test KB for Prompts');
    });

    test('disables preview button when no prompt content', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: System prompt is empty
       * THEN: Preview button is disabled
       */
      const page = authenticatedPage;

      // Mock empty prompt
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
        if (route.request().method() === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
              createKBSettings({
                prompts: { system_prompt: '' },
              })
            ),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Clear textarea to ensure empty
      await page.locator('[data-testid="system-prompt-textarea"]').clear();

      // Preview button should be disabled
      await expect(page.getByRole('button', { name: /preview/i })).toBeDisabled();
    });
  });

  test.describe('[P1] AC-7.15.8: Prompt Templates', () => {
    test('displays template options when clicking Load Template', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User is on Prompts tab
       * WHEN: User clicks Load Template dropdown
       * THEN: Default RAG, Strict Citations, Conversational, Technical Documentation options shown
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Open template dropdown
      await page.locator('[data-testid="load-template-trigger"]').click();

      // Verify template options
      await expect(page.getByRole('option', { name: /default rag/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /strict citations/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /conversational/i })).toBeVisible();
      await expect(
        page.getByRole('option', { name: /technical documentation/i })
      ).toBeVisible();
    });

    test('shows confirmation dialog when loading template with existing content', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: User has existing system prompt content
       * WHEN: User selects a template
       * THEN: Confirmation dialog is shown
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Ensure there's existing content
      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await textarea.fill('Existing content');

      // Try to load a template
      await page.locator('[data-testid="load-template-trigger"]').click();
      await page.getByRole('option', { name: /default rag/i }).click();

      // Confirmation dialog should appear
      await expect(page.getByRole('alertdialog')).toBeVisible();
      await expect(page.getByText(/load template\?/i)).toBeVisible();
    });

    test('loads template content on confirmation', async ({ authenticatedPage }) => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User confirms
       * THEN: Template content replaces system prompt
       */
      const page = authenticatedPage;

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Add existing content
      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await textarea.fill('Existing content');

      // Load template
      await page.locator('[data-testid="load-template-trigger"]').click();
      await page.getByRole('option', { name: /default rag/i }).click();

      // Confirm
      await page.getByRole('button', { name: /load template/i }).click();

      // Template content should be loaded
      await expect(textarea).toContainText(/helpful assistant/i);
    });

    test('loads template directly when system prompt is empty', async ({
      authenticatedPage,
    }) => {
      /**
       * GIVEN: System prompt is empty
       * WHEN: User selects a template
       * THEN: Template loads without confirmation
       */
      const page = authenticatedPage;

      // Mock empty prompt
      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
        if (route.request().method() === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(
              createKBSettings({
                prompts: { system_prompt: '' },
              })
            ),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Ensure empty
      await page.locator('[data-testid="system-prompt-textarea"]').clear();

      // Load template
      await page.locator('[data-testid="load-template-trigger"]').click();
      await page.getByRole('option', { name: /default rag/i }).click();

      // Should load without confirmation dialog
      await expect(page.getByRole('alertdialog')).not.toBeVisible();

      // Template content should be loaded
      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await expect(textarea).toContainText(/helpful assistant/i);
    });
  });

  test.describe('[P0] Save Prompts Settings', () => {
    test('saves prompts settings via PUT endpoint', async ({ authenticatedPage }) => {
      /**
       * GIVEN: User modifies prompts settings
       * WHEN: User clicks Save
       * THEN: PUT request includes prompts configuration
       */
      const page = authenticatedPage;
      let savedSettings: KBSettings | null = null;

      await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, async (route) => {
        if (route.request().method() === 'PUT') {
          savedSettings = route.request().postDataJSON();
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(savedSettings),
          });
        }
        return route.continue();
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      await page.locator(`[data-testid="kb-settings-button-${mockKbId}"]`).click();
      await page.locator('[data-testid="kb-settings-tab-prompts"]').click();

      // Modify system prompt
      const textarea = page.locator('[data-testid="system-prompt-textarea"]');
      await textarea.fill('Custom prompt for testing');

      // Save
      await page.locator('[data-testid="save-settings-button"]').click();

      // Verify API call includes prompts
      await expect.poll(() => savedSettings).not.toBeNull();
      expect((savedSettings as KBSettings | null)?.prompts?.system_prompt).toBe('Custom prompt for testing');
    });
  });
});
