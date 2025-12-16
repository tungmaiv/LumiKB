/**
 * Unit tests for KBActionsMenu component
 * Story 7-26: KB Archive/Delete/Restore UI (AC-7.26.1-4)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KBActionsMenu } from '../kb-actions-menu';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

// Mock useKBActions hook
const mockArchive = vi.fn();
const mockRestore = vi.fn();
const mockRemove = vi.fn();

vi.mock('@/hooks/useKBActions', () => ({
  useKBActions: () => ({
    archive: mockArchive,
    restore: mockRestore,
    remove: mockRemove,
    isArchiving: false,
    isRestoring: false,
    isDeleting: false,
    isPending: false,
  }),
}));

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createMockKB = (overrides: Partial<KnowledgeBase> = {}): KnowledgeBase => ({
  id: 'kb-123',
  name: 'Test KB',
  description: 'Test description',
  status: 'active',
  document_count: 5,
  permission_level: 'ADMIN',
  tags: [],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  archived_at: null,
  ...overrides,
});

describe('KBActionsMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockArchive.mockResolvedValue(true);
    mockRestore.mockResolvedValue(true);
    mockRemove.mockResolvedValue(true);
  });

  describe('Menu Rendering (AC-7.26.1)', () => {
    it('[P0] renders action menu trigger button for admin users', () => {
      render(<KBActionsMenu kb={createMockKB()} />);
      expect(screen.getByRole('button', { name: /KB actions/i })).toBeInTheDocument();
    });

    it('[P0] does not render for non-admin users', () => {
      render(<KBActionsMenu kb={createMockKB({ permission_level: 'READ' })} />);
      expect(screen.queryByRole('button', { name: /KB actions/i })).not.toBeInTheDocument();
    });

    it('[P0] shows Archive KB option for active KB', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB()} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.getByText('Archive KB')).toBeInTheDocument();
      });
    });

    it('[P0] shows Restore KB option for archived KB', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.getByText('Restore KB')).toBeInTheDocument();
      });
    });

    it('[P0] shows Delete KB option for active KB with 0 documents', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ document_count: 0 })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.getByText('Delete KB')).toBeInTheDocument();
      });
    });

    it('[P1] disables Delete KB option for KB with documents', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ document_count: 5 })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        const deleteItem = screen.getByText('Delete KB').closest('[role="menuitem"]');
        expect(deleteItem).toHaveAttribute('data-disabled');
      });
    });

    it('[P1] does not show Restore KB option for active KB', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB()} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.queryByText('Restore KB')).not.toBeInTheDocument();
      });
    });
  });

  describe('Archive Dialog (AC-7.26.2)', () => {
    it('[P0] opens archive dialog when Archive KB is clicked', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB()} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Archive KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/Archive Knowledge Base/i)).toBeInTheDocument();
      });
    });

    it('[P0] shows KB name in archive dialog', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ name: 'My Test KB' })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Archive KB'));

      await waitFor(() => {
        expect(screen.getByText(/My Test KB/)).toBeInTheDocument();
      });
    });

    it('[P0] calls archive when confirmed', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ id: 'kb-to-archive', name: 'Test KB' })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Archive KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /^Archive$/i }));

      await waitFor(() => {
        expect(mockArchive).toHaveBeenCalledWith('kb-to-archive', 'Test KB');
      });
    });

    it('[P1] closes dialog when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB()} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Archive KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Restore Dialog (AC-7.26.4)', () => {
    it('[P0] opens restore dialog when Restore KB is clicked', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Restore KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/Restore Knowledge Base/i)).toBeInTheDocument();
      });
    });

    it('[P0] calls restore when confirmed', async () => {
      const user = userEvent.setup();
      render(
        <KBActionsMenu
          kb={createMockKB({ id: 'kb-to-restore', name: 'Test KB', archived_at: '2025-01-15T00:00:00Z' })}
        />
      );

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Restore KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /^Restore$/i }));

      await waitFor(() => {
        expect(mockRestore).toHaveBeenCalledWith('kb-to-restore', 'Test KB');
      });
    });
  });

  describe('Delete Dialog (AC-7.26.3)', () => {
    it('[P0] opens delete dialog when Delete KB is clicked', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ document_count: 0 })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Delete KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/Delete Knowledge Base/i)).toBeInTheDocument();
      });
    });

    it('[P0] requires typing KB name to enable delete', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB({ name: 'Test KB', document_count: 0 })} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Delete KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      // Delete button should be disabled initially
      const deleteButton = screen.getByRole('button', { name: /Delete Permanently/i });
      expect(deleteButton).toBeDisabled();

      // Type the KB name
      const input = screen.getByPlaceholderText('Test KB');
      await user.type(input, 'Test KB');

      // Delete button should now be enabled
      expect(deleteButton).not.toBeDisabled();
    });

    it('[P0] calls remove when confirmed with correct name', async () => {
      const user = userEvent.setup();
      render(
        <KBActionsMenu kb={createMockKB({ id: 'kb-to-delete', name: 'My KB', document_count: 0 })} />
      );

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Delete KB'));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const input = screen.getByPlaceholderText('My KB');
      await user.type(input, 'My KB');
      await user.click(screen.getByRole('button', { name: /Delete Permanently/i }));

      await waitFor(() => {
        expect(mockRemove).toHaveBeenCalledWith('kb-to-delete', 'My KB');
      });
    });
  });

  describe('Settings Option', () => {
    it('[P1] shows Settings option when onSettingsClick is provided', async () => {
      const user = userEvent.setup();
      const mockOnSettings = vi.fn();
      render(<KBActionsMenu kb={createMockKB()} onSettingsClick={mockOnSettings} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument();
      });
    });

    it('[P1] calls onSettingsClick when Settings is clicked', async () => {
      const user = userEvent.setup();
      const mockOnSettings = vi.fn();
      render(<KBActionsMenu kb={createMockKB()} onSettingsClick={mockOnSettings} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));
      await user.click(screen.getByText('Settings'));

      expect(mockOnSettings).toHaveBeenCalled();
    });

    it('[P1] does not show Settings option when onSettingsClick is not provided', async () => {
      const user = userEvent.setup();
      render(<KBActionsMenu kb={createMockKB()} />);

      await user.click(screen.getByRole('button', { name: /KB actions/i }));

      await waitFor(() => {
        expect(screen.queryByText('Settings')).not.toBeInTheDocument();
      });
    });
  });
});
