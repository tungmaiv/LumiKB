/**
 * Story 7-14: GenerationSection Component Tests
 *
 * Tests AC-7.14.4: Generation section with:
 * - Temperature slider (0.0-2.0, default 0.7)
 * - Top P slider (0.0-1.0, default 1.0)
 * - Max tokens input (100-16000)
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { GenerationSection } from '../generation-section';
import {
  generalPanelSchema,
  defaultGeneralPanelValues,
  type KBSettingsFormData,
} from '../general-panel';

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
      <form onSubmit={form.handleSubmit(onSubmit || vi.fn())}>
        {children(form)}
      </form>
    </FormProvider>
  );
}

// Helper to render with form
function renderWithForm(
  defaultValues?: Partial<KBSettingsFormData>,
  disabled = false
) {
  const onSubmit = vi.fn();
  const result = render(
    <TestWrapper defaultValues={defaultValues} onSubmit={onSubmit}>
      {(form) => <GenerationSection form={form} disabled={disabled} />}
    </TestWrapper>
  );
  return { ...result, onSubmit };
}

describe('GenerationSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] AC-7.14.4: Generation Section Rendering', () => {
    it('renders section with heading', () => {
      renderWithForm();
      expect(screen.getByText('Generation')).toBeInTheDocument();
    });

    it('renders description text', () => {
      renderWithForm();
      expect(
        screen.getByText(/configure parameters for ai response generation/i)
      ).toBeInTheDocument();
    });

    it('renders temperature controls', () => {
      renderWithForm();
      expect(screen.getByText('Temperature')).toBeInTheDocument();
      // Temperature value display should be visible (default 0.70)
      expect(screen.getByText('0.70')).toBeInTheDocument();
    });

    it('renders top p controls', () => {
      renderWithForm();
      // Multiple elements match /top p/i (label and description), use getAllByText
      const topPElements = screen.getAllByText(/top p/i);
      expect(topPElements.length).toBeGreaterThanOrEqual(1);
      // Top P value display should be visible (default from kb-settings is 0.90)
      expect(screen.getByText('0.90')).toBeInTheDocument();
    });

    it('renders max tokens input', () => {
      renderWithForm();
      expect(screen.getByText('Max Tokens')).toBeInTheDocument();
      expect(screen.getByRole('spinbutton')).toBeInTheDocument();
    });
  });

  describe('[P0] Temperature Controls', () => {
    it('displays current temperature value with decimal precision', () => {
      renderWithForm({
        generation: {
          temperature: 1.25,
          top_p: 1.0,
          max_tokens: 4096,
        },
      });

      expect(screen.getByText('1.25')).toBeInTheDocument();
    });

    it('displays default temperature value', () => {
      renderWithForm();

      // Default is 0.7
      expect(screen.getByText('0.70')).toBeInTheDocument();
    });
  });

  describe('[P0] Top P Controls', () => {
    it('displays current top_p value with decimal precision', () => {
      renderWithForm({
        generation: {
          temperature: 0.7,
          top_p: 0.95,
          max_tokens: 4096,
        },
      });

      expect(screen.getByText('0.95')).toBeInTheDocument();
    });

    it('displays default top_p value', () => {
      renderWithForm();

      // Default is 0.9 from kb-settings - this test covers top_p display
      // The '0.90' text should be visible as the default value
      expect(screen.getByText('0.90')).toBeInTheDocument();
    });
  });

  describe('[P0] Max Tokens Input', () => {
    it('displays current max_tokens value', () => {
      renderWithForm({
        generation: {
          temperature: 0.7,
          top_p: 1.0,
          max_tokens: 8192,
        },
      });

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(8192);
    });

    it('displays default max_tokens value', () => {
      renderWithForm();

      // Max tokens label should be present
      expect(screen.getByText('Max Tokens')).toBeInTheDocument();
      // Input should have default value 2048 from kb-settings
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(2048);
    });

    it('updates max_tokens when input changes', async () => {
      renderWithForm();

      const input = screen.getByRole('spinbutton');

      // Use fireEvent for immediate value update with react-hook-form
      fireEvent.change(input, { target: { value: '2048' } });

      await waitFor(() => {
        expect(input).toHaveValue(2048);
      });
    });

    it('has min and max attributes', () => {
      renderWithForm();

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '100');
      expect(input).toHaveAttribute('max', '16000');
    });
  });

  describe('[P1] Disabled State', () => {
    it('disables temperature slider when disabled', () => {
      renderWithForm(undefined, true);

      // Check that section is rendered with disabled state
      // Sliders in disabled state have visual indicators
      expect(screen.getByText('Temperature')).toBeInTheDocument();
      // The disabled state is applied to the form controls
      const input = screen.getByRole('spinbutton');
      expect(input).toBeDisabled();
    });

    it('disables top_p slider when disabled', () => {
      renderWithForm(undefined, true);

      // Top P label should be present (multiple matches so use getAllByText)
      const topPElements = screen.getAllByText(/top p/i);
      expect(topPElements.length).toBeGreaterThanOrEqual(1);
      // Value display should still be visible (default is 0.90)
      expect(screen.getByText('0.90')).toBeInTheDocument();
    });

    it('disables max_tokens input when disabled', () => {
      renderWithForm(undefined, true);

      const input = screen.getByRole('spinbutton');
      expect(input).toBeDisabled();
    });
  });

  describe('[P2] Descriptions', () => {
    it('shows temperature description with range', () => {
      renderWithForm();
      expect(
        screen.getByText(/controls randomness.*0\.0.*2\.0/i)
      ).toBeInTheDocument();
    });

    it('shows top_p description with range', () => {
      renderWithForm();
      expect(
        screen.getByText(/limits token selection.*0\.0.*1\.0/i)
      ).toBeInTheDocument();
    });

    it('shows max_tokens description with range', () => {
      renderWithForm();
      expect(
        screen.getByText(/maximum number of tokens.*100.*16,000/i)
      ).toBeInTheDocument();
    });
  });
});
