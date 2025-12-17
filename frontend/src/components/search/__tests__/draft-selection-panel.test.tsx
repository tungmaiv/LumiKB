/**
 * Draft Selection Panel Tests (Story 3.8)
 * Updated for Epic 4 (Story 4.4) - GenerationModal integration
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DraftSelectionPanel } from '../draft-selection-panel';
import { useDraftStore, type DraftResult } from '@/lib/stores/draft-store';
import { toast } from 'sonner';

// Mock dependencies
vi.mock('@/lib/stores/draft-store');
vi.mock('sonner');

// Mock GenerationModal to avoid complex dependency chain
vi.mock('@/components/chat/generation-modal', () => ({
  GenerationModal: ({ open }: { open: boolean }) =>
    open ? <div data-testid="generation-modal">Modal Open</div> : null,
}));

// Mock API call
vi.mock('@/lib/api/generation', () => ({
  generateDocument: vi.fn(),
}));

// Cast useDraftStore to mockable function
const mockUseDraftStore = useDraftStore as unknown as ReturnType<typeof vi.fn>;

describe('DraftSelectionPanel', () => {
  const defaultKbId = 'kb-test-1';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when there are selected results', () => {
    // Arrange
    mockUseDraftStore.mockReturnValue({
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
    render(<DraftSelectionPanel kbId={defaultKbId} />);

    // Assert
    expect(screen.getByTestId('draft-selection-panel')).toBeInTheDocument();
    expect(screen.getByText(/1 result selected for draft/i)).toBeInTheDocument();
  });

  it('hides when there are no selected results', () => {
    // Arrange
    mockUseDraftStore.mockReturnValue({
      selectedResults: [],
      clearAll: vi.fn(),
    });

    // Act
    const { container } = render(<DraftSelectionPanel kbId={defaultKbId} />);

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('displays correct count for multiple results', () => {
    // Arrange
    mockUseDraftStore.mockReturnValue({
      selectedResults: [
        { chunkId: '1', documentName: 'Doc 1' },
        { chunkId: '2', documentName: 'Doc 2' },
        { chunkId: '3', documentName: 'Doc 3' },
      ] as DraftResult[],
      clearAll: vi.fn(),
    });

    // Act
    render(<DraftSelectionPanel kbId={defaultKbId} />);

    // Assert
    expect(screen.getByText(/3 results selected for draft/i)).toBeInTheDocument();
  });

  it('calls clearAll when Clear All button clicked', () => {
    // Arrange
    const clearAllMock = vi.fn();
    mockUseDraftStore.mockReturnValue({
      selectedResults: [{ chunkId: '1' }] as DraftResult[],
      clearAll: clearAllMock,
    });

    // Act
    render(<DraftSelectionPanel kbId={defaultKbId} />);
    const clearButton = screen.getByRole('button', { name: /clear all/i });
    fireEvent.click(clearButton);

    // Assert
    expect(clearAllMock).toHaveBeenCalledTimes(1);
    expect(toast.success).toHaveBeenCalledWith('Draft selections cleared', expect.any(Object));
  });

  it('opens generation modal when Start Draft clicked (Epic 4 integration)', () => {
    // Arrange
    mockUseDraftStore.mockReturnValue({
      selectedResults: [{ chunkId: '1' }] as DraftResult[],
      clearAll: vi.fn(),
    });

    // Act
    render(<DraftSelectionPanel kbId={defaultKbId} />);
    const startButton = screen.getByRole('button', { name: /start draft/i });
    fireEvent.click(startButton);

    // Assert - Modal should now be open
    expect(screen.getByTestId('generation-modal')).toBeInTheDocument();
  });
});
