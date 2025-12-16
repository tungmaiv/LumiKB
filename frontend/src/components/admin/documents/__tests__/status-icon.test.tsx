/**
 * Status Icon Component Tests
 *
 * Story 9-10: Document Timeline UI
 * AC10: Unit tests for timeline rendering and interactions
 * AC3: Status icons for each status type
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StatusIcon } from '../status-icon';

describe('StatusIcon', () => {
  it('renders completed icon with green color', () => {
    render(<StatusIcon status="completed" />);

    const icon = screen.getByTestId('status-icon-completed');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('text-green-500');
    expect(icon).toHaveAttribute('aria-label', 'Completed');
  });

  it('renders failed icon with red color', () => {
    render(<StatusIcon status="failed" />);

    const icon = screen.getByTestId('status-icon-failed');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('text-red-500');
    expect(icon).toHaveAttribute('aria-label', 'Failed');
  });

  it('renders in-progress icon with blue spinning animation', () => {
    render(<StatusIcon status="in_progress" />);

    const icon = screen.getByTestId('status-icon-in-progress');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('text-blue-500');
    expect(icon).toHaveClass('animate-spin');
    expect(icon).toHaveAttribute('aria-label', 'In Progress');
  });

  it('renders started icon with spinning animation (same as in_progress)', () => {
    render(<StatusIcon status="started" />);

    const icon = screen.getByTestId('status-icon-in-progress');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('animate-spin');
  });

  it('renders pending icon with gray color', () => {
    render(<StatusIcon status="pending" />);

    const icon = screen.getByTestId('status-icon-pending');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('text-gray-400');
    expect(icon).toHaveAttribute('aria-label', 'Pending');
  });

  it('renders pending icon for unknown status', () => {
    render(<StatusIcon status="unknown_status" />);

    const icon = screen.getByTestId('status-icon-pending');
    expect(icon).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<StatusIcon status="completed" className="custom-class" />);

    const icon = screen.getByTestId('status-icon-completed');
    expect(icon).toHaveClass('custom-class');
  });
});
