import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceIndicator } from '../confidence-indicator';

describe('ConfidenceIndicator', () => {
  it('renders confidence percentage', () => {
    render(<ConfidenceIndicator confidence={0.85} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders label when showLabel is true', () => {
    render(<ConfidenceIndicator confidence={0.85} showLabel={true} />);
    expect(screen.getByText('Confidence:')).toBeInTheDocument();
  });

  it('does not render label when showLabel is false', () => {
    render(<ConfidenceIndicator confidence={0.85} showLabel={false} />);
    expect(screen.queryByText('Confidence:')).not.toBeInTheDocument();
  });

  it('uses green color for high confidence (80-100%)', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.9} />);
    const bar = container.querySelector('.bg-\\[\\#10B981\\]');
    expect(bar).toBeInTheDocument();
  });

  it('uses green color for confidence at 80% threshold', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.8} />);
    const bar = container.querySelector('.bg-\\[\\#10B981\\]');
    expect(bar).toBeInTheDocument();
  });

  it('uses amber color for medium confidence (50-79%)', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.65} />);
    const bar = container.querySelector('.bg-\\[\\#F59E0B\\]');
    expect(bar).toBeInTheDocument();
  });

  it('uses amber color for confidence at 50% threshold', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.5} />);
    const bar = container.querySelector('.bg-\\[\\#F59E0B\\]');
    expect(bar).toBeInTheDocument();
  });

  it('uses red color for low confidence (0-49%)', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.35} />);
    const bar = container.querySelector('.bg-\\[\\#EF4444\\]');
    expect(bar).toBeInTheDocument();
  });

  it('uses red color for confidence at 0%', () => {
    const { container } = render(<ConfidenceIndicator confidence={0} />);
    const bar = container.querySelector('.bg-\\[\\#EF4444\\]');
    expect(bar).toBeInTheDocument();
  });

  it('has correct data-testid', () => {
    render(<ConfidenceIndicator confidence={0.85} />);
    expect(screen.getByTestId('confidence-indicator')).toBeInTheDocument();
  });

  it('sets bar width proportional to confidence', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.75} />);
    const bar = container.querySelector('[role="meter"]');
    expect(bar).toHaveStyle({ width: '75%' });
  });

  it('has correct ARIA attributes', () => {
    render(<ConfidenceIndicator confidence={0.85} />);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '85');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
    expect(meter).toHaveAttribute('aria-label', 'Confidence level: 85%');
  });

  it('rounds confidence to nearest integer', () => {
    render(<ConfidenceIndicator confidence={0.847} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('applies small size classes', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.85} size="sm" />);
    const wrapper = container.querySelector('[data-testid="confidence-indicator"]');
    expect(wrapper?.querySelector('.text-xs')).toBeInTheDocument();
  });

  it('applies medium size classes', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.85} size="md" />);
    const wrapper = container.querySelector('[data-testid="confidence-indicator"]');
    expect(wrapper?.querySelector('.text-sm')).toBeInTheDocument();
  });

  it('applies large size classes', () => {
    const { container } = render(<ConfidenceIndicator confidence={0.85} size="lg" />);
    const wrapper = container.querySelector('[data-testid="confidence-indicator"]');
    expect(wrapper?.querySelector('.text-base')).toBeInTheDocument();
  });
});
