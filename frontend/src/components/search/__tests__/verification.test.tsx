/**
 * Tests for verification flow components (Story 3.10)
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VerifyAllButton } from '../verify-all-button';
import { VerificationControls } from '../verification-controls';
import type { Citation } from '../citation-card';

// Mock the verification store
const mockStartVerification = vi.fn();
const mockExitVerification = vi.fn();
const mockNavigateNext = vi.fn();
const mockNavigatePrevious = vi.fn();
const mockToggleVerified = vi.fn();
let mockIsAllVerified = false;
let mockProgress = { verified: 0, total: 3 };
let mockStoreState = {
  activeAnswerId: null as string | null,
  currentCitationIndex: 0,
  verifiedCitations: new Set<number>(),
  isVerifying: false,
  totalCitations: 0,
};

vi.mock('@/lib/hooks/use-verification', () => ({
  useVerificationStore: (selector?: (state: unknown) => unknown) => {
    const fullState = {
      ...mockStoreState,
      startVerification: mockStartVerification,
      exitVerification: mockExitVerification,
      navigateNext: mockNavigateNext,
      navigatePrevious: mockNavigatePrevious,
      toggleVerified: mockToggleVerified,
      isAllVerified: () => mockIsAllVerified,
      getProgress: () => mockProgress,
    };
    if (typeof selector === 'function') {
      return selector(fullState);
    }
    return fullState;
  },
}));

// Mock citations
const mockCitations: Citation[] = [
  {
    number: 1,
    documentId: 'doc1',
    documentName: 'Document 1',
    excerpt: 'Excerpt 1',
    charStart: 0,
    charEnd: 100,
  },
  {
    number: 2,
    documentId: 'doc2',
    documentName: 'Document 2',
    excerpt: 'Excerpt 2',
    charStart: 0,
    charEnd: 100,
  },
  {
    number: 3,
    documentId: 'doc3',
    documentName: 'Document 3',
    excerpt: 'Excerpt 3',
    charStart: 0,
    charEnd: 100,
  },
];

describe('VerifyAllButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock state
    mockStoreState = {
      activeAnswerId: null,
      currentCitationIndex: 0,
      verifiedCitations: new Set(),
      isVerifying: false,
      totalCitations: 0,
    };
    mockIsAllVerified = false;
    mockProgress = { verified: 0, total: 3 };
  });

  test('displays citation count for multiple citations', () => {
    render(<VerifyAllButton answerId="test" citations={mockCitations} isStreaming={false} />);

    expect(screen.getByRole('button')).toHaveTextContent('Verify All (3 citations)');
  });

  test('shows warning for zero citations', () => {
    render(<VerifyAllButton answerId="test" citations={[]} isStreaming={false} />);

    expect(screen.getByText(/No sources cited - use with caution/i)).toBeInTheDocument();
  });

  test('shows Preview Citation button for single citation', () => {
    render(<VerifyAllButton answerId="test" citations={[mockCitations[0]]} isStreaming={false} />);

    expect(screen.getByRole('button')).toHaveTextContent('Preview Citation');
  });

  test('clicking Verify All activates verification mode', () => {
    render(<VerifyAllButton answerId="test" citations={mockCitations} isStreaming={false} />);

    fireEvent.click(screen.getByRole('button'));

    expect(mockStartVerification).toHaveBeenCalledWith('test', 3);
  });

  test('displays progress badge when partially verified', () => {
    mockProgress = { verified: 2, total: 3 };

    render(<VerifyAllButton answerId="test" citations={mockCitations} isStreaming={false} />);

    expect(screen.getByText('2/3 verified')).toBeInTheDocument();
  });

  test('displays All verified badge when complete', () => {
    mockIsAllVerified = true;
    mockProgress = { verified: 3, total: 3 };

    render(<VerifyAllButton answerId="test" citations={mockCitations} isStreaming={false} />);

    expect(screen.getByText('✓ All verified')).toBeInTheDocument();
  });
});

describe('VerificationControls', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock state for verification mode
    mockStoreState = {
      activeAnswerId: 'test',
      currentCitationIndex: 0,
      verifiedCitations: new Set(),
      isVerifying: true,
      totalCitations: 3,
    };
    mockIsAllVerified = false;
    mockProgress = { verified: 0, total: 3 };
  });

  test('displays progress correctly', () => {
    render(<VerificationControls citations={mockCitations} />);

    expect(screen.getByText('Citation 1 of 3')).toBeInTheDocument();
  });

  test('Previous button disabled on first citation', () => {
    render(<VerificationControls citations={mockCitations} />);

    const prevButton = screen.getByLabelText('Previous citation');
    expect(prevButton).toBeDisabled();
  });

  test('Next button disabled on last citation', () => {
    mockStoreState.currentCitationIndex = 2;
    render(<VerificationControls citations={mockCitations} />);

    const nextButton = screen.getByLabelText('Next citation');
    expect(nextButton).toBeDisabled();
  });

  test('Next button navigates to next citation', () => {
    render(<VerificationControls citations={mockCitations} />);

    const nextButton = screen.getByLabelText('Next citation');
    fireEvent.click(nextButton);

    expect(mockNavigateNext).toHaveBeenCalled();
  });

  test('Previous button navigates to previous citation', () => {
    mockStoreState.currentCitationIndex = 1;
    render(<VerificationControls citations={mockCitations} />);

    const prevButton = screen.getByLabelText('Previous citation');
    fireEvent.click(prevButton);

    expect(mockNavigatePrevious).toHaveBeenCalled();
  });

  test('Checkbox toggles verification state', () => {
    render(<VerificationControls citations={mockCitations} />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);

    expect(mockToggleVerified).toHaveBeenCalledWith(1);
  });

  test('Exit button deactivates verification mode', () => {
    render(<VerificationControls citations={mockCitations} />);

    const exitButton = screen.getByLabelText('Exit verification mode');
    fireEvent.click(exitButton);

    expect(mockExitVerification).toHaveBeenCalled();
  });

  test('All verified message appears when complete', () => {
    mockStoreState.verifiedCitations = new Set([1, 2, 3]);
    mockStoreState.currentCitationIndex = 2;
    mockIsAllVerified = true;

    render(<VerificationControls citations={mockCitations} />);

    expect(screen.getByText('All sources verified ✓')).toBeInTheDocument();
  });
});
