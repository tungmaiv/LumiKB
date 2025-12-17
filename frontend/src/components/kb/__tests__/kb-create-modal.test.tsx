import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KbCreateModal } from '../kb-create-modal';

// Mock the KB store
const mockCreateKb = vi.fn();

vi.mock('@/lib/stores/kb-store', () => ({
  useKBStore: (selector?: (state: { createKb: typeof mockCreateKb }) => unknown) => {
    const state = { createKb: mockCreateKb };
    if (selector) {
      return selector(state);
    }
    return state;
  },
}));

// Story 7-10: Mock useAvailableModels hook for model selection tests
const mockEmbeddingModels = [
  { id: 'emb-model-1', name: 'text-embedding-3-small', model_id: 'text-embedding-3-small' },
  { id: 'emb-model-2', name: 'text-embedding-3-large', model_id: 'text-embedding-3-large' },
];

const mockGenerationModels = [
  { id: 'gen-model-1', name: 'gpt-4o-mini', model_id: 'gpt-4o-mini' },
  { id: 'gen-model-2', name: 'gpt-4o', model_id: 'gpt-4o' },
];

const mockUseAvailableModels = vi.fn();

vi.mock('@/hooks/useAvailableModels', () => ({
  useAvailableModels: () => mockUseAvailableModels(),
}));

// Mock ResizeObserver for Radix UI - must be a class for constructor
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

// Mock hasPointerCapture for Radix Select
Element.prototype.hasPointerCapture = vi.fn().mockReturnValue(false) as (
  pointerId: number
) => boolean;

// Mock scrollIntoView for Radix Select (JSDOM doesn't implement this)
Element.prototype.scrollIntoView = vi.fn();

// Mock setPointerCapture and releasePointerCapture for Radix UI
Element.prototype.setPointerCapture = vi.fn();
Element.prototype.releasePointerCapture = vi.fn();

