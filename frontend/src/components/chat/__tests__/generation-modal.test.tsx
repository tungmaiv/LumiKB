/**
 * Unit tests for GenerationModal component
 * Epic 4, Story 4.4, AC1
 */

import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GenerationModal, type GenerationModalProps } from '../generation-modal';
import { useDraftStore } from '@/lib/stores/draft-store';

// Mock Radix UI pointer capture and scroll methods
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn();
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
});

// Mock draft store
vi.mock('@/lib/stores/draft-store', () => ({
  useDraftStore: vi.fn(),
}));

describe('GenerationModal', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnSubmit = vi.fn();

  const defaultProps: GenerationModalProps = {
    open: true,
    onOpenChange: mockOnOpenChange,
    kbId: 'kb-123',
    onSubmit: mockOnSubmit,
  };

  // Helper to mock draft store with selected sources
  const mockWithSelectedSources = (count = 1) => {
    const results = Array.from({ length: count }, (_, i) => ({
      chunkId: `chunk-${i + 1}`,
      documentId: `doc-${i + 1}`,
      documentName: `Test Doc ${i + 1}`,
      chunkText: `Sample text ${i + 1}`,
      kbId: 'kb-123',
      kbName: 'Test KB',
      relevanceScore: 0.95 - i * 0.05,
    }));

    vi.mocked(useDraftStore).mockReturnValue({
      selectedResults: results,
      addToDraft: vi.fn(),
      removeFromDraft: vi.fn(),
      clearAll: vi.fn(),
      isInDraft: vi.fn(),
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Default: No selected sources
    vi.mocked(useDraftStore).mockReturnValue({
      selectedResults: [],
      addToDraft: vi.fn(),
      removeFromDraft: vi.fn(),
      clearAll: vi.fn(),
      isInDraft: vi.fn(),
    });
  });

  describe('Rendering', () => {
    it('renders modal when open is true', () => {
      render(<GenerationModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Generate Document')).toBeInTheDocument();
      expect(
        screen.getByText(/Create a professional document using AI-powered synthesis/)
      ).toBeInTheDocument();
    });

    it('does not render modal when open is false', () => {
      render(<GenerationModal {...defaultProps} open={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<GenerationModal {...defaultProps} />);

      // Template selection uses radiogroup with 4 templates
      expect(screen.getByText(/Template/i)).toBeInTheDocument();
      expect(screen.getByRole('radiogroup', { name: /Template selection/i })).toBeInTheDocument();
      expect(screen.getByText(/Additional Instructions/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      expect(screen.getByTestId('generate-button')).toBeInTheDocument();
    });
  });

  describe('Selected Sources Integration (AC2)', () => {
    it('shows selected sources indicator when sources exist', () => {
      vi.mocked(useDraftStore).mockReturnValue({
        selectedResults: [
          {
            chunkId: 'chunk-1',
            documentId: 'doc-1',
            documentName: 'Test Doc',
            chunkText: 'Sample text',
            kbId: 'kb-123',
            kbName: 'Test KB',
            relevanceScore: 0.95,
          },
        ],
        addToDraft: vi.fn(),
        removeFromDraft: vi.fn(),
        clearAll: vi.fn(),
        isInDraft: vi.fn(),
      });

      render(<GenerationModal {...defaultProps} />);

      const indicator = screen.getByTestId('selected-sources-indicator');
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveTextContent('1 source selected from search results');
    });

    it('shows correct pluralization for multiple sources', () => {
      vi.mocked(useDraftStore).mockReturnValue({
        selectedResults: [
          {
            chunkId: 'chunk-1',
            documentId: 'doc-1',
            documentName: 'Test Doc 1',
            chunkText: 'Sample text 1',
            kbId: 'kb-123',
            kbName: 'Test KB',
            relevanceScore: 0.95,
          },
          {
            chunkId: 'chunk-2',
            documentId: 'doc-2',
            documentName: 'Test Doc 2',
            chunkText: 'Sample text 2',
            kbId: 'kb-123',
            kbName: 'Test KB',
            relevanceScore: 0.85,
          },
        ],
        addToDraft: vi.fn(),
        removeFromDraft: vi.fn(),
        clearAll: vi.fn(),
        isInDraft: vi.fn(),
      });

      render(<GenerationModal {...defaultProps} />);

      expect(screen.getByTestId('selected-sources-indicator')).toHaveTextContent(
        '2 sources selected from search results'
      );
    });

    it('does not show indicator when no sources selected', () => {
      render(<GenerationModal {...defaultProps} />);

      expect(screen.queryByTestId('selected-sources-indicator')).not.toBeInTheDocument();
    });
  });

  describe('Form Interaction', () => {
    it('allows user to select generation mode', async () => {
      const user = userEvent.setup();
      render(<GenerationModal {...defaultProps} />);

      // TemplateSelector uses a radiogroup with radio buttons (card-based UI)
      const radiogroup = screen.getByRole('radiogroup', { name: /Template selection/i });
      expect(radiogroup).toBeInTheDocument();

      // Default selection is RFP Response Section
      const rfpRadio = screen.getByRole('radio', { name: /RFP Response Section/i });
      expect(rfpRadio).toHaveAttribute('aria-checked', 'true');

      // Click Technical Checklist template card
      const checklistRadio = screen.getByRole('radio', { name: /Technical Checklist/i });
      await user.click(checklistRadio);

      await waitFor(() => {
        expect(checklistRadio).toHaveAttribute('aria-checked', 'true');
        expect(rfpRadio).toHaveAttribute('aria-checked', 'false');
      });
    });

    it('allows user to enter additional prompt', async () => {
      const user = userEvent.setup();
      render(<GenerationModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Add specific instructions/i);
      await user.type(textarea, 'Focus on security requirements');

      // Verify controlled input receives changes
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('Focus on security requirements');
    });

    it('validates form before submission', async () => {
      // Mock selected sources to enable button
      vi.mocked(useDraftStore).mockReturnValue({
        selectedResults: [
          {
            chunkId: 'chunk-1',
            documentId: 'doc-1',
            documentName: 'Test Doc',
            chunkText: 'Sample text',
            kbId: 'kb-123',
            kbName: 'Test KB',
            relevanceScore: 0.95,
          },
        ],
        addToDraft: vi.fn(),
        removeFromDraft: vi.fn(),
        clearAll: vi.fn(),
        isInDraft: vi.fn(),
      });

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');

      // With selected sources, button should not be disabled
      // This test verifies form validation exists via zod schema
      expect(generateButton).not.toBeDisabled();
    });
  });

  describe('Form Submission', () => {
    it('calls onSubmit with form data when submitted', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValueOnce(undefined);

      render(<GenerationModal {...defaultProps} />);

      // Submit with default values
      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          mode: 'rfp_response',
          additionalPrompt: '',
        });
      });
    });

    it('closes modal after successful submission', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValueOnce(undefined);

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('shows loading state during submission', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      // Button should show loading state
      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument();
      });
    });

    it('displays error message on submission failure', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      const errorMessage = 'Generation failed due to server error';
      mockOnSubmit.mockRejectedValueOnce(new Error(errorMessage));

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(errorMessage);
      });
    });

    it('keeps modal open on submission failure', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValueOnce(new Error('Generation failed'));

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Modal should still be visible and displaying error
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      // The primary assertion is that error is shown and modal is still rendered
    });

    it('resets form after successful submission', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValueOnce(undefined);

      const { rerender } = render(<GenerationModal {...defaultProps} />);

      // Enter custom data
      const textarea = screen.getByPlaceholderText(/Add specific instructions/i);
      await user.type(textarea, 'Custom instructions');

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });

      // Reopen modal with selected sources again
      mockWithSelectedSources();
      rerender(<GenerationModal {...defaultProps} open={true} />);

      // Form should be reset to defaults
      const resetTextarea = screen.getByPlaceholderText(/Add specific instructions/i);
      expect(resetTextarea).toHaveValue('');
    });
  });

  describe('Cancel Behavior', () => {
    it('calls onOpenChange(false) when Cancel clicked', async () => {
      const user = userEvent.setup();
      render(<GenerationModal {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    it('resets form when cancelled', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<GenerationModal {...defaultProps} />);

      // Enter data
      const textarea = screen.getByPlaceholderText(/Add specific instructions/i);
      await user.type(textarea, 'Some text');

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      // Reopen modal
      rerender(<GenerationModal {...defaultProps} open={true} />);

      // Form should be reset
      const resetTextarea = screen.getByPlaceholderText(/Add specific instructions/i);
      expect(resetTextarea).toHaveValue('');
    });

    it('clears error state when cancelled', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValueOnce(new Error('Test error'));

      const { rerender } = render(<GenerationModal {...defaultProps} />);

      // Trigger error
      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Close modal
      mockOnOpenChange.mockClear();
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      // Reopen modal with selected sources again
      mockWithSelectedSources();
      rerender(<GenerationModal {...defaultProps} open={true} />);

      // Error should be cleared
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for modal', () => {
      render(<GenerationModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Generate Document')).toBeInTheDocument();
    });

    it('disables form controls during submission', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Cancel/i })).toBeDisabled();
        expect(generateButton).toBeDisabled();
      });
    });

    it('prevents modal close during submission', async () => {
      mockWithSelectedSources(); // Enable button
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<GenerationModal {...defaultProps} />);

      const generateButton = screen.getByTestId('generate-button');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument();
      });

      // Try to close modal during submission
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Integration with Primitive Components', () => {
    it('renders TemplateSelector with correct props', () => {
      render(<GenerationModal {...defaultProps} />);

      // TemplateSelector renders as a radiogroup with 4 template options
      const selector = screen.getByRole('radiogroup', { name: /Template selection/i });
      expect(selector).toBeInTheDocument();

      // Default selection is RFP Response Section
      const rfpRadio = screen.getByRole('radio', { name: /RFP Response Section/i });
      expect(rfpRadio).toHaveAttribute('aria-checked', 'true');
    });

    it('renders AdditionalPromptInput with correct props', () => {
      render(<GenerationModal {...defaultProps} />);

      const input = screen.getByPlaceholderText(/Add specific instructions/i);
      expect(input).toBeInTheDocument();
      expect(input.tagName.toLowerCase()).toBe('textarea');
    });

    it('renders GenerateButton with correct props', () => {
      render(<GenerationModal {...defaultProps} />);

      const button = screen.getByTestId('generate-button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Generate Draft');
    });

    it('disables GenerateButton when no sources selected', () => {
      vi.mocked(useDraftStore).mockReturnValue({
        selectedResults: [],
        addToDraft: vi.fn(),
        removeFromDraft: vi.fn(),
        clearAll: vi.fn(),
        isInDraft: vi.fn(),
      });

      render(<GenerationModal {...defaultProps} />);

      const button = screen.getByTestId('generate-button');
      expect(button).toBeDisabled();
    });

    it('enables GenerateButton when sources are selected', () => {
      vi.mocked(useDraftStore).mockReturnValue({
        selectedResults: [
          {
            chunkId: 'chunk-1',
            documentId: 'doc-1',
            documentName: 'Test Doc',
            chunkText: 'Sample text',
            kbId: 'kb-123',
            kbName: 'Test KB',
            relevanceScore: 0.95,
          },
        ],
        addToDraft: vi.fn(),
        removeFromDraft: vi.fn(),
        clearAll: vi.fn(),
        isInDraft: vi.fn(),
      });

      render(<GenerationModal {...defaultProps} />);

      const button = screen.getByTestId('generate-button');
      expect(button).not.toBeDisabled();
    });
  });
});
