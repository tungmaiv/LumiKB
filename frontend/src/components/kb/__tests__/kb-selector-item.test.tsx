import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KbSelectorItem } from '../kb-selector-item';

describe('KbSelectorItem', () => {
  const defaultProps = {
    name: 'Test KB',
    documentCount: 5,
    permissionLevel: 'READ' as const,
  };

  it('renders KB name', () => {
    render(<KbSelectorItem {...defaultProps} />);
    expect(screen.getByText('Test KB')).toBeInTheDocument();
  });

  it('renders document count with correct text', () => {
    render(<KbSelectorItem {...defaultProps} />);
    expect(screen.getByText('5 docs')).toBeInTheDocument();
  });

  it('renders singular "doc" for count of 1', () => {
    render(<KbSelectorItem {...defaultProps} documentCount={1} />);
    expect(screen.getByText('1 doc')).toBeInTheDocument();
  });

  it('renders "0 docs" with muted styling for empty KB', () => {
    render(<KbSelectorItem {...defaultProps} documentCount={0} />);
    const countElement = screen.getByText('0 docs');
    expect(countElement).toBeInTheDocument();
    expect(countElement).toHaveClass('text-muted-foreground/60');
  });

  it('renders Eye icon for READ permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="READ" />);
    expect(screen.getByLabelText('Read access')).toBeInTheDocument();
  });

  it('renders Pencil icon for WRITE permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="WRITE" />);
    expect(screen.getByLabelText('Write access')).toBeInTheDocument();
  });

  it('renders Settings icon for ADMIN permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="ADMIN" />);
    expect(screen.getByLabelText('Admin access')).toBeInTheDocument();
  });

  it('applies correct color class for READ permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="READ" />);
    const icon = screen.getByLabelText('Read access');
    expect(icon).toHaveClass('text-muted-foreground');
  });

  it('applies correct color class for WRITE permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="WRITE" />);
    const icon = screen.getByLabelText('Write access');
    expect(icon).toHaveClass('text-blue-500');
  });

  it('applies correct color class for ADMIN permission', () => {
    render(<KbSelectorItem {...defaultProps} permissionLevel="ADMIN" />);
    const icon = screen.getByLabelText('Admin access');
    expect(icon).toHaveClass('text-amber-500');
  });

  it('calls onClick handler when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<KbSelectorItem {...defaultProps} onClick={handleClick} />);

    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies active state styling when isActive is true', () => {
    render(<KbSelectorItem {...defaultProps} isActive />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-accent');
    expect(button).toHaveClass('text-accent-foreground');
  });

  it('does not apply active state styling when isActive is false', () => {
    render(<KbSelectorItem {...defaultProps} isActive={false} />);
    const button = screen.getByRole('button');
    expect(button).not.toHaveClass('bg-accent');
  });

  it('sets aria-current when active', () => {
    render(<KbSelectorItem {...defaultProps} isActive />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-current', 'true');
  });

  it('truncates long KB names', () => {
    const longName = 'This is a very long knowledge base name that should be truncated';
    render(<KbSelectorItem {...defaultProps} name={longName} />);
    const nameElement = screen.getByText(longName);
    expect(nameElement).toHaveAttribute('title', longName);
  });
});
