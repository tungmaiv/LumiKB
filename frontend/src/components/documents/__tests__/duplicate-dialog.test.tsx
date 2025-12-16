import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DuplicateDialog, type DuplicateInfo } from '../duplicate-dialog';

describe('DuplicateDialog', () => {
  const mockOnCancel = vi.fn();
  const mockOnReplace = vi.fn();
  const mockOnSkip = vi.fn();

  const defaultDuplicateInfo: DuplicateInfo = {
    exists: true,
    document_id: 'doc-123',
    uploaded_at: '2024-01-01T10:00:00Z',
    file_size: 1024 * 500, // 500 KB
    existing_status: 'completed',
  };

  const defaultProps = {
    isOpen: true,
    onCancel: mockOnCancel,
    onReplace: mockOnReplace,
    onSkip: mockOnSkip,
    filename: 'test-document.pdf',
    duplicateInfo: defaultDuplicateInfo,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // AC-6.9.1: Show modal when duplicate detected
  it('renders duplicate dialog when open', () => {
    render(<DuplicateDialog {...defaultProps} />);

    expect(screen.getByText('Document Already Exists')).toBeInTheDocument();
    expect(screen.getByText(/test-document.pdf/)).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<DuplicateDialog {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Document Already Exists')).not.toBeInTheDocument();
  });

  // AC-6.9.2: Replace option triggers onReplace
  it('calls onReplace when Replace button is clicked', () => {
    render(<DuplicateDialog {...defaultProps} />);

    const replaceButton = screen.getByRole('button', { name: /replace existing/i });
    fireEvent.click(replaceButton);

    expect(mockOnReplace).toHaveBeenCalledTimes(1);
  });

  // AC-6.9.3: Cancel option triggers onSkip
  it('calls onSkip when Cancel button is clicked', () => {
    render(<DuplicateDialog {...defaultProps} />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });

  // AC-6.9.5: Loading state during replace
  it('shows loading state when isReplacing is true', () => {
    render(<DuplicateDialog {...defaultProps} isReplacing={true} />);

    expect(screen.getByText('Replacing...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /replacing/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
  });

  // AC-6.9.6: Error state after replace failure
  it('displays error message when replace fails', () => {
    const errorMessage = 'File type mismatch. Expected PDF, got DOCX.';
    render(<DuplicateDialog {...defaultProps} error={errorMessage} />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  // AC-6.9.7: Archived document restore note
  it('shows restore note for archived documents', () => {
    const archivedInfo: DuplicateInfo = {
      ...defaultDuplicateInfo,
      existing_status: 'archived',
    };
    render(<DuplicateDialog {...defaultProps} duplicateInfo={archivedInfo} />);

    expect(
      screen.getByText(/replacing will restore this document to active status/i)
    ).toBeInTheDocument();
    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  it('does not show restore note for completed documents', () => {
    render(<DuplicateDialog {...defaultProps} />);

    expect(
      screen.queryByText(/replacing will restore this document to active status/i)
    ).not.toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  // Status badge display
  it('displays status badge for completed document', () => {
    render(<DuplicateDialog {...defaultProps} />);

    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('displays status badge for archived document', () => {
    const archivedInfo: DuplicateInfo = {
      ...defaultDuplicateInfo,
      existing_status: 'archived',
    };
    render(<DuplicateDialog {...defaultProps} duplicateInfo={archivedInfo} />);

    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  // File metadata display
  it('displays file size in human-readable format', () => {
    render(<DuplicateDialog {...defaultProps} />);

    expect(screen.getByText(/500\.0 KB/)).toBeInTheDocument();
  });

  it('displays upload time relative to now', () => {
    render(<DuplicateDialog {...defaultProps} />);

    // Should display some form of relative time (e.g., "about 1 year ago")
    const timeText = screen.getByText(/uploaded/i);
    expect(timeText).toBeInTheDocument();
  });

  // Buttons are enabled when not replacing
  it('enables buttons when not replacing', () => {
    render(<DuplicateDialog {...defaultProps} isReplacing={false} />);

    expect(screen.getByRole('button', { name: /replace existing/i })).not.toBeDisabled();
    expect(screen.getByRole('button', { name: /cancel/i })).not.toBeDisabled();
  });

  // Default status when not provided
  it('defaults to completed status when not specified', () => {
    const infoWithoutStatus: DuplicateInfo = {
      exists: true,
      document_id: 'doc-123',
    };
    render(<DuplicateDialog {...defaultProps} duplicateInfo={infoWithoutStatus} />);

    expect(screen.getByText('completed')).toBeInTheDocument();
  });
});
