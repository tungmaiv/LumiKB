/**
 * Unit tests for KB Archive/Restore/Delete dialogs
 * Story 7-26: KB Archive/Delete/Restore UI (AC-7.26.2-4)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ArchiveKBDialog } from '../dialogs/archive-kb-dialog';
import { RestoreKBDialog } from '../dialogs/restore-kb-dialog';
import { DeleteKBDialog } from '../dialogs/delete-kb-dialog';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

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

describe('ArchiveKBDialog (AC-7.26.2)', () => {
  const mockOnConfirm = vi.fn();
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] renders archive dialog with KB name', () => {
    render(
      <ArchiveKBDialog
        open={true}
        kb={createMockKB({ name: 'My Knowledge Base' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText(/Archive Knowledge Base/i)).toBeInTheDocument();
    expect(screen.getByText(/My Knowledge Base/)).toBeInTheDocument();
  });

  it('[P0] shows document count warning when KB has documents', () => {
    render(
      <ArchiveKBDialog
        open={true}
        kb={createMockKB({ document_count: 10 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByText(/This will archive 10 documents/i)).toBeInTheDocument();
  });

  it('[P0] calls onConfirm when Archive button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ArchiveKBDialog
        open={true}
        kb={createMockKB()}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: /^Archive$/i }));

    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it('[P0] calls onOpenChange when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ArchiveKBDialog
        open={true}
        kb={createMockKB()}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: /Cancel/i }));

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('[P1] shows loading state when isLoading is true', () => {
    render(
      <ArchiveKBDialog
        open={true}
        kb={createMockKB()}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={true}
      />
    );

    expect(screen.getByText(/Archiving/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Archiving/i })).toBeDisabled();
  });

  it('[P2] does not render when open is false', () => {
    render(
      <ArchiveKBDialog
        open={false}
        kb={createMockKB()}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });
});

describe('RestoreKBDialog (AC-7.26.4)', () => {
  const mockOnConfirm = vi.fn();
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] renders restore dialog with KB name', () => {
    render(
      <RestoreKBDialog
        open={true}
        kb={createMockKB({ name: 'Archived KB', archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText(/Restore Knowledge Base/i)).toBeInTheDocument();
    expect(screen.getByText(/Archived KB/)).toBeInTheDocument();
  });

  it('[P0] shows document count when KB has documents', () => {
    render(
      <RestoreKBDialog
        open={true}
        kb={createMockKB({ document_count: 8, archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByText(/This will restore 8 documents/i)).toBeInTheDocument();
  });

  it('[P0] calls onConfirm when Restore button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <RestoreKBDialog
        open={true}
        kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: /^Restore$/i }));

    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it('[P0] calls onOpenChange when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <RestoreKBDialog
        open={true}
        kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: /Cancel/i }));

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('[P1] shows loading state when isLoading is true', () => {
    render(
      <RestoreKBDialog
        open={true}
        kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={true}
      />
    );

    expect(screen.getByText(/Restoring/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Restoring/i })).toBeDisabled();
  });

  it('[P2] does not render when open is false', () => {
    render(
      <RestoreKBDialog
        open={false}
        kb={createMockKB({ archived_at: '2025-01-15T00:00:00Z' })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });
});

describe('DeleteKBDialog (AC-7.26.3)', () => {
  const mockOnConfirm = vi.fn();
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] renders delete dialog with KB name', () => {
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'KB To Delete', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText(/Delete Knowledge Base/i)).toBeInTheDocument();
    // KB name appears in description - use getAllByText and check at least one exists
    expect(screen.getAllByText(/KB To Delete/).length).toBeGreaterThan(0);
  });

  it('[P0] shows destructive warning', () => {
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
  });

  it('[P0] requires typing KB name to enable delete button', async () => {
    const user = userEvent.setup();
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'My KB', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /Delete Permanently/i });
    expect(deleteButton).toBeDisabled();

    // Type wrong name
    const input = screen.getByPlaceholderText('My KB');
    await user.type(input, 'Wrong Name');
    expect(deleteButton).toBeDisabled();

    // Clear and type correct name
    await user.clear(input);
    await user.type(input, 'My KB');
    expect(deleteButton).not.toBeDisabled();
  });

  it('[P0] calls onConfirm when confirmed', async () => {
    const user = userEvent.setup();
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'Delete Me', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText('Delete Me');
    await user.type(input, 'Delete Me');
    await user.click(screen.getByRole('button', { name: /Delete Permanently/i }));

    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it('[P0] calls onOpenChange when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    await user.click(screen.getByRole('button', { name: /Cancel/i }));

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('[P1] disables delete button when isLoading is true', async () => {
    const user = userEvent.setup();
    render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'Test', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={true}
      />
    );

    const input = screen.getByPlaceholderText('Test');
    await user.type(input, 'Test');

    expect(screen.getByText(/Deleting/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Deleting/i })).toBeDisabled();
  });

  it('[P1] clears input when dialog reopens', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'Test', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText('Test');
    await user.type(input, 'Test');
    expect(input).toHaveValue('Test');

    // Close dialog
    rerender(
      <DeleteKBDialog
        open={false}
        kb={createMockKB({ name: 'Test', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    // Reopen dialog
    rerender(
      <DeleteKBDialog
        open={true}
        kb={createMockKB({ name: 'Test', document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    const newInput = screen.getByPlaceholderText('Test');
    expect(newInput).toHaveValue('');
  });

  it('[P2] does not render when open is false', () => {
    render(
      <DeleteKBDialog
        open={false}
        kb={createMockKB({ document_count: 0 })}
        onConfirm={mockOnConfirm}
        onOpenChange={mockOnOpenChange}
        isLoading={false}
      />
    );

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });
});
