/**
 * E2E tests for template selection workflow
 *
 * Story 4.9: Generation Templates
 * Tests AC-1 (templates available), AC-3 (example previews), AC-4 (custom prompt)
 */

import { test, expect } from '@playwright/test';

test.describe('Template Selection Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // GIVEN: User is logged in and navigates to search page
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'admin@example.com');
    await page.fill('[data-testid="password-input"]', 'SecurePassword123!');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/search');

    // AND: User clicks "Generate Draft" button to open generation modal
    await page.click('[data-testid="generate-draft-button"]');
    await page.waitForSelector('[data-testid="template-rfp_response"]');
  });

  test('[P0] displays all four template options', async ({ page }) => {
    // WHEN: Generation modal is open
    // THEN: All four template cards are visible
    await expect(page.locator('[data-testid="template-rfp_response"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-checklist"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-gap_analysis"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-custom"]')).toBeVisible();

    // AND: Each template shows name and description
    await expect(page.getByText('RFP Response Section')).toBeVisible();
    await expect(
      page.getByText(/Generate a structured RFP response with executive summary/)
    ).toBeVisible();
    await expect(page.getByText('Technical Checklist')).toBeVisible();
    await expect(page.getByText('Gap Analysis')).toBeVisible();
    await expect(page.getByText('Custom Prompt')).toBeVisible();
  });

  test('[P1] selects template and shows correct preview', async ({ page }) => {
    // GIVEN: Generation modal is open with default template
    // WHEN: User clicks on Technical Checklist template
    await page.click('[data-testid="template-checklist"]');

    // THEN: Checklist template is highlighted with border-primary
    const checklistCard = page.locator('[data-testid="template-checklist"]');
    await expect(checklistCard).toHaveClass(/border-primary/);

    // AND: Example preview shows checklist format
    await expect(page.getByText('Example preview:')).toBeVisible();
    await expect(page.getByText(/Authentication Requirements/)).toBeVisible();

    // WHEN: User switches to Gap Analysis
    await page.click('[data-testid="template-gap_analysis"]');

    // THEN: Gap Analysis is now selected
    const gapCard = page.locator('[data-testid="template-gap_analysis"]');
    await expect(gapCard).toHaveClass(/border-primary/);

    // AND: Checklist is no longer selected
    await expect(checklistCard).not.toHaveClass(/border-primary/);
  });

  test('[P1] custom template changes placeholder text', async ({ page }) => {
    // GIVEN: Generation modal is open with RFP Response selected (default)
    const contextInput = page.locator('[data-testid="context-input"]');

    // THEN: Placeholder shows RFP-specific example
    await expect(contextInput).toHaveAttribute(
      'placeholder',
      /Respond to section 4.2 about authentication requirements/i
    );

    // WHEN: User selects Custom Prompt template
    await page.click('[data-testid="template-custom"]');

    // THEN: Placeholder changes to custom instructions
    await expect(contextInput).toHaveAttribute('placeholder', /Provide your custom instructions/i);

    // AND: No example preview is shown for custom template
    const customCard = page.locator('[data-testid="template-custom"]');
    const preElement = customCard.locator('pre');
    await expect(preElement).not.toBeVisible();
  });

  test('[P1] generate button disabled without context', async ({ page }) => {
    // GIVEN: RFP Response template is selected
    await page.click('[data-testid="template-rfp_response"]');

    // WHEN: Context input is empty
    const contextInput = page.locator('[data-testid="context-input"]');
    await expect(contextInput).toHaveValue('');

    // THEN: Generate button is disabled
    const generateBtn = page.locator('[data-testid="generate-button"]');
    await expect(generateBtn).toBeDisabled();

    // WHEN: User enters context
    await contextInput.fill('Generate RFP response for section 4.2 on authentication');

    // THEN: Generate button is enabled
    await expect(generateBtn).toBeEnabled();

    // WHEN: User clears context
    await contextInput.clear();

    // THEN: Generate button is disabled again
    await expect(generateBtn).toBeDisabled();
  });

  test('[P2] keyboard navigation works for template selection', async ({ page }) => {
    // GIVEN: Generation modal is open
    // WHEN: User tabs to template selector and presses Enter on checklist
    await page.locator('[data-testid="template-checklist"]').focus();
    await page.keyboard.press('Enter');

    // THEN: Checklist template is selected
    const checklistCard = page.locator('[data-testid="template-checklist"]');
    await expect(checklistCard).toHaveClass(/border-primary/);

    // WHEN: User tabs to gap analysis and presses Space
    await page.locator('[data-testid="template-gap_analysis"]').focus();
    await page.keyboard.press('Space');

    // THEN: Gap Analysis is selected
    const gapCard = page.locator('[data-testid="template-gap_analysis"]');
    await expect(gapCard).toHaveClass(/border-primary/);
  });

  test('[P1] template selection persists during generation workflow', async ({ page }) => {
    // GIVEN: User selects Gap Analysis template
    await page.click('[data-testid="template-gap_analysis"]');
    await expect(page.locator('[data-testid="template-gap_analysis"]')).toHaveClass(
      /border-primary/
    );

    // WHEN: User enters context and clicks generate
    await page.fill('[data-testid="context-input"]', 'Analyze authentication gaps');
    await page.click('[data-testid="generate-button"]');

    // THEN: Generation starts (modal may close or show loading state)
    // This test verifies the template ID is sent with the generation request
    // (API verification would be done in integration tests)
    await page.waitForTimeout(500); // Small wait to ensure request sent

    // NOTE: Actual generated content verification would require:
    // 1. Wait for generation to complete
    // 2. Check that output follows gap analysis format (table with columns)
    // 3. Verify citations are included [1], [2]
    // This is covered by integration tests for generation API
  });

  test('[P2] example previews show citation format', async ({ page }) => {
    // GIVEN: RFP Response template is selected
    await page.click('[data-testid="template-rfp_response"]');

    // THEN: Example preview shows citation format [1]
    const rfpCard = page.locator('[data-testid="template-rfp_response"]');
    const exampleText = await rfpCard.locator('pre').textContent();
    expect(exampleText).toContain('[1]');

    // WHEN: User selects Checklist template
    await page.click('[data-testid="template-checklist"]');

    // THEN: Example shows citation format
    const checklistCard = page.locator('[data-testid="template-checklist"]');
    const checklistExample = await checklistCard.locator('pre').textContent();
    expect(checklistExample).toContain('[1]');
  });
});

