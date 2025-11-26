import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentList } from '../document-list';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock toast utility
vi.mock('@/lib/utils/document-toast', () => ({
  showDocumentStatusToast: vi.fn(),
}));

// Mock the status polling hook to return the initial status
vi.mock('@/lib/hooks/use-document-status-polling', () => ({
  useDocumentStatusPolling: vi.fn((docId, kbId, initialStatus) => ({
    status: initialStatus,
    chunkCount: initialStatus === 'READY' ? 10 : 0,
    error: initialStatus === 'FAILED' ? 'Processing failed' : null,
    isPolling: false,
    refetch: vi.fn(),
  })),
}));

// Mock date-fns to return consistent dates
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 hours ago'),
}));

const mockDocuments = [
  {
    id: 'doc-1',
    name: 'Test Document 1',
    original_filename: 'test1.pdf',
    mime_type: 'application/pdf',
    file_size_bytes: 1024000,
    status: 'READY' as const,
    chunk_count: 10,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    uploaded_by: 'user-123',
    uploader_email: 'test@example.com',
  },
  {
    id: 'doc-2',
    name: 'Processing Doc',
    original_filename: 'processing.pdf',
    mime_type: 'application/pdf',
    file_size_bytes: 2048000,
    status: 'PROCESSING' as const,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 'doc-3',
    name: 'Failed Document',
    original_filename: 'failed.pdf',
    mime_type: 'application/pdf',
    file_size_bytes: 512000,
    status: 'FAILED' as const,
    last_error: 'Parse error',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
];

describe('DocumentList - Delete Functionality', () => {
  const defaultProps = {
    documents: mockDocuments,
    kbId: 'kb-test-123',
    onDeleted: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Delete Button Rendering', () => {
    it('renders delete button for each document', () => {
      render(<DocumentList {...defaultProps} />);

      // Each document should have a delete button with TrashIcon
      const deleteButtons = screen.getAllByTitle(/delete/i);
      expect(deleteButtons.length).toBe(3);
    });

    it('delete button is enabled for READY documents', () => {
      render(<DocumentList {...defaultProps} />);

      // Find the delete button in the first document row (READY status)
      const docRows = screen
        .getAllByRole('button', { name: /delete document/i })
        .filter((btn) => !btn.hasAttribute('disabled'));

      // READY and FAILED documents should have enabled delete buttons
      expect(docRows.length).toBe(2);
    });

    it('delete button is disabled for PROCESSING documents', () => {
      render(<DocumentList {...defaultProps} />);

      const disabledDeleteButton = screen.getByTitle('Cannot delete while processing');
      expect(disabledDeleteButton).toBeDisabled();
    });

    it('shows correct tooltip for disabled PROCESSING document', () => {
      render(<DocumentList {...defaultProps} />);

      const disabledButton = screen.getByTitle('Cannot delete while processing');
      expect(disabledButton).toBeInTheDocument();
    });
  });

  describe('Delete Confirmation Dialog', () => {
    it('opens confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Click delete button for first document (READY status)
      const deleteButtons = screen.getAllByTitle('Delete document');
      await user.click(deleteButtons[0]);

      // Dialog should appear with document name
      expect(await screen.findByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /delete document/i })).toBeInTheDocument();
      expect(screen.getByText(/"Test Document 1"/)).toBeInTheDocument();
    });

    it('closes dialog when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dialog
      const deleteButtons = screen.getAllByTitle('Delete document');
      await user.click(deleteButtons[0]);

      // Click Cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Delete API Call', () => {
    it('calls delete API with correct URL on confirmation', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dialog and confirm
      const deleteButtons = screen.getAllByTitle('Delete document');
      await user.click(deleteButtons[0]);
      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/knowledge-bases/kb-test-123/documents/doc-1',
          expect.objectContaining({
            method: 'DELETE',
            credentials: 'include',
          })
        );
      });
    });

    it('calls onDeleted callback on successful delete', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dialog and confirm
      const deleteButtons = screen.getAllByTitle('Delete document');
      await user.click(deleteButtons[0]);
      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(defaultProps.onDeleted).toHaveBeenCalledWith('doc-1');
      });
    });
  });

  describe('Delete for Different Statuses', () => {
    it('allows deletion of FAILED documents', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      const user = userEvent.setup();
      render(
        <DocumentList
          {...defaultProps}
          documents={[mockDocuments[2]]} // FAILED document only
        />
      );

      // Click delete button
      const deleteButton = screen.getByTitle('Delete document');
      await user.click(deleteButton);

      // Confirm deletion
      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/documents/doc-3'),
          expect.any(Object)
        );
      });
    });

    it('does not allow deletion of PROCESSING documents (button disabled)', async () => {
      const user = userEvent.setup();
      render(
        <DocumentList
          {...defaultProps}
          documents={[mockDocuments[1]]} // PROCESSING document only
        />
      );

      const deleteButton = screen.getByTitle('Cannot delete while processing');
      expect(deleteButton).toBeDisabled();

      // Clicking disabled button should not open dialog
      await user.click(deleteButton);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('allows deletion of PENDING documents', async () => {
      const pendingDoc = {
        ...mockDocuments[0],
        id: 'doc-pending',
        name: 'Pending Doc',
        status: 'PENDING' as const,
      };

      // Update mock for PENDING status
      vi.mocked(
        (await import('@/lib/hooks/use-document-status-polling')).useDocumentStatusPolling
      ).mockReturnValue({
        status: 'PENDING',
        chunkCount: 0,
        error: null,
        isPolling: false,
        refetch: vi.fn(),
      });

      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
      });

      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} documents={[pendingDoc]} />);

      const deleteButton = screen.getByTitle('Delete document');
      expect(deleteButton).not.toBeDisabled();
    });
  });

  describe('Click event propagation', () => {
    it('delete button click does not trigger document click', async () => {
      const onDocumentClick = vi.fn();
      const user = userEvent.setup();

      render(<DocumentList {...defaultProps} onDocumentClick={onDocumentClick} />);

      // Click delete button
      const deleteButtons = screen.getAllByTitle('Delete document');
      await user.click(deleteButtons[0]);

      // onDocumentClick should not be called
      expect(onDocumentClick).not.toHaveBeenCalled();
    });
  });

  describe('Empty state', () => {
    it('shows empty message when no documents', () => {
      render(<DocumentList {...defaultProps} documents={[]} />);

      expect(screen.getByText('No documents uploaded yet')).toBeInTheDocument();
    });
  });

  describe('Loading state', () => {
    it('shows loading skeleton when isLoading is true', () => {
      render(<DocumentList {...defaultProps} isLoading />);

      // Should show skeleton placeholders
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('does not show delete buttons in loading state', () => {
      render(<DocumentList {...defaultProps} isLoading />);

      expect(screen.queryByTitle(/delete/i)).not.toBeInTheDocument();
    });
  });
});
