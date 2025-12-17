import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentEditTagsModal } from '../document-edit-tags-modal';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('DocumentEditTagsModal', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    kbId: 'kb-123',
    documentId: 'doc-456',
    documentName: 'Test Document',
    currentTags: ['python', 'api'],
    onTagsUpdated: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('rendering', () => {
    it('renders modal with title and description', () => {
      render(<DocumentEditTagsModal {...defaultProps} />);

      expect(screen.getByText('Edit Document Tags')).toBeInTheDocument();
      expect(screen.getByText(/Manage tags for "Test Document"/)).toBeInTheDocument();
    });

    it('displays current tags', () => {
      render(<DocumentEditTagsModal {...defaultProps} />);

      expect(screen.getByText('python')).toBeInTheDocument();
      expect(screen.getByText('api')).toBeInTheDocument();
    });

    it('shows Cancel and Save Changes buttons', () => {
      render(<DocumentEditTagsModal {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });

    it('disables Save Changes when no changes made', () => {
      render(<DocumentEditTagsModal {...defaultProps} />);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('tag editing', () => {
    it('enables Save Changes after adding a tag', async () => {
      const user = userEvent.setup();
      render(<DocumentEditTagsModal {...defaultProps} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      expect(saveButton).not.toBeDisabled();
    });

    it('enables Save Changes after removing a tag', async () => {
      const user = userEvent.setup();
      render(<DocumentEditTagsModal {...defaultProps} />);

      const removeButton = screen.getByRole('button', { name: /remove python/i });
      await user.click(removeButton);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      expect(saveButton).not.toBeDisabled();
    });
  });

  describe('submitting changes', () => {
    it('calls API with updated tags on save', async () => {
      const user = userEvent.setup();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tags: ['python', 'api', 'newtag'] }),
      });

      render(<DocumentEditTagsModal {...defaultProps} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/knowledge-bases/kb-123/documents/doc-456/tags'),
          expect.objectContaining({
            method: 'PATCH',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
            }),
            body: expect.stringContaining('newtag'),
          })
        );
      });
    });

    it('calls onTagsUpdated on successful save', async () => {
      const user = userEvent.setup();
      const onTagsUpdated = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tags: ['python', 'api', 'newtag'] }),
      });

      render(<DocumentEditTagsModal {...defaultProps} onTagsUpdated={onTagsUpdated} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(onTagsUpdated).toHaveBeenCalledWith(['python', 'api', 'newtag']);
      });
    });

    it('closes modal on successful save', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tags: ['python', 'api', 'newtag'] }),
      });

      render(<DocumentEditTagsModal {...defaultProps} onOpenChange={onOpenChange} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('displays error message on API failure', async () => {
      const user = userEvent.setup();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: () => Promise.resolve({ detail: { message: 'Permission denied' } }),
      });

      render(<DocumentEditTagsModal {...defaultProps} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Permission denied')).toBeInTheDocument();
      });
    });

    it('shows loading state while saving', async () => {
      const user = userEvent.setup();
      // Create a promise that we can control
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockFetch.mockReturnValueOnce(promise);

      render(<DocumentEditTagsModal {...defaultProps} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Save button should be disabled while loading
      expect(saveButton).toBeDisabled();

      // Resolve the promise
      resolvePromise!({
        ok: true,
        json: () => Promise.resolve({ tags: ['python', 'api', 'newtag'] }),
      });
    });
  });

  describe('cancellation', () => {
    it('closes modal on Cancel click', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      render(<DocumentEditTagsModal {...defaultProps} onOpenChange={onOpenChange} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it('resets tags when modal closes without saving', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      const { rerender } = render(
        <DocumentEditTagsModal {...defaultProps} onOpenChange={onOpenChange} />
      );

      // Add a new tag
      const input = screen.getByRole('textbox');
      await user.type(input, 'newtag{Enter}');
      expect(screen.getByText('newtag')).toBeInTheDocument();

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Reopen modal
      rerender(<DocumentEditTagsModal {...defaultProps} open={true} />);

      // Should not have the new tag since we cancelled
      // (the new tag won't appear because modal resets on open)
      expect(screen.queryByText('newtag')).not.toBeInTheDocument();
    });
  });
});
