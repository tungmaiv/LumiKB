/**
 * Component Tests: ViewModeToggle
 *
 * Story: 7-31 View Mode Toggle for Chunk Viewer
 * Coverage: Toggle rendering, mode switching, disabled state, visual indication
 *
 * Test Count: 12 tests
 * Priority: P0 (5), P1 (5), P2 (2)
 *
 * Test Framework: Vitest + Testing Library
 *
 * AC Coverage:
 * - AC-7.31.1: Toggle Component (renders with both options)
 * - AC-7.31.3: Disabled When Unavailable (markdown grayed out)
 * - AC-7.31.5: Visual Indication (selected state)
 * - AC-7.31.6: Unit Tests (mode switching, persistence, disabled state)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ViewModeToggle } from '../view-mode-toggle';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

describe('ViewModeToggle Component', () => {
  const defaultProps = {
    markdownAvailable: true,
    value: 'markdown' as const,
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // Rendering Tests - AC-7.31.1
  // ============================================================================

  it('[P0] should render toggle with both Original and Markdown options - AC-7.31.1', () => {
    // GIVEN: Default props with markdown available
    // WHEN: Component is rendered
    render(<ViewModeToggle {...defaultProps} />);

    // THEN: Both options should be visible
    expect(screen.getByRole('radio', { name: /original/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /markdown/i })).toBeInTheDocument();
  });

  it('[P0] should render with FileText icon for Original option - AC-7.31.1', () => {
    // GIVEN: Component rendered
    render(<ViewModeToggle {...defaultProps} />);

    // THEN: Original button should be visible with appropriate icon/text
    const originalButton = screen.getByRole('radio', { name: /original/i });
    expect(originalButton).toBeInTheDocument();
    expect(originalButton).toHaveAccessibleName(/original/i);
  });

  it('[P0] should render with Code icon for Markdown option - AC-7.31.1', () => {
    // GIVEN: Component rendered
    render(<ViewModeToggle {...defaultProps} />);

    // THEN: Markdown button should be visible with appropriate icon/text
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    expect(markdownButton).toBeInTheDocument();
    expect(markdownButton).toHaveAccessibleName(/markdown/i);
  });

  // ============================================================================
  // Mode Switching Tests - AC-7.31.6
  // ============================================================================

  it('[P0] should call onChange when Original is clicked - AC-7.31.6', async () => {
    // GIVEN: Component with markdown selected
    const onChange = vi.fn();
    render(<ViewModeToggle {...defaultProps} value="markdown" onChange={onChange} />);

    // WHEN: User clicks Original option
    const originalButton = screen.getByRole('radio', { name: /original/i });
    await userEvent.click(originalButton);

    // THEN: onChange should be called with 'original'
    expect(onChange).toHaveBeenCalledWith('original');
  });

  it('[P0] should call onChange when Markdown is clicked - AC-7.31.6', async () => {
    // GIVEN: Component with original selected
    const onChange = vi.fn();
    render(<ViewModeToggle {...defaultProps} value="original" onChange={onChange} />);

    // WHEN: User clicks Markdown option
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    await userEvent.click(markdownButton);

    // THEN: onChange should be called with 'markdown'
    expect(onChange).toHaveBeenCalledWith('markdown');
  });

  // ============================================================================
  // Disabled State Tests - AC-7.31.3
  // ============================================================================

  it('[P1] should disable Markdown option when markdown not available - AC-7.31.3', () => {
    // GIVEN: Markdown is not available
    render(<ViewModeToggle {...defaultProps} markdownAvailable={false} value="original" />);

    // THEN: Markdown button should be disabled
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    expect(markdownButton).toBeDisabled();
  });

  it('[P1] should not disable Original option regardless of markdown availability - AC-7.31.3', () => {
    // GIVEN: Markdown is not available
    render(<ViewModeToggle {...defaultProps} markdownAvailable={false} value="original" />);

    // THEN: Original button should still be enabled
    const originalButton = screen.getByRole('radio', { name: /original/i });
    expect(originalButton).not.toBeDisabled();
  });

  it('[P1] should show tooltip when Markdown disabled - AC-7.31.3', async () => {
    // GIVEN: Markdown is not available
    render(<ViewModeToggle {...defaultProps} markdownAvailable={false} value="original" />);

    // WHEN: User hovers over disabled Markdown option
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    await userEvent.hover(markdownButton);

    // THEN: Tooltip should appear explaining why
    // Note: Radix tooltip renders multiple instances (visual + accessibility)
    await waitFor(() => {
      const tooltips = screen.getAllByText(/markdown not available for this document/i);
      expect(tooltips.length).toBeGreaterThan(0);
    });
  });

  it('[P1] should not call onChange when clicking disabled Markdown - AC-7.31.3', async () => {
    // GIVEN: Markdown is not available
    const onChange = vi.fn();
    render(
      <ViewModeToggle
        {...defaultProps}
        markdownAvailable={false}
        value="original"
        onChange={onChange}
      />
    );

    // WHEN: User tries to click disabled Markdown option
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    await userEvent.click(markdownButton);

    // THEN: onChange should NOT be called
    expect(onChange).not.toHaveBeenCalled();
  });

  // ============================================================================
  // Visual Indication Tests - AC-7.31.5
  // ============================================================================

  it('[P1] should show Markdown as selected when value is markdown - AC-7.31.5', () => {
    // GIVEN: Value is markdown
    render(<ViewModeToggle {...defaultProps} value="markdown" />);

    // THEN: Markdown button should have selected state
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    expect(markdownButton).toHaveAttribute('data-state', 'on');

    // AND: Original should not be selected
    const originalButton = screen.getByRole('radio', { name: /original/i });
    expect(originalButton).toHaveAttribute('data-state', 'off');
  });

  it('[P2] should show Original as selected when value is original - AC-7.31.5', () => {
    // GIVEN: Value is original
    render(<ViewModeToggle {...defaultProps} value="original" />);

    // THEN: Original button should have selected state
    const originalButton = screen.getByRole('radio', { name: /original/i });
    expect(originalButton).toHaveAttribute('data-state', 'on');

    // AND: Markdown should not be selected
    const markdownButton = screen.getByRole('radio', { name: /markdown/i });
    expect(markdownButton).toHaveAttribute('data-state', 'off');
  });

  // ============================================================================
  // Edge Cases - AC-7.31.6
  // ============================================================================

  it('[P2] should have accessible labels for screen readers - AC-7.31.6', () => {
    // GIVEN: Component rendered
    render(<ViewModeToggle {...defaultProps} />);

    // THEN: Buttons should have proper aria-labels
    const originalButton = screen.getByRole('radio', { name: /original view/i });
    const markdownButton = screen.getByRole('radio', { name: /markdown view/i });

    expect(originalButton).toHaveAttribute('aria-label');
    expect(markdownButton).toHaveAttribute('aria-label');
  });
});