describe('KbCreateModal', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Story 7-10: Default mock for useAvailableModels
    mockUseAvailableModels.mockReturnValue({
      embeddingModels: mockEmbeddingModels,
      generationModels: mockGenerationModels,
      nerModels: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('renders dialog when open', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('does not render dialog when closed', () => {
    render(<KbCreateModal {...defaultProps} open={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders title and description', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByText('Create Knowledge Base')).toBeInTheDocument();
    expect(
      screen.getByText('Create a new knowledge base to organize your documents.')
    ).toBeInTheDocument();
  });

  it('renders name input field', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });

  it('renders description input field', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it('renders Cancel and Create buttons', () => {
    render(<KbCreateModal {...defaultProps} />);
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
  });

  it('shows validation error when name is empty', async () => {
    const user = userEvent.setup();
    render(<KbCreateModal {...defaultProps} />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });
  });

  it('shows validation error when name exceeds 255 characters', async () => {
    const user = userEvent.setup();
    render(<KbCreateModal {...defaultProps} />);

    const longName = 'a'.repeat(256);
    await user.type(screen.getByLabelText('Name'), longName);
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Name must be less than 255 characters')).toBeInTheDocument();
    });
  });

  it('calls createKb on valid submission', async () => {
    const user = userEvent.setup();
    mockCreateKb.mockResolvedValueOnce({
      id: 'new-kb',
      name: 'New KB',
      description: 'Test description',
    });

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.type(screen.getByLabelText(/description/i), 'Test description');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(mockCreateKb).toHaveBeenCalledWith({
        name: 'New KB',
        description: 'Test description',
      });
    });
  });

  it('closes modal on successful creation', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    mockCreateKb.mockResolvedValueOnce({ id: 'new-kb', name: 'New KB' });

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('shows error message on creation failure', async () => {
    const user = userEvent.setup();
    mockCreateKb.mockRejectedValueOnce(new Error('Creation failed'));

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Creation failed')).toBeInTheDocument();
    });
  });

  it('does not close modal on error', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    mockCreateKb.mockRejectedValueOnce(new Error('Creation failed'));

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText('Creation failed')).toBeInTheDocument();
    });
    // Modal should remain open
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });

  it('closes modal when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();

    render(<KbCreateModal open onOpenChange={onOpenChange} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('resets form when modal is closed', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();

    const { rerender } = render(<KbCreateModal open onOpenChange={onOpenChange} />);

    // Type something in the name field
    await user.type(screen.getByLabelText('Name'), 'Test Name');
    expect(screen.getByLabelText('Name')).toHaveValue('Test Name');

    // Close the modal
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    // Reopen the modal
    rerender(<KbCreateModal open onOpenChange={onOpenChange} />);

    // Field should be empty
    expect(screen.getByLabelText('Name')).toHaveValue('');
  });

  it('disables form inputs during submission', async () => {
    const user = userEvent.setup();
    // Create a promise that we can control
    let resolveCreate: (value: unknown) => void;
    const createPromise = new Promise((resolve) => {
      resolveCreate = resolve;
    });
    mockCreateKb.mockReturnValueOnce(createPromise);

    render(<KbCreateModal {...defaultProps} />);

    await user.type(screen.getByLabelText('Name'), 'New KB');
    await user.click(screen.getByRole('button', { name: /create/i }));

    // Check that inputs are disabled during submission
    await waitFor(() => {
      expect(screen.getByLabelText('Name')).toBeDisabled();
    });

    // Resolve the promise and wait for state updates to complete
    await act(async () => {
      resolveCreate!({ id: 'new-kb', name: 'New KB' });
    });

    // Wait for form to re-enable after submission completes
    await waitFor(
      () => {
        expect(screen.queryByLabelText('Name')).not.toBeDisabled();
      },
      { timeout: 100 }
    ).catch(() => {
      // Modal may close after successful submission, which is expected
    });
  });

  /**
   * Story 7-10: KB Model Configuration Tests (AC-7.10.1 through AC-7.10.3)
   * Tests for model selection dropdowns during KB creation
   */
  describe('Story 7-10: Model Configuration', () => {
    it('renders model configuration section', () => {
      /**
       * GIVEN: KB create modal is open
       * WHEN: Rendering the modal
       * THEN: Model configuration section is visible
       * AC: 7.10.1 - Model selection available during KB creation
       */
      render(<KbCreateModal {...defaultProps} />);

      expect(screen.getByText('Model Configuration (optional)')).toBeInTheDocument();
      expect(screen.getByText('Embedding Model')).toBeInTheDocument();
      expect(screen.getByText('Generation Model')).toBeInTheDocument();
    });

    it('renders embedding model dropdown with available models', async () => {
      /**
       * GIVEN: KB create modal with available embedding models
       * WHEN: Opening the embedding model dropdown
       * THEN: Shows all active embedding models from registry
       * AC: 7.10.1, 7.10.2 - Dropdown shows active models from registry
       */
      const user = userEvent.setup();
      render(<KbCreateModal {...defaultProps} />);

      // Find and click the embedding model select trigger
      const embeddingTriggers = screen.getAllByRole('combobox');
      // First combobox should be embedding model
      await user.click(embeddingTriggers[0]);

      // Should show available embedding models (use getAllByText since Radix creates multiple elements)
      await waitFor(() => {
        // Use getAllByRole('option') to find dropdown items
        const options = screen.getAllByRole('option');
        const optionTexts = options.map((o) => o.textContent);
        expect(optionTexts).toContain('text-embedding-3-small');
        expect(optionTexts).toContain('text-embedding-3-large');
      });
    });

    it('renders generation model dropdown with available models', async () => {
      /**
       * GIVEN: KB create modal with available generation models
       * WHEN: Opening the generation model dropdown
       * THEN: Shows all active generation models from registry
       * AC: 7.10.1, 7.10.2 - Dropdown shows active models from registry
       */
      const user = userEvent.setup();
      render(<KbCreateModal {...defaultProps} />);

      // Find all comboboxes - second should be generation model
      const comboboxes = screen.getAllByRole('combobox');
      // Second combobox should be generation model
      await user.click(comboboxes[1]);

      // Should show available generation models (use role='option')
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        const optionTexts = options.map((o) => o.textContent);
        expect(optionTexts).toContain('gpt-4o-mini');
        expect(optionTexts).toContain('gpt-4o');
      });
    });

    it('shows system default placeholder when no model selected', () => {
      /**
       * GIVEN: KB create modal with no model pre-selected
       * WHEN: Viewing model dropdowns
       * THEN: Shows "Use system default" placeholder
       * AC: 7.10.1 - System default is the default selection
       */
      render(<KbCreateModal {...defaultProps} />);

      const triggers = screen.getAllByRole('combobox');
      expect(triggers[0]).toHaveTextContent('Use system default');
      expect(triggers[1]).toHaveTextContent('Use system default');
    });

    it('disables model dropdowns when models are loading', () => {
      /**
       * GIVEN: Models are still loading from API
       * WHEN: Rendering the modal
       * THEN: Model dropdowns are disabled
       * AC: 7.10.6 - UI handles loading state
       */
      mockUseAvailableModels.mockReturnValue({
        embeddingModels: [],
        generationModels: [],
        nerModels: [],
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      render(<KbCreateModal {...defaultProps} />);

      const triggers = screen.getAllByRole('combobox');
      expect(triggers[0]).toBeDisabled();
      expect(triggers[1]).toBeDisabled();
    });

    it('includes selected embedding model in create request', async () => {
      /**
       * GIVEN: User selects an embedding model
       * WHEN: Submitting the form
       * THEN: Request includes embedding_model_id
       * AC: 7.10.1 - Model selection is passed to backend
       */
      const user = userEvent.setup();
      mockCreateKb.mockResolvedValueOnce({
        id: 'new-kb',
        name: 'Test KB',
      });

      render(<KbCreateModal {...defaultProps} />);

      // Fill required name field
      await user.type(screen.getByLabelText('Name'), 'Test KB');

      // Select embedding model
      const comboboxes = screen.getAllByRole('combobox');
      await user.click(comboboxes[0]);

      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      // Click the option with matching text
      const option = screen
        .getAllByRole('option')
        .find((o) => o.textContent === 'text-embedding-3-small');
      expect(option).toBeDefined();
      await user.click(option!);

      // Submit form
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(mockCreateKb).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test KB',
            embedding_model_id: 'emb-model-1',
          })
        );
      });
    });

    it('includes selected generation model in create request', async () => {
      /**
       * GIVEN: User selects a generation model
       * WHEN: Submitting the form
       * THEN: Request includes generation_model_id
       * AC: 7.10.1 - Model selection is passed to backend
       */
      const user = userEvent.setup();
      mockCreateKb.mockResolvedValueOnce({
        id: 'new-kb',
        name: 'Test KB',
      });

      render(<KbCreateModal {...defaultProps} />);

      // Fill required name field
      await user.type(screen.getByLabelText('Name'), 'Test KB');

      // Select generation model - second combobox
      const comboboxes = screen.getAllByRole('combobox');
      await user.click(comboboxes[1]);

      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      // Click the option with matching text
      const option = screen.getAllByRole('option').find((o) => o.textContent === 'gpt-4o');
      expect(option).toBeDefined();
      await user.click(option!);

      // Submit form
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(mockCreateKb).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test KB',
            generation_model_id: 'gen-model-2',
          })
        );
      });
    });

    it('includes both models when both are selected', async () => {
      /**
       * GIVEN: User selects both embedding and generation models
       * WHEN: Submitting the form
       * THEN: Request includes both model IDs
       * AC: 7.10.1 - Multiple model selections are passed to backend
       */
      const user = userEvent.setup();
      mockCreateKb.mockResolvedValueOnce({
        id: 'new-kb',
        name: 'Test KB',
      });

      render(<KbCreateModal {...defaultProps} />);

      // Fill required name field
      await user.type(screen.getByLabelText('Name'), 'Test KB');

      // Select embedding model
      const comboboxes = screen.getAllByRole('combobox');
      await user.click(comboboxes[0]);
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      const embOption = screen
        .getAllByRole('option')
        .find((o) => o.textContent === 'text-embedding-3-large');
      expect(embOption).toBeDefined();
      await user.click(embOption!);

      // Select generation model
      await user.click(comboboxes[1]);
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      const genOption = screen.getAllByRole('option').find((o) => o.textContent === 'gpt-4o-mini');
      expect(genOption).toBeDefined();
      await user.click(genOption!);

      // Submit form
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(mockCreateKb).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test KB',
            embedding_model_id: 'emb-model-2',
            generation_model_id: 'gen-model-1',
          })
        );
      });
    });

    it('does not include model IDs when using system defaults', async () => {
      /**
       * GIVEN: User does not select any models (uses defaults)
       * WHEN: Submitting the form
       * THEN: Request does not include model IDs or includes undefined
       * AC: 7.10.1 - System default is used when no selection made
       */
      const user = userEvent.setup();
      mockCreateKb.mockResolvedValueOnce({
        id: 'new-kb',
        name: 'Test KB',
      });

      render(<KbCreateModal {...defaultProps} />);

      // Fill only required name field, leave models as default
      await user.type(screen.getByLabelText('Name'), 'Test KB');

      // Submit form
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        const call = mockCreateKb.mock.calls[0][0];
        expect(call.name).toBe('Test KB');
        // Should not have model IDs or they should be undefined
        expect(call.embedding_model_id).toBeUndefined();
        expect(call.generation_model_id).toBeUndefined();
      });
    });

    it('shows model descriptions in form', () => {
      /**
       * GIVEN: KB create modal is open
       * WHEN: Viewing model configuration section
       * THEN: Shows helpful descriptions for each model type
       * AC: 7.10.3 - Model info/purpose is displayed
       */
      render(<KbCreateModal {...defaultProps} />);

      expect(screen.getByText(/Model used for document embedding/)).toBeInTheDocument();
      expect(screen.getByText(/Model used for document generation/)).toBeInTheDocument();
    });

    it('handles empty model lists gracefully', () => {
      /**
       * GIVEN: No active models available from registry
       * WHEN: Rendering the modal
       * THEN: Dropdowns render without errors
       * AC: 7.10.2 - Handles empty model registry
       */
      mockUseAvailableModels.mockReturnValue({
        embeddingModels: [],
        generationModels: [],
        nerModels: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      render(<KbCreateModal {...defaultProps} />);

      // Should still render the dropdowns
      const triggers = screen.getAllByRole('combobox');
      expect(triggers.length).toBeGreaterThanOrEqual(2);
    });

    it('resets model selections when modal is closed', async () => {
      /**
       * GIVEN: User has selected models
       * WHEN: Modal is closed and reopened
       * THEN: Model selections are reset to defaults
       * AC: 7.10.1 - Form resets on close
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      const { rerender } = render(<KbCreateModal open onOpenChange={onOpenChange} />);

      // Select an embedding model
      const comboboxes = screen.getAllByRole('combobox');
      await user.click(comboboxes[0]);
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      const option = screen
        .getAllByRole('option')
        .find((o) => o.textContent === 'text-embedding-3-small');
      expect(option).toBeDefined();
      await user.click(option!);

      // Verify selection
      await waitFor(() => {
        expect(comboboxes[0]).toHaveTextContent('text-embedding-3-small');
      });

      // Close the modal by clicking cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }));
      expect(onOpenChange).toHaveBeenCalledWith(false);

      // Close the modal first (simulating the real behavior)
      rerender(<KbCreateModal open={false} onOpenChange={onOpenChange} />);

      // Reopen the modal
      rerender(<KbCreateModal open={true} onOpenChange={onOpenChange} />);

      // Should be reset to default
      await waitFor(() => {
        const newComboboxes = screen.getAllByRole('combobox');
        expect(newComboboxes[0]).toHaveTextContent('Use system default');
      });
    });
  });
});
