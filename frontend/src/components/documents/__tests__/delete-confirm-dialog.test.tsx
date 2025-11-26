import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteConfirmDialog } from '../delete-confirm-dialog';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('DeleteConfirmDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    documentName: 'Test Document.pdf',
    documentId: 'doc-123',
    kbId: 'kb-456',
    onDeleted: vi.fn(),
    onError: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders dialog with document name', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('heading', { name: /delete document/i })).toBeInTheDocument();
      expect(screen.getByText(/"Test Document\.pdf"/)).toBeInTheDocument();
    });

    it('displays warning about permanent deletion', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByText(/This action cannot be undone/)).toBeInTheDocument();
    });

    it('shows what will be deleted', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByText(/Remove it from the Knowledge Base/)).toBeInTheDocument();
      expect(screen.getByText(/Delete all indexed chunks from search/)).toBeInTheDocument();
      expect(screen.getByText(/Delete the uploaded file/)).toBeInTheDocument();
    });

    it('renders Cancel and Delete buttons', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /delete document/i })).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      render(<DeleteConfirmDialog {...defaultProps} open={false} />);

      expect(screen.queryByText('Delete Document')).not.toBeInTheDocument();
    });
  });

  describe('Cancel Action', () => {
    it('calls onOpenChange(false) when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
    });

    it('does not call delete API when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('Delete Action - Success', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });
    });

    it('calls delete API with correct URL and method', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/knowledge-bases/kb-456/documents/doc-123',
          {
            method: 'DELETE',
            credentials: 'include',
          }
        );
      });
    });

    it('calls onDeleted callback on success', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onDeleted).toHaveBeenCalled();
      });
    });

    it('closes dialog on success', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('does not call onError on success', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onDeleted).toHaveBeenCalled();
      });
      expect(defaultProps.onError).not.toHaveBeenCalled();
    });
  });

  describe('Delete Action - Loading State', () => {
    beforeEach(() => {
      // Use a promise that doesn't resolve immediately
      mockFetch.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));
    });

    it('shows loading state when deleting', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      // Use getAllByText since button text contains "Deleting..."
      const deletingElements = screen.getAllByText(/deleting/i);
      expect(deletingElements.length).toBeGreaterThan(0);
    });

    it('disables Cancel button during deletion', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });

    it('disables Delete button during deletion', async () => {
      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      // Button text changes to "Deleting..."
      expect(screen.getByRole('button', { name: /deleting/i })).toBeDisabled();
    });
  });

  describe('Delete Action - Error Handling', () => {
    it('calls onError with message for PROCESSING_IN_PROGRESS error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            detail: {
              error: {
                code: 'PROCESSING_IN_PROGRESS',
                message: 'Cannot delete while processing',
              },
            },
          }),
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith(
          'Cannot delete while document is processing. Please wait.'
        );
      });
    });

    it('calls onError with message for ALREADY_DELETED error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            detail: {
              error: {
                code: 'ALREADY_DELETED',
                message: 'Document already deleted',
              },
            },
          }),
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith('Document has already been deleted.');
      });
    });

    it('calls onError with generic message for 400 with unknown error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            detail: {
              error: {
                code: 'UNKNOWN_ERROR',
                message: 'Something went wrong',
              },
            },
          }),
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith('Something went wrong');
      });
    });

    it('calls onError for 404 Not Found', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith('Document not found.');
      });
    });

    it('calls onError for unexpected errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith('An unexpected error occurred.');
      });
    });

    it('calls onError for network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalledWith('Network error. Please try again.');
      });
    });

    it('does not close dialog on error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
      });

      const user = userEvent.setup();
      render(<DeleteConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalled();
      });
      // onOpenChange should not be called with false on error
      expect(defaultProps.onOpenChange).not.toHaveBeenCalledWith(false);
    });
  });

  describe('Accessibility', () => {
    it('has accessible dialog role', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has dialog title', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('heading', { name: /delete document/i })).toBeInTheDocument();
    });

    it('has dialog description', () => {
      render(<DeleteConfirmDialog {...defaultProps} />);

      expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
    });
  });
});
