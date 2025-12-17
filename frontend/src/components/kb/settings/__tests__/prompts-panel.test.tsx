/**
 * Story 7-15: PromptsPanel Component Tests
 *
 * Tests the Prompts tab panel including:
 * - System prompt textarea with character count (AC-7.15.1, AC-7.15.2)
 * - Prompt variables help section (AC-7.15.3)
 * - Citation style selector (AC-7.15.4)
 * - Uncertainty handling selector (AC-7.15.5)
 * - Response language input (AC-7.15.6)
 * - Preview modal (AC-7.15.7)
 * - Template loading (AC-7.15.8)
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  PromptsPanel,
  promptsPanelSchema,
  defaultPromptsPanelValues,
  type PromptsPanelFormData,
} from '../prompts-panel';
import { CitationStyle, UncertaintyHandling } from '@/types/kb-settings';
import { PROMPT_TEMPLATES } from '@/lib/prompt-templates';

// =============================================================================
// Test Wrapper
// =============================================================================

interface TestWrapperProps {
  children: (form: ReturnType<typeof useForm<PromptsPanelFormData>>) => React.ReactNode;
  defaultValues?: Partial<PromptsPanelFormData>;
}

function TestWrapper({ children, defaultValues }: TestWrapperProps) {
  const form = useForm<PromptsPanelFormData>({
    resolver: zodResolver(promptsPanelSchema),
    defaultValues: {
      ...defaultPromptsPanelValues,
      ...defaultValues,
      prompts: {
        ...defaultPromptsPanelValues.prompts,
        ...defaultValues?.prompts,
      },
    },
    mode: 'onChange',
  });

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(vi.fn())}>{children(form)}</form>
    </FormProvider>
  );
}

// Helper to render with form
function renderWithForm(
  defaultValues?: Partial<PromptsPanelFormData>,
  options: { disabled?: boolean; kbName?: string } = {}
) {
  const { disabled = false, kbName = 'Test KB' } = options;
  const result = render(
    <TestWrapper defaultValues={defaultValues}>
      {(form) => <PromptsPanel form={form} kbName={kbName} disabled={disabled} />}
    </TestWrapper>
  );
  return result;
}

// Helper to get the system prompt textarea (which has id="system-prompt")
function getSystemPromptTextarea() {
  return screen.getByRole('textbox', { name: /system prompt/i });
}

describe('PromptsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ===========================================================================
  // AC-7.15.1, AC-7.15.2: System Prompt with Character Count
  // ===========================================================================
  describe('[P0] AC-7.15.1/AC-7.15.2: System Prompt', () => {
    it('renders system prompt textarea', () => {
      renderWithForm();

      expect(screen.getByText(/system prompt/i)).toBeInTheDocument();
      expect(getSystemPromptTextarea()).toBeInTheDocument();
    });

    it('displays character count indicator', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Test prompt',
        },
      });

      // Should show "11 / 4000"
      expect(screen.getByTestId('character-count')).toHaveTextContent('11 / 4000');
    });

    it('updates character count as user types', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const textarea = getSystemPromptTextarea();
      await user.type(textarea, 'Hello World');

      await waitFor(() => {
        expect(screen.getByTestId('character-count')).toHaveTextContent('11 / 4000');
      });
    });

    it('enforces max 4000 character limit via maxLength', () => {
      renderWithForm();

      const textarea = getSystemPromptTextarea();
      expect(textarea).toHaveAttribute('maxLength', '4000');
    });

    it('shows warning color when approaching limit (>90%)', () => {
      // Create a string that's > 90% of 4000 (>3600 chars)
      const longPrompt = 'a'.repeat(3700);
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: longPrompt,
        },
      });

      // Character count should have amber color class
      const charCount = screen.getByTestId('character-count');
      expect(charCount).toHaveClass('text-amber-500');
    });
  });

  // ===========================================================================
  // AC-7.15.3: Prompt Variables Help Section
  // ===========================================================================
  describe('[P1] AC-7.15.3: Variables Help Section', () => {
    it('renders collapsible variables help', () => {
      renderWithForm();

      expect(screen.getByText(/available variables/i)).toBeInTheDocument();
    });

    it('shows variables when expanded', async () => {
      const user = userEvent.setup();
      renderWithForm();

      // Click to expand
      await user.click(screen.getByText(/available variables/i));

      await waitFor(() => {
        expect(screen.getByText('{context}')).toBeInTheDocument();
        expect(screen.getByText('{query}')).toBeInTheDocument();
        expect(screen.getByText('{kb_name}')).toBeInTheDocument();
      });
    });

    it('shows descriptions for each variable', async () => {
      const user = userEvent.setup();
      renderWithForm();

      await user.click(screen.getByText(/available variables/i));

      await waitFor(() => {
        expect(screen.getByText(/retrieved document chunks/i)).toBeInTheDocument();
        expect(screen.getByText(/user's question/i)).toBeInTheDocument();
        expect(screen.getByText(/name of the current knowledge base/i)).toBeInTheDocument();
      });
    });
  });

  // ===========================================================================
  // AC-7.15.4: Citation Style Selector
  // ===========================================================================
  describe('[P0] AC-7.15.4: Citation Style Selector', () => {
    it('renders citation style dropdown', () => {
      renderWithForm();

      expect(screen.getByText(/citation style/i)).toBeInTheDocument();
      expect(screen.getByTestId('citation-style-trigger')).toBeInTheDocument();
    });

    it('shows all citation style options when clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      // Click the trigger to open the dropdown
      const trigger = screen.getByTestId('citation-style-trigger');
      await user.click(trigger);

      // Options should be visible
      await waitFor(() => {
        // Check for options in the listbox
        const listbox = screen.getByRole('listbox');
        expect(within(listbox).getByText('Inline')).toBeInTheDocument();
        expect(within(listbox).getByText('Footnote')).toBeInTheDocument();
        expect(within(listbox).getByText('None')).toBeInTheDocument();
      });
    });

    it('updates form state when citation style selected', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          citation_style: CitationStyle.INLINE,
        },
      });

      const trigger = screen.getByTestId('citation-style-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      // Click on Footnote option
      await user.click(within(screen.getByRole('listbox')).getByText('Footnote'));

      await waitFor(() => {
        expect(trigger).toHaveTextContent('Footnote');
      });
    });

    it('shows description for selected citation style', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          citation_style: CitationStyle.INLINE,
        },
      });

      expect(screen.getByText(/references appear as \[1\], \[2\]/i)).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // AC-7.15.5: Uncertainty Handling Selector
  // ===========================================================================
  describe('[P0] AC-7.15.5: Uncertainty Handling Selector', () => {
    it('renders uncertainty handling dropdown', () => {
      renderWithForm();

      expect(screen.getByText(/when uncertain, the ai should/i)).toBeInTheDocument();
      expect(screen.getByTestId('uncertainty-handling-trigger')).toBeInTheDocument();
    });

    it('shows all uncertainty handling options when clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const trigger = screen.getByTestId('uncertainty-handling-trigger');
      await user.click(trigger);

      await waitFor(() => {
        const listbox = screen.getByRole('listbox');
        expect(within(listbox).getByText('Acknowledge Uncertainty')).toBeInTheDocument();
        expect(within(listbox).getByText('Refuse Response')).toBeInTheDocument();
        expect(within(listbox).getByText('Best Effort')).toBeInTheDocument();
      });
    });

    it('updates form state when uncertainty handling selected', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
        },
      });

      const trigger = screen.getByTestId('uncertainty-handling-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Refuse Response'));

      await waitFor(() => {
        expect(trigger).toHaveTextContent('Refuse Response');
      });
    });

    it('shows description for selected uncertainty handling', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
        },
      });

      expect(screen.getByText(/ai states when it is uncertain/i)).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // AC-7.15.6: Response Language Dropdown
  // ===========================================================================
  describe('[P1] AC-7.15.6: Response Language Dropdown', () => {
    it('renders response language input', () => {
      renderWithForm();

      expect(screen.getByText(/response language/i)).toBeInTheDocument();
      expect(screen.getByTestId('response-language-trigger')).toBeInTheDocument();
    });

    it('shows English as default selection', () => {
      renderWithForm();

      const trigger = screen.getByTestId('response-language-trigger');
      expect(trigger).toHaveTextContent('English');
    });

    it('shows all language options when clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const trigger = screen.getByTestId('response-language-trigger');
      await user.click(trigger);

      await waitFor(() => {
        const listbox = screen.getByRole('listbox');
        expect(within(listbox).getByText('English')).toBeInTheDocument();
        expect(within(listbox).getByText('Tiếng Việt')).toBeInTheDocument();
      });
    });

    it('shows description about language selection', () => {
      renderWithForm();

      expect(
        screen.getByText(/ai responses and prompt templates will use this language/i)
      ).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // AC-7.15.7: Preview Modal
  // ===========================================================================
  describe('[P1] AC-7.15.7: Preview Modal', () => {
    it('renders preview button', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Test prompt',
        },
      });

      expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
    });

    it('disables preview button when no prompt content', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: '',
        },
      });

      expect(screen.getByRole('button', { name: /preview/i })).toBeDisabled();
    });

    it('opens preview modal when clicked', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Hello from {kb_name}',
        },
      });

      await user.click(screen.getByRole('button', { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText(/prompt preview/i)).toBeInTheDocument();
      });
    });

    it('substitutes variables in preview', async () => {
      const user = userEvent.setup();
      renderWithForm(
        {
          prompts: {
            ...defaultPromptsPanelValues.prompts,
            system_prompt: 'Welcome to {kb_name}. Query: {query}',
          },
        },
        { kbName: 'My Knowledge Base' }
      );

      await user.click(screen.getByRole('button', { name: /preview/i }));

      await waitFor(() => {
        const dialog = screen.getByRole('dialog');
        // Check that variable substitution happened
        expect(dialog).toHaveTextContent(/Welcome to My Knowledge Base/);
        expect(dialog).toHaveTextContent(/What is the meaning of X/i);
      });
    });

    it('shows sample values legend in preview', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Test {context}',
        },
      });

      await user.click(screen.getByRole('button', { name: /preview/i }));

      await waitFor(() => {
        expect(screen.getByText(/sample values used/i)).toBeInTheDocument();
      });
    });
  });

  // ===========================================================================
  // AC-7.15.8: Template Loading
  // ===========================================================================
  describe('[P1] AC-7.15.8: Template Loading', () => {
    it('renders load template dropdown', () => {
      renderWithForm();

      expect(screen.getByTestId('load-template-trigger')).toBeInTheDocument();
    });

    it('shows all template options when clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        const listbox = screen.getByRole('listbox');
        expect(within(listbox).getByText('Default RAG')).toBeInTheDocument();
        expect(within(listbox).getByText('Strict Citations')).toBeInTheDocument();
        expect(within(listbox).getByText('Conversational')).toBeInTheDocument();
        expect(within(listbox).getByText('Technical Documentation')).toBeInTheDocument();
      });
    });

    it('loads template directly when system prompt is empty', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: '',
        },
      });

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Default RAG'));

      // Should load template without confirmation
      await waitFor(() => {
        const textarea = getSystemPromptTextarea();
        expect(textarea).toHaveValue(PROMPT_TEMPLATES.default_rag.system_prompt);
      });
    });

    it('shows confirmation dialog when content exists', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Existing content',
        },
      });

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Default RAG'));

      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/load template\?/i)).toBeInTheDocument();
        expect(screen.getByText(/replace your current system prompt/i)).toBeInTheDocument();
      });
    });

    it('loads template when confirmed', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: 'Existing content',
        },
      });

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Strict Citations'));

      // Confirm in dialog
      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      // Find the confirm button inside the dialog
      const dialog = screen.getByRole('alertdialog');
      await user.click(within(dialog).getByRole('button', { name: /load template/i }));

      // Should load template content
      await waitFor(() => {
        const textarea = getSystemPromptTextarea();
        expect(textarea).toHaveValue(PROMPT_TEMPLATES.strict_citations.system_prompt);
      });
    });

    it('does not load template when cancelled', async () => {
      const user = userEvent.setup();
      const originalContent = 'Existing content';
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: originalContent,
        },
      });

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Default RAG'));

      // Cancel in dialog
      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const dialog = screen.getByRole('alertdialog');
      await user.click(within(dialog).getByRole('button', { name: /cancel/i }));

      // Content should remain unchanged
      await waitFor(() => {
        const textarea = getSystemPromptTextarea();
        expect(textarea).toHaveValue(originalContent);
      });
    });

    it('applies template citation style and uncertainty handling', async () => {
      const user = userEvent.setup();
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: '',
          citation_style: CitationStyle.NONE,
          uncertainty_handling: UncertaintyHandling.BEST_EFFORT,
        },
      });

      const trigger = screen.getByTestId('load-template-trigger');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      await user.click(within(screen.getByRole('listbox')).getByText('Strict Citations'));

      // Template should also update citation style and uncertainty handling
      await waitFor(() => {
        // Strict Citations template uses INLINE citation style
        expect(screen.getByTestId('citation-style-trigger')).toHaveTextContent('Inline');
        // And REFUSE for uncertainty handling
        expect(screen.getByTestId('uncertainty-handling-trigger')).toHaveTextContent(
          'Refuse Response'
        );
      });
    });
  });

  // ===========================================================================
  // Disabled State
  // ===========================================================================
  describe('[P1] Disabled State', () => {
    it('disables textarea when disabled', () => {
      renderWithForm(undefined, { disabled: true });

      expect(getSystemPromptTextarea()).toBeDisabled();
    });

    it('disables dropdowns when disabled', () => {
      renderWithForm(undefined, { disabled: true });

      expect(screen.getByTestId('citation-style-trigger')).toBeDisabled();
      expect(screen.getByTestId('uncertainty-handling-trigger')).toBeDisabled();
      expect(screen.getByTestId('load-template-trigger')).toBeDisabled();
    });

    it('disables response language dropdown when disabled', () => {
      renderWithForm(undefined, { disabled: true });

      expect(screen.getByTestId('response-language-trigger')).toBeDisabled();
    });

    it('disables preview button when disabled', () => {
      renderWithForm(
        {
          prompts: {
            ...defaultPromptsPanelValues.prompts,
            system_prompt: 'Test content',
          },
        },
        { disabled: true }
      );

      expect(screen.getByRole('button', { name: /preview/i })).toBeDisabled();
    });
  });

  // ===========================================================================
  // Form Validation
  // ===========================================================================
  describe('[P2] Form Validation', () => {
    it('allows valid form values', () => {
      renderWithForm({
        prompts: {
          system_prompt: 'Valid prompt',
          context_template: '',
          citation_style: CitationStyle.INLINE,
          uncertainty_handling: UncertaintyHandling.ACKNOWLEDGE,
          response_language: 'en',
        },
      });

      // Should render without error messages
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('accepts empty system prompt', () => {
      renderWithForm({
        prompts: {
          ...defaultPromptsPanelValues.prompts,
          system_prompt: '',
        },
      });

      // Should render without error
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
