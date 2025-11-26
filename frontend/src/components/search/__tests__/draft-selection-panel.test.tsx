/**
 * Draft Selection Panel Tests (Story 3.8)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DraftSelectionPanel } from '../draft-selection-panel';
import { useDraftStore } from '@/lib/stores/draft-store';
import { toast } from 'sonner';

// Mock dependencies
vi.mock('@/lib/stores/draft-store');
vi.mock('sonner');

describe('DraftSelectionPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when there are selected results', () => {
    // Arrange
    (useDraftStore as any).mockReturnValue({
      selectedResults: [
        {
          chunkId: '1',
          documentId: 'doc-1',
          documentName: 'Test Doc',
          chunkText: 'Sample text',
          kbId: 'kb-1',
          kbName: 'Test KB',
          relevanceScore: 0.9,
        },
      ],
      clearAll: vi.fn(),
    });

    // Act
    render(<DraftSelectionPanel />);

    // Assert
    expect(screen.getByTestId('draft-selection-panel')).toBeInTheDocument();
    expect(screen.getByText(/1 result selected for draft/i)).toBeInTheDocument();
  });

  it('hides when there are no selected results', () => {
    // Arrange
    (useDraftStore as any).mockReturnValue({
      selectedResults: [],
      clearAll: vi.fn(),
    });

    // Act
    const { container } = render(<DraftSelectionPanel />);

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('displays correct count for multiple results', () => {
    // Arrange
    (useDraftStore as any).mockReturnValue({
      selectedResults: [
        { chunkId: '1', documentName: 'Doc 1' /* other fields */ },
        { chunkId: '2', documentName: 'Doc 2' /* other fields */ },
        { chunkId: '3', documentName: 'Doc 3' /* other fields */ },
      ],
      clearAll: vi.fn(),
    });

    // Act
    render(<DraftSelectionPanel />);

    // Assert
    expect(screen.getByText(/3 results selected for draft/i)).toBeInTheDocument();
  });

  it('calls clearAll when Clear All button clicked', () => {
    // Arrange
    const clearAllMock = vi.fn();
    (useDraftStore as any).mockReturnValue({
      selectedResults: [{ chunkId: '1' /* other fields */ }],
      clearAll: clearAllMock,
    });

    // Act
    render(<DraftSelectionPanel />);
    const clearButton = screen.getByRole('button', { name: /clear all/i });
    fireEvent.click(clearButton);

    // Assert
    expect(clearAllMock).toHaveBeenCalledTimes(1);
    expect(toast.success).toHaveBeenCalledWith('Draft selections cleared', expect.any(Object));
  });

  it('shows placeholder toast when Start Draft clicked', () => {
    // Arrange
    (useDraftStore as any).mockReturnValue({
      selectedResults: [{ chunkId: '1' /* other fields */ }],
      clearAll: vi.fn(),
    });

    // Act
    render(<DraftSelectionPanel />);
    const startButton = screen.getByRole('button', { name: /start draft/i });
    fireEvent.click(startButton);

    // Assert
    expect(toast.info).toHaveBeenCalledWith(
      'Draft generation coming in Epic 4!',
      expect.objectContaining({
        duration: 4000,
      })
    );
  });
});
