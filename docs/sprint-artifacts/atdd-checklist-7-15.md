# ATDD Checklist: Story 7-15 KB Settings UI - Prompts Panel

**Story ID:** 7.15
**Title:** KB Settings UI - Prompts Panel
**Generated:** 2025-12-09
**Generator:** TEA (Test Engineering Architect)
**Status:** RED (Failing Tests - Implementation Required)

---

## Story Summary

**As a** KB owner
**I want** to configure custom system prompts and citation styles for my Knowledge Base
**So that** I can control how the AI responds and formats its citations

---

## Acceptance Criteria Coverage

| AC ID | Description | Test Level | Test File |
|-------|-------------|------------|-----------|
| 7.15.1 | Prompts tab visible in KB settings modal | E2E, Component | `kb-settings-prompts.spec.ts`, `prompts-panel.test.tsx` |
| 7.15.2 | System prompt textarea with max 4000 chars | Component | `prompts-panel.test.tsx` |
| 7.15.3 | Prompt variables help explaining {context}, {query}, {kb_name} | Component | `prompts-panel.test.tsx` |
| 7.15.4 | Citation style dropdown (inline, footnote, none) | Component, E2E | `prompts-panel.test.tsx`, `kb-settings-prompts.spec.ts` |
| 7.15.5 | Uncertainty handling dropdown (acknowledge, refuse, best_effort) | Component, E2E | `prompts-panel.test.tsx` |
| 7.15.6 | Response language input with placeholder | Component | `prompts-panel.test.tsx` |
| 7.15.7 | Preview button showing rendered prompt | Component | `prompts-panel.test.tsx` |
| 7.15.8 | Load Template dropdown with presets | Component, E2E | `prompts-panel.test.tsx` |

---

## Test Files to Create

### 1. Component Tests (Vitest + RTL)

**File:** `frontend/src/components/kb/settings/__tests__/prompts-panel.test.tsx`

