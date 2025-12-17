import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentList } from '../document-list';

// Mock PointerCapture methods for Radix UI compatibility with JSDOM
beforeAll(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
});

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

// Mock the document lifecycle hook
vi.mock('@/hooks/useDocumentLifecycle', () => ({
  useDocumentLifecycle: vi.fn(() => ({
    archiveDocument: { mutateAsync: vi.fn(), isPending: false },
    clearDocument: { mutateAsync: vi.fn(), isPending: false },
  })),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
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

  // Helper to open dropdown menu for a document and click Delete
  const openDropdownAndClickDelete = async (
    user: ReturnType<typeof userEvent.setup>,
    menuButtonIndex = 0
  ) => {
    const moreActionsButtons = screen.getAllByTitle('More actions');
    await user.click(moreActionsButtons[menuButtonIndex]);

    // Wait for dropdown to open and click Delete
    const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
    return deleteMenuItem;
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Delete Button Rendering', () => {
    it('renders more actions menu for each document', () => {
      render(<DocumentList {...defaultProps} />);

      // Each document should have a "More actions" dropdown trigger
      const moreActionsButtons = screen.getAllByTitle('More actions');
      expect(moreActionsButtons.length).toBe(3);
    });

    it('delete menu item is enabled for READY documents', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dropdown for first document (READY status)
      const moreActionsButtons = screen.getAllByTitle('More actions');
      await user.click(moreActionsButtons[0]);

      // Delete menu item should be enabled
      const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
      expect(deleteMenuItem).not.toHaveAttribute('data-disabled');
    });

    it('delete menu item is disabled for PROCESSING documents', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dropdown for second document (PROCESSING status)
      const moreActionsButtons = screen.getAllByTitle('More actions');
      await user.click(moreActionsButtons[1]);

      // Delete menu item should be disabled
      const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
      expect(deleteMenuItem).toHaveAttribute('data-disabled');
    });

    it('shows Delete option in dropdown menu', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dropdown
      const moreActionsButtons = screen.getAllByTitle('More actions');
      await user.click(moreActionsButtons[0]);

      // Should show Delete menu item
      expect(await screen.findByRole('menuitem', { name: /delete/i })).toBeInTheDocument();
    });
  });

  describe('Delete Confirmation Dialog', () => {
    it('opens confirmation dialog when delete menu item is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dropdown and click Delete for first document (READY status)
      const deleteMenuItem = await openDropdownAndClickDelete(user, 0);
      await user.click(deleteMenuItem);

      // Dialog should appear with document name
      expect(await screen.findByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /delete document/i })).toBeInTheDocument();
      expect(screen.getByText(/"Test Document 1"/)).toBeInTheDocument();
    });

    it('closes dialog when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} />);

      // Open dropdown and click Delete
      const deleteMenuItem = await openDropdownAndClickDelete(user, 0);
      await user.click(deleteMenuItem);

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

      // Open dropdown and click Delete
      const deleteMenuItem = await openDropdownAndClickDelete(user, 0);
      await user.click(deleteMenuItem);

      // Confirm deletion in dialog
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

      // Open dropdown and click Delete
      const deleteMenuItem = await openDropdownAndClickDelete(user, 0);
      await user.click(deleteMenuItem);

      // Confirm deletion in dialog
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

      // Open dropdown and click Delete
      const moreActionsButton = screen.getByTitle('More actions');
      await user.click(moreActionsButton);

      const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
      await user.click(deleteMenuItem);

      // Confirm deletion
      await user.click(screen.getByRole('button', { name: /delete document/i }));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/documents/doc-3'),
          expect.any(Object)
        );
      });
    });

    it('does not allow deletion of PROCESSING documents (menu item disabled)', async () => {
      const user = userEvent.setup();
      render(
        <DocumentList
          {...defaultProps}
          documents={[mockDocuments[1]]} // PROCESSING document only
        />
      );

      // Open dropdown
      const moreActionsButton = screen.getByTitle('More actions');
      await user.click(moreActionsButton);

      // Delete menu item should be disabled
      const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
      expect(deleteMenuItem).toHaveAttribute('data-disabled');
    });

    it('shows Cancel Processing option for PENDING documents instead of allowing direct delete', async () => {
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
        status: 200,
      });

      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} documents={[pendingDoc]} />);

      // Open dropdown
      const moreActionsButton = screen.getByTitle('More actions');
      await user.click(moreActionsButton);

      // Delete menu item should be disabled for PENDING documents (use Cancel Processing instead)
      const deleteMenuItem = await screen.findByRole('menuitem', { name: /delete/i });
      expect(deleteMenuItem).toHaveAttribute('data-disabled');

      // Should have Cancel Processing option available
      const cancelMenuItem = await screen.findByRole('menuitem', { name: /cancel processing/i });
      expect(cancelMenuItem).not.toHaveAttribute('data-disabled');
    });
  });

  describe('Cancel Processing functionality', () => {
    it('shows Cancel Processing option for PROCESSING documents', async () => {
      const user = userEvent.setup();
      render(
        <DocumentList
          {...defaultProps}
          documents={[mockDocuments[1]]} // PROCESSING document only
        />
      );

      // Open dropdown
      const moreActionsButton = screen.getByTitle('More actions');
      await user.click(moreActionsButton);

      // Cancel Processing menu item should be present and enabled
      const cancelMenuItem = await screen.findByRole('menuitem', { name: /cancel processing/i });
      expect(cancelMenuItem).not.toHaveAttribute('data-disabled');
    });

    it('calls cancel API when Cancel Processing is clicked', async () => {
      const processingDoc = {
        ...mockDocuments[0],
        id: 'doc-processing',
        name: 'Processing Doc',
        status: 'PROCESSING' as const,
      };

      // Update mock for PROCESSING status
      vi.mocked(
        (await import('@/lib/hooks/use-document-status-polling')).useDocumentStatusPolling
      ).mockReturnValue({
        status: 'PROCESSING',
        chunkCount: 0,
        error: null,
        isPolling: true,
        refetch: vi.fn(),
      });

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
      });

      const user = userEvent.setup();
      render(<DocumentList {...defaultProps} documents={[processingDoc]} />);

      // Open dropdown
      const moreActionsButton = screen.getByTitle('More actions');
      await user.click(moreActionsButton);

      // Click Cancel Processing
      const cancelMenuItem = await screen.findByRole('menuitem', { name: /cancel processing/i });
      await user.click(cancelMenuItem);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/documents/doc-processing/cancel'),
          expect.objectContaining({
            method: 'POST',
            credentials: 'include',
          })
        );
      });
    });
  });

  describe('Click event propagation', () => {
    it('dropdown menu click does not trigger document click', async () => {
      const onDocumentClick = vi.fn();
      const user = userEvent.setup();

      render(<DocumentList {...defaultProps} onDocumentClick={onDocumentClick} />);

      // Click More actions dropdown button
      const moreActionsButtons = screen.getAllByTitle('More actions');
      await user.click(moreActionsButtons[0]);

      // onDocumentClick should not be called when opening dropdown
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

    it('does not show action buttons in loading state', () => {
      render(<DocumentList {...defaultProps} isLoading />);

      // In loading state, no More actions buttons should be shown
      expect(screen.queryByTitle('More actions')).not.toBeInTheDocument();
    });
  });
});
