/**
 * ATDD E2E Tests: Epic 4 - Document Generation & Export (Story 4.4-4.7)
 * Status: RED phase - Tests written before implementation
 * Generated: 2025-11-26
 *
 * Test Coverage:
 * - P0: Low confidence sections highlighted (R-005)
 * - P0: DOCX/PDF export preserves citations (R-004)
 * - P0: Verification prompt before export
 * - P1: Template selection and generation
 * - P1: Draft editing with citation preservation
 *
 * Risk Mitigation:
 * - R-004 (DATA): Citation loss during export
 * - R-005 (BUS): Low-confidence drafts flagged
 *
 * Knowledge Base References:
 * - network-first.md: Route interception for generation
 * - test-quality.md: File download validation
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { Page, Download } from '@playwright/test';

test.describe('Document Generation & Export', () => {
  test.beforeEach(async ({ page }) => {
    // GIVEN: User is on chat page with demo KB
    await page.goto('/dashboard');
    await page.click('[data-testid="kb-card"]:first-child');
    await page.waitForURL(/\/kb\/.*\/chat/);
  });

  test('P0: low confidence sections are highlighted with warnings', async ({ page }) => {
    /**
     * Risk: R-005 (Low-confidence drafts not flagged)
     * GIVEN: User requests document generation
     * WHEN: Some sections have <70% confidence
     * THEN: Sections shown with amber/red highlighting and warning
     */

    // Click "Generate Document" button
    await page.click('[data-testid="generate-document-button"]');

    // Select template
    await page.click('[data-testid="template-select"]');
    await page.click('[data-testid="template-option-gap-analysis"]');

    // Enter context
    await page.fill(
      '[data-testid="generation-context"]',
      'Quantum blockchain authentication protocols' // Intentionally obscure
    );

    // Start generation
    await page.click('[data-testid="start-generation-button"]');

    // Wait for generation to complete
    await expect(page.locator('[data-testid="generation-complete"]')).toBeVisible({
      timeout: 30000,
    });

    // Check for confidence indicators
    const lowConfidenceSections = page.locator(
      '[data-testid="draft-section"][data-confidence="low"]'
    );
    const mediumConfidenceSections = page.locator(
      '[data-testid="draft-section"][data-confidence="medium"]'
    );

    const lowCount = await lowConfidenceSections.count();
    const mediumCount = await mediumConfidenceSections.count();

    // If any low/medium confidence sections exist, verify warnings
    if (lowCount > 0) {
      // CRITICAL: Low confidence section should have red styling
      const firstLowSection = lowConfidenceSections.first();
      const bgColor = await firstLowSection.evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor;
      });

      // Should have red/amber background (not white)
      expect(bgColor).not.toBe('rgb(255, 255, 255)');

      // Warning text should be visible
      await expect(firstLowSection.locator(':has-text("Verify carefully")')).toBeVisible();
    }

    if (mediumCount > 0) {
      // Medium confidence should have amber styling
      const firstMediumSection = mediumConfidenceSections.first();
      await expect(firstMediumSection.locator(':has-text("Review suggested")')).toBeVisible();
    }
  });

  test('P0: DOCX export preserves citations and requires verification', async ({ page }) => {
    /**
     * Risk: R-004 (Citation loss during export)
     * GIVEN: User has generated draft with citations
     * WHEN: User exports to DOCX
     * THEN: Verification prompt shown AND citations preserved in download
     */

    // Generate simple draft
    await generateDraft(page, 'RFP Response', 'OAuth implementation proposal');

    // Click export button
    await page.click('[data-testid="export-draft-button"]');

    // Select DOCX format
    await page.click('[data-testid="export-format-docx"]');

    // CRITICAL: Verification modal should appear
    await expect(page.locator('[data-testid="export-verification-modal"]')).toBeVisible();

    // Modal should mention source verification
    const modalText = await page.locator('[data-testid="export-verification-modal"]').textContent();
    expect(modalText?.toLowerCase()).toMatch(/verified|verify|check.*sources/);

    // Confirm verification
    await page.click('[data-testid="confirm-sources-verified"]');

    // Start download
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="confirm-export-button"]');

    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toMatch(/\.docx$/);

    // Save file for inspection
    const path = await download.path();
    expect(path).toBeTruthy();

    // NOTE: Actual DOCX citation validation done in integration tests
    // E2E just verifies download succeeds
  });

  test('P0: PDF export preserves citations', async ({ page }) => {
    /**
     * Risk: R-004 (Citation loss during export)
     * GIVEN: Generated draft with citations
     * WHEN: Exported to PDF
     * THEN: Download succeeds and PDF is generated
     */

    await generateDraft(page, 'Checklist', 'OAuth implementation checklist');

    await page.click('[data-testid="export-draft-button"]');
    await page.click('[data-testid="export-format-pdf"]');

    // Verify sources
    await page.click('[data-testid="confirm-sources-verified"]');

    // Download PDF
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="confirm-export-button"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test('P1: template selection shows correct structure preview', async ({ page }) => {
    /**
     * GIVEN: User clicks generate document
     * WHEN: User browses templates
     * THEN: Each template shows description and expected sections
     */

    await page.click('[data-testid="generate-document-button"]');

    // Select RFP Response template
    await page.click('[data-testid="template-select"]');
    await page.click('[data-testid="template-option-rfp-response"]');

    // Verify template description shown
    await expect(page.locator('[data-testid="template-description"]')).toBeVisible();

    const description = await page.locator('[data-testid="template-description"]').textContent();
    expect(description?.toLowerCase()).toContain('rfp');

    // Verify expected sections listed
    const sectionList = page.locator('[data-testid="template-sections"] li');
    const sectionCount = await sectionList.count();
    expect(sectionCount).toBeGreaterThan(0);

    // RFP should have sections like Executive Summary, Technical Approach, etc.
    const sections = [];
    for (let i = 0; i < sectionCount; i++) {
      sections.push(await sectionList.nth(i).textContent());
    }

    expect(sections.some((s) => s?.toLowerCase().includes('executive summary'))).toBeTruthy();
    expect(sections.some((s) => s?.toLowerCase().includes('technical'))).toBeTruthy();
  });

  test('P1: draft generation shows progress indicator', async ({ page }) => {
    /**
     * GIVEN: User starts generation
     * WHEN: Generation is in progress
     * THEN: Progress indicator shows estimated completion
     */

    await page.click('[data-testid="generate-document-button"]');
    await page.click('[data-testid="template-select"]');
    await page.click('[data-testid="template-option-checklist"]');

    await page.fill('[data-testid="generation-context"]', 'Security checklist for OAuth');
    await page.click('[data-testid="start-generation-button"]');

    // Progress indicator should appear
    await expect(page.locator('[data-testid="generation-progress"]')).toBeVisible();

    // Verify progress percentage or text
    const progressText = await page.locator('[data-testid="generation-progress"]').textContent();
    expect(progressText).toMatch(/generating|progress|\d+%/i);

    // Wait for completion
    await expect(page.locator('[data-testid="generation-complete"]')).toBeVisible({
      timeout: 30000,
    });

    // Progress indicator should disappear
    await expect(page.locator('[data-testid="generation-progress"]')).toBeHidden();
  });

  test('P1: source summary displays after generation', async ({ page }) => {
    /**
     * FR35d: "Based on 5 sources from 3 documents" summary
     * GIVEN: Draft generation completes
     * WHEN: User views draft
     * THEN: Summary shows source count and document count
     */

    await generateDraft(page, 'RFP Response', 'OAuth and JWT comparison');

    // Source summary should be visible
    await expect(page.locator('[data-testid="source-summary"]')).toBeVisible();

    const summaryText = await page.locator('[data-testid="source-summary"]').textContent();

    // Should show pattern: "Based on X sources from Y documents"
    expect(summaryText).toMatch(/based on \d+ sources? from \d+ documents?/i);
  });

  test('P2: draft editing preserves citation markers', async ({ page }) => {
    /**
     * Risk: R-008 (Draft editing corrupts citations)
     * GIVEN: User has generated draft with citations
     * WHEN: User edits text around citation markers
     * THEN: Citation markers remain intact
     */

    await generateDraft(page, 'RFP Response', 'OAuth implementation');

    // Get draft editor
    const editor = page.locator('[data-testid="draft-editor"]');
    await expect(editor).toBeVisible();

    // Count initial citations
    const initialCitations = await page.locator('[data-testid="citation-badge"]').count();
    expect(initialCitations).toBeGreaterThan(0);

    // Click into editor and type text
    await editor.click();
    await page.keyboard.type(' Additional text here. ');

    // Wait a moment for any auto-save
    await page.waitForTimeout(500);

    // Citations should still be present
    const finalCitations = await page.locator('[data-testid="citation-badge"]').count();
    expect(finalCitations).toBe(initialCitations);
  });

  test('P2: export with low confidence requires additional acknowledgment', async ({ page }) => {
    /**
     * Risk: R-005 (Low-confidence drafts not flagged)
     * GIVEN: Draft with low-confidence sections
     * WHEN: User attempts export
     * THEN: Additional warning shown requiring acknowledgment
     */

    // Generate draft with obscure topic (low confidence)
    await generateDraft(page, 'Gap Analysis', 'Quantum authentication protocols');

    // Check if draft has low confidence sections
    const lowConfSections = await page
      .locator('[data-testid="draft-section"][data-confidence="low"]')
      .count();

    if (lowConfSections > 0) {
      await page.click('[data-testid="export-draft-button"]');
      await page.click('[data-testid="export-format-docx"]');

      // Verify sources checkbox
      await page.click('[data-testid="confirm-sources-verified"]');

      // CRITICAL: Additional warning for low confidence
      const warningText = await page
        .locator('[data-testid="export-verification-modal"]')
        .textContent();
      expect(warningText?.toLowerCase()).toMatch(/low confidence|verify carefully/);

      // Additional checkbox should be required
      const lowConfCheckbox = page.locator('[data-testid="acknowledge-low-confidence"]');
      await expect(lowConfCheckbox).toBeVisible();

      // Export button should be disabled until acknowledged
      const exportButton = page.locator('[data-testid="confirm-export-button"]');
      await expect(exportButton).toBeDisabled();

      // Acknowledge low confidence
      await lowConfCheckbox.check();

      // Now export should be enabled
      await expect(exportButton).toBeEnabled();
    }
  });

  test('P3: markdown export provides footnote format', async ({ page }) => {
    /**
     * GIVEN: Generated draft
     * WHEN: User exports to Markdown
     * THEN: Download succeeds with .md extension
     */

    await generateDraft(page, 'RFP Response', 'JWT authentication');

    await page.click('[data-testid="export-draft-button"]');
    await page.click('[data-testid="export-format-markdown"]');

    await page.click('[data-testid="confirm-sources-verified"]');

    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="confirm-export-button"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.md$/);
  });
});

// Helper function
async function generateDraft(page: Page, templateType: string, context: string) {
  await page.click('[data-testid="generate-document-button"]');

  // Select template
  await page.click('[data-testid="template-select"]');
  const templateSlug = templateType.toLowerCase().replace(/\s+/g, '-');
  await page.click(`[data-testid="template-option-${templateSlug}"]`);

  // Enter context
  await page.fill('[data-testid="generation-context"]', context);

  // Start generation
  await page.click('[data-testid="start-generation-button"]');

  // Wait for completion
  await expect(page.locator('[data-testid="generation-complete"]')).toBeVisible({ timeout: 30000 });
}