```typescript
/**
 * Story 7-15 ATDD: PromptsPanel Component Tests
 * Generated: 2025-12-09
 * Status: RED - Implementation required to pass
 *
 * Required implementation:
 * - frontend/src/components/kb/settings/prompts-panel.tsx
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PromptsPanel } from '../prompts-panel';

interface PromptsConfig {
  system_prompt: string;
  context_template: string;
  citation_style: 'inline' | 'footnote' | 'none';
  uncertainty_handling: 'acknowledge' | 'refuse' | 'best_effort';
  response_language: string;
}

const defaultConfig: PromptsConfig = {
  system_prompt: '',
  context_template: '',
  citation_style: 'inline',
  uncertainty_handling: 'acknowledge',
  response_language: 'en',
};

describe('PromptsPanel', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] AC-7.15.1: Panel Structure', () => {
    it('renders the prompts panel with all required sections', () => {
      /**
       * GIVEN: Default prompts config
       * WHEN: Panel renders
       * THEN: System prompt, citation style, uncertainty handling, and language sections visible
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      expect(screen.getByTestId('prompts-panel')).toBeInTheDocument();
      expect(screen.getByTestId('system-prompt-section')).toBeInTheDocument();
      expect(screen.getByTestId('citation-style-section')).toBeInTheDocument();
      expect(screen.getByTestId('uncertainty-handling-section')).toBeInTheDocument();
      expect(screen.getByTestId('response-language-section')).toBeInTheDocument();
    });
  });

  describe('[P0] AC-7.15.2: System Prompt Textarea', () => {
    it('renders textarea with character count indicator', () => {
      /**
       * GIVEN: Default config with empty system_prompt
       * WHEN: Panel renders
       * THEN: Textarea shows "0 / 4000" character count
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const textarea = screen.getByTestId('system-prompt-textarea');
      expect(textarea).toBeInTheDocument();
      expect(screen.getByText('0 / 4000')).toBeInTheDocument();
    });

    it('updates character count on input', async () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: User types in system prompt
       * THEN: Character count updates
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const textarea = screen.getByTestId('system-prompt-textarea');
      await user.type(textarea, 'Hello world');

      expect(screen.getByText('11 / 4000')).toBeInTheDocument();
    });

    it('enforces 4000 character maximum', async () => {
      /**
       * GIVEN: System prompt near limit
       * WHEN: User tries to exceed 4000 chars
       * THEN: Input is truncated at 4000
       */
      const longPrompt = 'a'.repeat(3999);
      render(
        <PromptsPanel
          config={{ ...defaultConfig, system_prompt: longPrompt }}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const textarea = screen.getByTestId('system-prompt-textarea') as HTMLTextAreaElement;
      expect(textarea.value).toHaveLength(3999);
      expect(textarea).toHaveAttribute('maxLength', '4000');
    });

    it('shows warning when approaching character limit', () => {
      /**
       * GIVEN: System prompt at 3800+ chars
       * WHEN: Panel renders
       * THEN: Warning indicator shown
       */
      const nearLimitPrompt = 'a'.repeat(3850);
      render(
        <PromptsPanel
          config={{ ...defaultConfig, system_prompt: nearLimitPrompt }}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      expect(screen.getByTestId('char-limit-warning')).toBeInTheDocument();
    });
  });

  describe('[P0] AC-7.15.3: Prompt Variables Help', () => {
    it('displays variables help section', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Looking for help section
       * THEN: Variables {context}, {query}, {kb_name} are documented
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      expect(screen.getByTestId('variables-help')).toBeInTheDocument();
      expect(screen.getByText(/{context}/)).toBeInTheDocument();
      expect(screen.getByText(/{query}/)).toBeInTheDocument();
      expect(screen.getByText(/{kb_name}/)).toBeInTheDocument();
    });

    it('toggles variables help visibility', async () => {
      /**
       * GIVEN: Panel rendered with help collapsed
       * WHEN: User clicks help toggle
       * THEN: Help section expands
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const toggleButton = screen.getByTestId('variables-help-toggle');
      await user.click(toggleButton);

      expect(screen.getByTestId('variables-help-content')).toBeVisible();
    });
  });

  describe('[P0] AC-7.15.4: Citation Style Dropdown', () => {
    it('renders citation style dropdown with correct options', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Opening citation style dropdown
       * THEN: Options inline, footnote, none are available
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const dropdown = screen.getByTestId('citation-style-select');
      expect(dropdown).toBeInTheDocument();
    });

    it('selects inline as default', () => {
      /**
       * GIVEN: Default config
       * WHEN: Panel renders
       * THEN: Inline is selected
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const dropdown = screen.getByTestId('citation-style-select');
      expect(dropdown).toHaveTextContent('Inline');
    });

    it('calls onChange when citation style changes', async () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: User selects footnote
       * THEN: onChange called with updated citation_style
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const trigger = screen.getByTestId('citation-style-select');
      await user.click(trigger);
      await user.click(screen.getByRole('option', { name: /footnote/i }));

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ citation_style: 'footnote' })
      );
    });
  });

  describe('[P0] AC-7.15.5: Uncertainty Handling Dropdown', () => {
    it('renders uncertainty handling dropdown with correct options', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Checking dropdown
       * THEN: Options acknowledge, refuse, best_effort available
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const dropdown = screen.getByTestId('uncertainty-handling-select');
      expect(dropdown).toBeInTheDocument();
    });

    it('selects acknowledge as default', () => {
      /**
       * GIVEN: Default config
       * WHEN: Panel renders
       * THEN: Acknowledge is selected
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const dropdown = screen.getByTestId('uncertainty-handling-select');
      expect(dropdown).toHaveTextContent('Acknowledge');
    });

    it('calls onChange when uncertainty handling changes', async () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: User selects refuse
       * THEN: onChange called with updated uncertainty_handling
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const trigger = screen.getByTestId('uncertainty-handling-select');
      await user.click(trigger);
      await user.click(screen.getByRole('option', { name: /refuse/i }));

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ uncertainty_handling: 'refuse' })
      );
    });
  });

  describe('[P1] AC-7.15.6: Response Language Input', () => {
    it('renders language input with placeholder', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Checking language input
       * THEN: Placeholder shows "Leave empty for auto-detect"
       */
      render(
        <PromptsPanel
          config={{ ...defaultConfig, response_language: '' }}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const input = screen.getByTestId('response-language-input');
      expect(input).toHaveAttribute('placeholder', 'Leave empty for auto-detect');
    });

    it('accepts ISO 639-1 language codes', async () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: User enters "es"
       * THEN: Value is accepted
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      const input = screen.getByTestId('response-language-input');
      await user.clear(input);
      await user.type(input, 'es');

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ response_language: 'es' })
      );
    });
  });

  describe('[P1] AC-7.15.7: Preview Button', () => {
    it('renders preview button', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Checking for preview
       * THEN: Preview button exists
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      expect(screen.getByTestId('preview-prompt-button')).toBeInTheDocument();
    });

    it('opens preview modal with substituted variables', async () => {
      /**
       * GIVEN: System prompt with variables
       * WHEN: User clicks preview
       * THEN: Modal shows prompt with sample values
       */
      const user = userEvent.setup();
      const configWithPrompt = {
        ...defaultConfig,
        system_prompt: 'You are helping with {kb_name}. Context: {context}. Query: {query}',
      };

      render(
        <PromptsPanel
          config={configWithPrompt}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      await user.click(screen.getByTestId('preview-prompt-button'));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Variables should be substituted with sample values
      expect(screen.getByTestId('preview-content')).toHaveTextContent('Test KB');
      expect(screen.getByTestId('preview-content')).toHaveTextContent('[Sample context]');
      expect(screen.getByTestId('preview-content')).toHaveTextContent('[Sample query]');
    });
  });

  describe('[P1] AC-7.15.8: Load Template Dropdown', () => {
    it('renders load template dropdown', () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: Checking for templates
       * THEN: Load Template dropdown exists
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      expect(screen.getByTestId('load-template-dropdown')).toBeInTheDocument();
    });

    it('shows template options', async () => {
      /**
       * GIVEN: Panel rendered
       * WHEN: User opens template dropdown
       * THEN: Template options are shown
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      await user.click(screen.getByTestId('load-template-dropdown'));

      expect(screen.getByRole('option', { name: /default rag/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /strict citations/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /conversational/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /technical documentation/i })).toBeInTheDocument();
    });

    it('shows confirmation when loading template over existing content', async () => {
      /**
       * GIVEN: System prompt has content
       * WHEN: User selects a template
       * THEN: Confirmation dialog appears
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={{ ...defaultConfig, system_prompt: 'Existing prompt content' }}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      await user.click(screen.getByTestId('load-template-dropdown'));
      await user.click(screen.getByRole('option', { name: /strict citations/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/overwrite/i)).toBeInTheDocument();
      });
    });

    it('loads template content on confirm', async () => {
      /**
       * GIVEN: Confirmation dialog is shown
       * WHEN: User confirms
       * THEN: Template content is loaded
       */
      const user = userEvent.setup();
      render(
        <PromptsPanel
          config={{ ...defaultConfig, system_prompt: 'Existing prompt' }}
          onChange={mockOnChange}
          kbName="Test KB"
        />
      );

      await user.click(screen.getByTestId('load-template-dropdown'));
      await user.click(screen.getByRole('option', { name: /strict citations/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /confirm|continue/i }));

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          system_prompt: expect.stringContaining('citation'),
        })
      );
    });
  });

  describe('[P2] Disabled State', () => {
    it('disables all inputs when disabled prop is true', () => {
      /**
       * GIVEN: Panel with disabled=true
       * WHEN: Rendering
       * THEN: All inputs are disabled
       */
      render(
        <PromptsPanel
          config={defaultConfig}
          onChange={mockOnChange}
          kbName="Test KB"
          disabled={true}
        />
      );

      expect(screen.getByTestId('system-prompt-textarea')).toBeDisabled();
      expect(screen.getByTestId('citation-style-select')).toHaveAttribute('aria-disabled', 'true');
      expect(screen.getByTestId('uncertainty-handling-select')).toHaveAttribute('aria-disabled', 'true');
      expect(screen.getByTestId('response-language-input')).toBeDisabled();
      expect(screen.getByTestId('load-template-dropdown')).toBeDisabled();
    });
  });
});
```