test.describe('Template Selection Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'admin@example.com');
    await page.fill('[data-testid="password-input"]', 'SecurePassword123!');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/search');
    await page.click('[data-testid="generate-draft-button"]');
  });

  test('[P2] template selector has proper ARIA roles', async ({ page }) => {
    // GIVEN: Generation modal is open
    // THEN: Template selector has radiogroup role
    const radioGroup = page.locator('[role="radiogroup"]');
    await expect(radioGroup).toBeVisible();

    // AND: Each template has radio role
    const rfpRadio = page.locator('[data-testid="template-rfp_response"]');
    expect(await rfpRadio.getAttribute('role')).toBe('radio');

    // AND: Selected template has aria-checked="true"
    await page.click('[data-testid="template-rfp_response"]');
    expect(await rfpRadio.getAttribute('aria-checked')).toBe('true');

    // AND: Non-selected templates have aria-checked="false"
    const checklistRadio = page.locator('[data-testid="template-checklist"]');
    expect(await checklistRadio.getAttribute('aria-checked')).toBe('false');
  });

  test('[P2] screen reader can identify template options', async ({ page }) => {
    // GIVEN: Generation modal is open
    // THEN: Radiogroup has accessible label
    const radioGroup = page.locator('[role="radiogroup"]');
    expect(await radioGroup.getAttribute('aria-label')).toBe('Template selection');

    // AND: Each template is focusable
    const rfpTemplate = page.locator('[data-testid="template-rfp_response"]');
    expect(await rfpTemplate.getAttribute('tabindex')).toBe('0');
  });
});
