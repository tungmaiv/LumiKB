/**
 * CitationWarningBanner Component Tests - Epic 7, Story 7-21
 * Tests for warning display, dismissal, and auto-fix functionality
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { CitationWarningBanner, CitationWarningInline } from '../citation-warning-banner';
import type { ValidationWarning } from '@/hooks/useCitationValidation';

describe('CitationWarningBanner', () => {
  const mockOnDismiss = vi.fn();
  const mockOnAutoFix = vi.fn();

  const orphanedWarning: ValidationWarning = {
    type: 'orphaned_citation',
    message: 'Citation [5] references a missing source',
    citationNumbers: [5],
  };

  const unusedWarning: ValidationWarning = {
    type: 'unused_citation',
    message: 'Source [3] is defined but never used',
    citationNumbers: [3],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders nothing when no warnings', () => {
      const { container } = render(
        <CitationWarningBanner warnings={[]} onDismiss={mockOnDismiss} />
      );

      expect(container).toBeEmptyDOMElement();
    });

    it('renders orphaned citation warning (AC-7.21.4)', () => {
      render(<CitationWarningBanner warnings={[orphanedWarning]} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Missing Citation Source')).toBeInTheDocument();
      expect(screen.getByText('Citation [5] references a missing source')).toBeInTheDocument();
    });

    it('renders unused citation warning (AC-7.21.4)', () => {
      render(
        <CitationWarningBanner
          warnings={[unusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
        />
      );

      expect(screen.getByText('Unused Citation Source')).toBeInTheDocument();
      expect(screen.getByText('Source [3] is defined but never used')).toBeInTheDocument();
    });

    it('renders multiple warnings', () => {
      render(
        <CitationWarningBanner
          warnings={[orphanedWarning, unusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
        />
      );

      expect(screen.getByText('Missing Citation Source')).toBeInTheDocument();
      expect(screen.getByText('Unused Citation Source')).toBeInTheDocument();
    });

    it('has correct test id for banner', () => {
      render(<CitationWarningBanner warnings={[orphanedWarning]} onDismiss={mockOnDismiss} />);

      expect(screen.getByTestId('citation-warning-banner')).toBeInTheDocument();
    });
  });

  describe('dismiss functionality (AC-7.21.5)', () => {
    it('calls onDismiss with correct type when dismiss button clicked', () => {
      render(<CitationWarningBanner warnings={[orphanedWarning]} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByTestId('dismiss-orphaned_citation');
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledWith('orphaned_citation');
    });

    it('calls onDismiss for unused citation warning', () => {
      render(<CitationWarningBanner warnings={[unusedWarning]} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByTestId('dismiss-unused_citation');
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledWith('unused_citation');
    });

    it('dismiss buttons have correct aria labels', () => {
      render(
        <CitationWarningBanner
          warnings={[orphanedWarning, unusedWarning]}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByLabelText('Dismiss missing source warning')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss unused source warning')).toBeInTheDocument();
    });
  });

  describe('auto-fix functionality', () => {
    it('shows auto-fix button for unused citations', () => {
      render(
        <CitationWarningBanner
          warnings={[unusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
          showAutoFix={true}
        />
      );

      expect(screen.getByTestId('auto-fix-button')).toBeInTheDocument();
      expect(screen.getByText('Remove unused source')).toBeInTheDocument();
    });

    it('does not show auto-fix button for orphaned citations', () => {
      render(
        <CitationWarningBanner
          warnings={[orphanedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
          showAutoFix={true}
        />
      );

      expect(screen.queryByTestId('auto-fix-button')).not.toBeInTheDocument();
    });

    it('calls onAutoFix with correct citation numbers', () => {
      const multiUnusedWarning: ValidationWarning = {
        type: 'unused_citation',
        message: 'Sources [2], [3] are defined but never used',
        citationNumbers: [2, 3],
      };

      render(
        <CitationWarningBanner
          warnings={[multiUnusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
          showAutoFix={true}
        />
      );

      const autoFixButton = screen.getByTestId('auto-fix-button');
      fireEvent.click(autoFixButton);

      expect(mockOnAutoFix).toHaveBeenCalledWith([2, 3]);
    });

    it('shows plural text for multiple sources', () => {
      const multiUnusedWarning: ValidationWarning = {
        type: 'unused_citation',
        message: 'Sources [2], [3] are defined but never used',
        citationNumbers: [2, 3],
      };

      render(
        <CitationWarningBanner
          warnings={[multiUnusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
          showAutoFix={true}
        />
      );

      expect(screen.getByText('Remove unused sources')).toBeInTheDocument();
    });

    it('hides auto-fix button when showAutoFix is false', () => {
      render(
        <CitationWarningBanner
          warnings={[unusedWarning]}
          onDismiss={mockOnDismiss}
          onAutoFix={mockOnAutoFix}
          showAutoFix={false}
        />
      );

      expect(screen.queryByTestId('auto-fix-button')).not.toBeInTheDocument();
    });

    it('hides auto-fix button when onAutoFix is not provided', () => {
      render(
        <CitationWarningBanner
          warnings={[unusedWarning]}
          onDismiss={mockOnDismiss}
          showAutoFix={true}
        />
      );

      expect(screen.queryByTestId('auto-fix-button')).not.toBeInTheDocument();
    });
  });

  describe('styling', () => {
    it('uses amber/warning color scheme', () => {
      render(<CitationWarningBanner warnings={[orphanedWarning]} onDismiss={mockOnDismiss} />);

      const banner = screen.getByTestId('citation-warning-banner');
      const alert = banner.querySelector('[role="alert"]');
      expect(alert).toHaveClass('bg-amber-50', 'border-amber-200');
    });
  });
});

describe('CitationWarningInline', () => {
  const mockOnDismiss = vi.fn();

  const warnings: ValidationWarning[] = [
    {
      type: 'orphaned_citation',
      message: 'Citation [5] references a missing source',
      citationNumbers: [5],
    },
    {
      type: 'unused_citation',
      message: 'Source [3] is defined but never used',
      citationNumbers: [3],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when no warnings', () => {
    const { container } = render(<CitationWarningInline warnings={[]} onDismiss={mockOnDismiss} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('shows total issue count', () => {
    render(<CitationWarningInline warnings={warnings} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('2 citation issues detected')).toBeInTheDocument();
  });

  it('uses singular text for single issue', () => {
    render(<CitationWarningInline warnings={[warnings[0]]} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('1 citation issue detected')).toBeInTheDocument();
  });

  it('dismisses all warnings when X clicked', () => {
    render(<CitationWarningInline warnings={warnings} onDismiss={mockOnDismiss} />);

    const dismissButton = screen.getByLabelText('Dismiss all warnings');
    fireEvent.click(dismissButton);

    expect(mockOnDismiss).toHaveBeenCalledTimes(2);
    expect(mockOnDismiss).toHaveBeenCalledWith('orphaned_citation');
    expect(mockOnDismiss).toHaveBeenCalledWith('unused_citation');
  });

  it('has correct test id', () => {
    render(<CitationWarningInline warnings={warnings} onDismiss={mockOnDismiss} />);

    expect(screen.getByTestId('citation-warning-inline')).toBeInTheDocument();
  });
});
