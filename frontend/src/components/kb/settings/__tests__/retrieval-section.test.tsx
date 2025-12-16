/**
 * Story 7-14: RetrievalSection Component Tests
 *
 * Tests AC-7.14.3: Retrieval section with:
 * - Top K slider (1-100, default 10)
 * - Similarity threshold slider (0.0-1.0, default 0.7)
 * - Method dropdown (Vector, Hybrid, HyDE)
 * - MMR toggle with lambda slider
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { RetrievalSection } from '../retrieval-section';
import {
  generalPanelSchema,
  defaultGeneralPanelValues,
  type KBSettingsFormData,
} from '../general-panel';
import { RetrievalMethod } from '@/types/kb-settings';

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
      {(form) => <RetrievalSection form={form} disabled={disabled} />}
    </TestWrapper>
  );
  return { ...result, onSubmit };
}

describe('RetrievalSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] AC-7.14.3: Retrieval Section Rendering', () => {
    it('renders section with heading', () => {
      renderWithForm();
      expect(screen.getByText('Retrieval')).toBeInTheDocument();
    });

    it('renders description text', () => {
      renderWithForm();
      expect(
        screen.getByText(/configure how relevant documents are retrieved/i)
      ).toBeInTheDocument();
    });

    it('renders top k controls', () => {
      renderWithForm();
      expect(screen.getByText('Top K Results')).toBeInTheDocument();
      // Check for spinbutton input
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs.length).toBeGreaterThanOrEqual(1);
    });

    it('renders similarity threshold controls', () => {
      renderWithForm();
      expect(screen.getByText('Similarity Threshold')).toBeInTheDocument();
      // Slider value display should be visible
      expect(screen.getByText('0.70')).toBeInTheDocument();
    });

    it('renders method dropdown', () => {
      renderWithForm();
      expect(screen.getByText('Retrieval Method')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('renders MMR toggle', () => {
      renderWithForm();
      expect(screen.getByText(/maximal marginal relevance/i)).toBeInTheDocument();
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
  });

  describe('[P0] Top K Controls', () => {
    it('displays current top_k value', () => {
      renderWithForm({
        retrieval: {
          top_k: 25,
          similarity_threshold: 0.7,
          method: RetrievalMethod.VECTOR,
          mmr_enabled: false,
          mmr_lambda: 0.5,
        },
      });

      // First spinbutton is top_k
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[0]).toHaveValue(25);
    });

    it('updates top_k when input changes', async () => {
      renderWithForm();

      const inputs = screen.getAllByRole('spinbutton');
      const topKInput = inputs[0];

      // Use fireEvent for immediate value update with react-hook-form
      fireEvent.change(topKInput, { target: { value: '50' } });

      await waitFor(() => {
        expect(topKInput).toHaveValue(50);
      });
    });

    it('clamps top_k to max when exceeds limit', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const inputs = screen.getAllByRole('spinbutton');
      const topKInput = inputs[0];

      await user.clear(topKInput);
      await user.type(topKInput, '150');

      // Should clamp to max (100)
      await waitFor(() => {
        expect(topKInput).toHaveValue(100);
      });
    });
  });

  describe('[P0] Similarity Threshold', () => {
    it('displays current threshold value with decimal precision', () => {
      renderWithForm({
        retrieval: {
          top_k: 10,
          similarity_threshold: 0.85,
          method: RetrievalMethod.VECTOR,
          mmr_enabled: false,
          mmr_lambda: 0.5,
        },
      });

      expect(screen.getByText('0.85')).toBeInTheDocument();
    });
  });

  describe('[P0] Method Dropdown', () => {
    it('shows all method options when opened', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Radix Select renders options in a portal - use getAllByText to handle native select + portal
      await waitFor(() => {
        expect(screen.getAllByText('Vector').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('Hybrid').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('HyDE').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('displays current method value', () => {
      renderWithForm({
        retrieval: {
          top_k: 10,
          similarity_threshold: 0.7,
          method: RetrievalMethod.HYBRID,
          mmr_enabled: false,
          mmr_lambda: 0.5,
        },
      });

      expect(screen.getByRole('combobox')).toHaveTextContent(/hybrid/i);
    });

    it('changes method when option selected', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getAllByText('HyDE').length).toBeGreaterThanOrEqual(1);
      });

      // Click the visible option in the portal (last one is typically the portal item)
      const hydeOptions = screen.getAllByText('HyDE');
      await user.click(hydeOptions[hydeOptions.length - 1]);

      await waitFor(() => {
        expect(trigger).toHaveTextContent(/hyde/i);
      });
    });
  });

  describe('[P0] MMR Toggle and Lambda', () => {
    it('MMR toggle is off by default', () => {
      renderWithForm();

      const toggle = screen.getByRole('switch');
      expect(toggle).not.toBeChecked();
    });

    it('hides MMR lambda slider when MMR is disabled', () => {
      renderWithForm();

      expect(screen.queryByText('MMR Lambda')).not.toBeInTheDocument();
    });

    it('shows MMR lambda slider when MMR is enabled', () => {
      renderWithForm({
        retrieval: {
          top_k: 10,
          similarity_threshold: 0.7,
          method: RetrievalMethod.VECTOR,
          mmr_enabled: true,
          mmr_lambda: 0.5,
        },
      });

      expect(screen.getByText('MMR Lambda')).toBeInTheDocument();
      expect(screen.getByText('0.50')).toBeInTheDocument();
    });

    it('toggles MMR when switch is clicked', async () => {
      const user = userEvent.setup();
      renderWithForm();

      const toggle = screen.getByRole('switch');
      expect(toggle).not.toBeChecked();

      await user.click(toggle);

      await waitFor(() => {
        expect(toggle).toBeChecked();
        expect(screen.getByText('MMR Lambda')).toBeInTheDocument();
      });
    });

    it('displays MMR lambda value with correct precision', () => {
      renderWithForm({
        retrieval: {
          top_k: 10,
          similarity_threshold: 0.7,
          method: RetrievalMethod.VECTOR,
          mmr_enabled: true,
          mmr_lambda: 0.75,
        },
      });

      expect(screen.getByText('0.75')).toBeInTheDocument();
    });
  });

  describe('[P1] Disabled State', () => {
    it('disables top_k input when disabled', () => {
      renderWithForm(undefined, true);

      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs[0]).toBeDisabled();
    });

    it('disables method dropdown when disabled', () => {
      renderWithForm(undefined, true);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeDisabled();
    });

    it('disables MMR switch when disabled', () => {
      renderWithForm(undefined, true);

      const toggle = screen.getByRole('switch');
      expect(toggle).toBeDisabled();
    });
  });

  describe('[P2] Descriptions', () => {
    it('shows top_k description with range', () => {
      renderWithForm();
      expect(
        screen.getByText(/maximum number of results to retrieve.*1.*100/i)
      ).toBeInTheDocument();
    });

    it('shows similarity threshold description', () => {
      renderWithForm();
      expect(
        screen.getByText(/minimum similarity score.*0\.0.*1\.0/i)
      ).toBeInTheDocument();
    });

    it('shows method description', () => {
      renderWithForm();
      expect(
        screen.getByText(/search strategy.*vector.*hybrid.*hyde/i)
      ).toBeInTheDocument();
    });

    it('shows MMR description', () => {
      renderWithForm();
      expect(
        screen.getByText(/diversify results to reduce redundancy/i)
      ).toBeInTheDocument();
    });
  });
});