### 2. E2E Tests (Playwright)

**File:** `frontend/e2e/tests/kb/kb-settings-prompts.spec.ts`

```typescript
/**
 * Story 7-15 ATDD: KB Settings Prompts Tab E2E Tests
 * Generated: 2025-12-09
 * Status: RED - Implementation required to pass
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { createKBSettings } from '../../fixtures/kb-settings.factory';

const mockKbId = 'test-kb-uuid-7-15';

test.describe('KB Settings - Prompts Tab', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    // Network-first: Intercept BEFORE navigation
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}`, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockKbId,
          name: 'Test Knowledge Base',
          description: 'Test KB for prompts',
        }),
      });
    });

    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createKBSettings()),
        });
      } else {
        route.fulfill({ status: 200, body: '{}' });
      }
    });
  });

  test('[AC-7.15.1] displays Prompts tab in KB settings modal', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User is on KB page
     * WHEN: User opens KB settings modal
     * THEN: Prompts tab is visible and clickable
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');

    await expect(page.getByRole('tab', { name: /prompts/i })).toBeVisible();
    await page.click('[data-testid="tab-prompts"]');
    await expect(page.getByTestId('prompts-panel')).toBeVisible();
  });

  test('[AC-7.15.2] system prompt textarea enforces 4000 char limit', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User is on Prompts tab
     * WHEN: User types in system prompt
     * THEN: Character count is displayed and limit enforced
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="tab-prompts"]');

    const textarea = page.getByTestId('system-prompt-textarea');
    await textarea.fill('Test prompt content');

    await expect(page.getByText(/\d+ \/ 4000/)).toBeVisible();
    expect(await textarea.getAttribute('maxLength')).toBe('4000');
  });

  test('[AC-7.15.4] citation style dropdown saves selection', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User is on Prompts tab
     * WHEN: User changes citation style to footnote
     * THEN: Selection is saved via API
     */
    let savedSettings: Record<string, unknown> | null = null;
    await page.route(`**/api/v1/knowledge-bases/${mockKbId}/settings`, (route) => {
      if (route.request().method() === 'PUT') {
        savedSettings = JSON.parse(route.request().postData() || '{}');
        route.fulfill({ status: 200, body: JSON.stringify(savedSettings) });
      } else {
        route.fulfill({
          status: 200,
          body: JSON.stringify(createKBSettings()),
        });
      }
    });

    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="tab-prompts"]');

    await page.click('[data-testid="citation-style-select"]');
    await page.click('[role="option"]:has-text("Footnote")');
    await page.click('[data-testid="save-settings-button"]');

    await expect(page.getByText(/saved/i)).toBeVisible();
    expect((savedSettings as Record<string, Record<string, unknown>>)?.prompts?.citation_style).toBe('footnote');
  });

  test('[AC-7.15.5] uncertainty handling dropdown has all options', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User is on Prompts tab
     * WHEN: User opens uncertainty handling dropdown
     * THEN: All three options are available
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="tab-prompts"]');

    await page.click('[data-testid="uncertainty-handling-select"]');

    await expect(page.getByRole('option', { name: /acknowledge/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /refuse/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /best effort/i })).toBeVisible();
  });

  test('[AC-7.15.7] preview button shows rendered prompt', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User has entered a system prompt with variables
     * WHEN: User clicks preview button
     * THEN: Modal shows prompt with sample variable substitutions
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="tab-prompts"]');

    const textarea = page.getByTestId('system-prompt-textarea');
    await textarea.fill('Welcome to {kb_name}. Context: {context}');

    await page.click('[data-testid="preview-prompt-button"]');

    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByTestId('preview-content')).toContainText('Test Knowledge Base');
  });

  test('[AC-7.15.8] load template with confirmation', async ({ authenticatedPage: page }) => {
    /**
     * GIVEN: User has existing prompt content
     * WHEN: User selects a template
     * THEN: Confirmation dialog appears before overwriting
     */
    await page.goto(`/knowledge-bases/${mockKbId}`);
    await page.click('[data-testid="kb-settings-button"]');
    await page.click('[data-testid="tab-prompts"]');

    // Enter existing content
    await page.getByTestId('system-prompt-textarea').fill('My custom prompt');

    // Try to load a template
    await page.click('[data-testid="load-template-dropdown"]');
    await page.click('[role="option"]:has-text("Strict Citations")');

    // Confirmation dialog should appear
    await expect(page.getByRole('alertdialog')).toBeVisible();
    await expect(page.getByText(/overwrite/i)).toBeVisible();
  });
});
```

---

## Required data-testid Attributes

| Component | data-testid | Purpose |
|-----------|-------------|---------|
| PromptsPanel container | `prompts-panel` | Main panel wrapper |
| System prompt section | `system-prompt-section` | Section container |
| System prompt textarea | `system-prompt-textarea` | Main input field |
| Character limit warning | `char-limit-warning` | Warning when near limit |
| Variables help toggle | `variables-help-toggle` | Expand/collapse help |
| Variables help section | `variables-help` | Help container |
| Variables help content | `variables-help-content` | Expanded help content |
| Citation style dropdown | `citation-style-select` | Style selector |
| Citation style section | `citation-style-section` | Section container |
| Uncertainty handling dropdown | `uncertainty-handling-select` | Handling selector |
| Uncertainty handling section | `uncertainty-handling-section` | Section container |
| Response language input | `response-language-input` | Language code input |
| Response language section | `response-language-section` | Section container |
| Preview button | `preview-prompt-button` | Open preview modal |
| Preview content | `preview-content` | Rendered preview text |
| Load template dropdown | `load-template-dropdown` | Template selector |
| Tab trigger | `tab-prompts` | Tab navigation |

---

## Implementation Checklist for DEV

### Files to Create

- [ ] `frontend/src/components/kb/settings/prompts-panel.tsx` - Main panel component
- [ ] `frontend/src/lib/prompt-templates.ts` - Template definitions (Default RAG, Strict Citations, etc.)

### Files to Modify

- [ ] `frontend/src/components/kb/kb-settings-modal.tsx` - Add Prompts tab
- [ ] `frontend/src/types/kb-settings.ts` - Add PromptsConfig type if not exists

### Component Structure

```
PromptsPanel
├── SystemPromptSection
│   ├── Textarea (maxLength=4000)
│   ├── CharacterCounter
│   └── VariablesHelpCollapsible
├── CitationStyleSelect
├── UncertaintyHandlingSelect
├── ResponseLanguageInput
├── LoadTemplateDropdown
├── PreviewButton
└── PreviewModal
```

### Validation Rules

- System prompt: max 4000 characters
- Citation style: enum ['inline', 'footnote', 'none']
- Uncertainty handling: enum ['acknowledge', 'refuse', 'best_effort']
- Response language: optional, ISO 639-1 code

---

## Test Execution

```bash
# Run component tests
npm run test:run -- prompts-panel.test.tsx

# Run E2E tests
npx playwright test kb-settings-prompts.spec.ts

# Run all 7-15 tests
npm run test:run -- --grep "7-15|prompts-panel"
```

---

## Definition of Done

- [ ] All component tests pass (0 → green)
- [ ] All E2E tests pass (0 → green)
- [ ] PromptsPanel component implemented with all sections
- [ ] 4000 char limit enforced with visual feedback
- [ ] Variables help expandable/collapsible
- [ ] All three citation styles selectable
- [ ] All three uncertainty handling modes selectable
- [ ] Preview modal renders with sample substitutions
- [ ] Template loading with confirmation dialog
- [ ] Form state integrates with KB settings modal save
