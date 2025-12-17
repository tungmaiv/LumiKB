/**
 * Story 7-14: GeneralPanel Component Tests
 *
 * Tests the complete General tab panel integrating:
 * - ChunkingSection (AC-7.14.2)
 * - RetrievalSection (AC-7.14.3)
 * - GenerationSection (AC-7.14.4)
 * - Reset to Defaults (AC-7.14.5)
 * - Form validation (AC-7.14.7)
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  GeneralPanel,
  generalPanelSchema,
  defaultGeneralPanelValues,
  type KBSettingsFormData,
} from '../general-panel';
import { ChunkingStrategy, RetrievalMethod } from '@/types/kb-settings';

// =============================================================================
// Test Wrapper
// =============================================================================

interface TestWrapperProps {
  children: (form: ReturnType<typeof useForm<KBSettingsFormData>>) => React.ReactNode;
  defaultValues?: Partial<KBSettingsFormData>;
  onSubmit?: (data: KBSettingsFormData) => void;
}

function TestWrapper({ children, defaultValues, onSubmit }: TestWrapperProps) {
  const form = useForm<KBSettingsFormData>({
    resolver: zodResolver(generalPanelSchema),
    defaultValues: {
      ...defaultGeneralPanelValues,
      ...defaultValues,
      chunking: { ...defaultGeneralPanelValues.chunking, ...defaultValues?.chunking },
      retrieval: { ...defaultGeneralPanelValues.retrieval, ...defaultValues?.retrieval },
      generation: { ...defaultGeneralPanelValues.generation, ...defaultValues?.generation },
    },
    mode: 'onChange',
  });

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit || vi.fn())}>{children(form)}</form>
    </FormProvider>
  );
}

// Helper to render with form
function renderWithForm(
  defaultValues?: Partial<KBSettingsFormData>,
  options: { disabled?: boolean; onResetToDefaults?: () => void } = {}
) {
  const { disabled = false, onResetToDefaults = vi.fn() } = options;
  const onSubmit = vi.fn();
  const result = render(
    <TestWrapper defaultValues={defaultValues} onSubmit={onSubmit}>
      {(form) => (
        <GeneralPanel form={form} disabled={disabled} onResetToDefaults={onResetToDefaults} />
      )}
    </TestWrapper>
  );
  return { ...result, onSubmit, onResetToDefaults };
}

describe('GeneralPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] Panel Structure', () => {
    it('renders all three sections', () => {
      renderWithForm();

      expect(screen.getByText('Chunking')).toBeInTheDocument();
      expect(screen.getByText('Retrieval')).toBeInTheDocument();
      expect(screen.getByText('Generation')).toBeInTheDocument();
    });

    it('renders Reset to Defaults button', () => {
      renderWithForm();

      expect(screen.getByRole('button', { name: /reset to defaults/i })).toBeInTheDocument();
    });

    it('renders separators between sections', () => {
      const { container } = renderWithForm();

      // Check for horizontal rule elements (separators)
      const separators = container.querySelectorAll('[data-orientation="horizontal"]');
      expect(separators.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('[P0] Settings Display', () => {
    it('displays chunking settings correctly', () => {
      renderWithForm({
        chunking: {
          strategy: ChunkingStrategy.SEMANTIC,
          chunk_size: 1024,
          chunk_overlap: 100,
        },
      });

      // Check strategy dropdown shows semantic
      const comboboxes = screen.getAllByRole('combobox');
      expect(comboboxes[0]).toHaveTextContent(/semantic/i);

      // Check chunk size input (first spinbutton in chunking section)
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[0]).toHaveValue(1024);
    });

    it('displays retrieval settings correctly', () => {
      renderWithForm({
        retrieval: {
          top_k: 25,
          similarity_threshold: 0.85,
          method: RetrievalMethod.HYBRID,
          mmr_enabled: true,
          mmr_lambda: 0.75,
        },
      });

      // Check top_k input (third spinbutton: chunk_size, chunk_overlap, top_k)
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[2]).toHaveValue(25);

      // Check method dropdown shows hybrid (second combobox)
      const comboboxes = screen.getAllByRole('combobox');
      expect(comboboxes[1]).toHaveTextContent(/hybrid/i);

      // Check MMR toggle is on
      const mmrSwitch = screen.getByRole('switch');
      expect(mmrSwitch).toBeChecked();

      // Check MMR lambda is displayed
      expect(screen.getByText('0.75')).toBeInTheDocument();
    });

    it('displays generation settings correctly', () => {
      renderWithForm({
        generation: {
          temperature: 1.5,
          top_p: 0.9,
          max_tokens: 8192,
        },
      });

      // Check temperature value
      expect(screen.getByText('1.50')).toBeInTheDocument();

      // Check top_p value
      expect(screen.getByText('0.90')).toBeInTheDocument();

      // Check max_tokens input (last spinbutton)
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[inputs.length - 1]).toHaveValue(8192);
    });
  });

  describe('[P1] AC-7.14.5: Reset to Defaults', () => {
    it('shows confirmation dialog when reset clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      await user.click(screen.getByRole('button', { name: /reset to defaults/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/reset general settings/i)).toBeInTheDocument();
      });
    });

    it('confirms reset resets form to defaults', async () => {
      const user = userEvent.setup();
      const onResetToDefaults = vi.fn();

      renderWithForm(
        {
          chunking: {
            strategy: ChunkingStrategy.SEMANTIC,
            chunk_size: 1024,
            chunk_overlap: 200,
          },
        },
        { onResetToDefaults }
      );

      // Verify initial non-default value
      const inputs = screen.getAllByRole('spinbutton');
      const sizeInput = inputs[0];
      expect(sizeInput).toHaveValue(1024);

      // Open dialog
      await user.click(screen.getByRole('button', { name: /reset to defaults/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      // Click confirm - get all buttons with "reset to defaults" and click the one in dialog
      const dialogButtons = screen.getAllByRole('button', { name: /reset to defaults/i });
      await user.click(dialogButtons[dialogButtons.length - 1]);

      // Check callback was called
      expect(onResetToDefaults).toHaveBeenCalled();

      // Form should be reset to defaults
      await waitFor(() => {
        expect(sizeInput).toHaveValue(512); // default value
      });
    });

    it('does not reset when cancel clicked', async () => {
      const user = userEvent.setup();
      const onResetToDefaults = vi.fn();

      renderWithForm(
        {
          chunking: {
            strategy: ChunkingStrategy.SEMANTIC,
            chunk_size: 1024,
            chunk_overlap: 200,
          },
        },
        { onResetToDefaults }
      );

      const inputs = screen.getAllByRole('spinbutton');
      const sizeInput = inputs[0];
      expect(sizeInput).toHaveValue(1024);

      // Open dialog
      await user.click(screen.getByRole('button', { name: /reset to defaults/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      // Click cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      // Should NOT have called reset
      expect(onResetToDefaults).not.toHaveBeenCalled();

      // Value should remain unchanged
      expect(sizeInput).toHaveValue(1024);
    });
  });

  describe('[P1] Disabled State', () => {
    it('disables all section controls when disabled', () => {
      renderWithForm(undefined, { disabled: true });

      // Chunking controls
      const comboboxes = screen.getAllByRole('combobox');
      expect(comboboxes[0]).toBeDisabled();

      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[0]).toBeDisabled(); // chunk_size
      expect(inputs[1]).toBeDisabled(); // chunk_overlap

      // Retrieval controls
      expect(inputs[2]).toBeDisabled(); // top_k
      expect(comboboxes[1]).toBeDisabled(); // method dropdown
      expect(screen.getByRole('switch')).toBeDisabled(); // MMR switch

      // Generation controls
      expect(inputs[inputs.length - 1]).toBeDisabled(); // max_tokens
    });

    it('disables Reset to Defaults button when disabled', () => {
      renderWithForm(undefined, { disabled: true });

      expect(screen.getByRole('button', { name: /reset to defaults/i })).toBeDisabled();
    });
  });

  describe('[P2] Form Validation Integration', () => {
    it('allows valid form values', () => {
      renderWithForm({
        chunking: {
          strategy: ChunkingStrategy.RECURSIVE,
          chunk_size: 512,
          chunk_overlap: 50,
        },
        retrieval: {
          top_k: 10,
          similarity_threshold: 0.7,
          method: RetrievalMethod.VECTOR,
          mmr_enabled: false,
          mmr_lambda: 0.5,
        },
        generation: {
          temperature: 0.7,
          top_p: 1.0,
          max_tokens: 4096,
        },
      });

      // Should render without error messages
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('[P2] Interaction Flow', () => {
    it('allows changing values across all sections', async () => {
      const user = userEvent.setup();
      renderWithForm();

      // Change chunking strategy
      const strategyCombo = screen.getAllByRole('combobox')[0];
      await user.click(strategyCombo);

      // Wait for dropdown and use getAllByText to handle multiple elements
      await waitFor(() => {
        expect(screen.getAllByText('Semantic').length).toBeGreaterThanOrEqual(1);
      });

      // Click the visible option in the portal
      const semanticOptions = screen.getAllByText('Semantic');
      await user.click(semanticOptions[semanticOptions.length - 1]);

      // Change MMR toggle
      const mmrSwitch = screen.getByRole('switch');
      await user.click(mmrSwitch);

      // Verify changes
      await waitFor(() => {
        expect(strategyCombo).toHaveTextContent(/semantic/i);
        expect(mmrSwitch).toBeChecked();
      });
    });
  });
});
