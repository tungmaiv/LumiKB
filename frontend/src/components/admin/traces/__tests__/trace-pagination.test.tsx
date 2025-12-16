/**
 * Trace Pagination Component Tests
 *
 * Story 9-8: Trace Viewer UI Component
 * AC10: Unit tests for component rendering and user interactions
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { TracePagination } from '../trace-pagination';

describe('TracePagination', () => {
  const defaultProps = {
    page: 1,
    totalPages: 5,
    total: 100,
    limit: 20,
    onPageChange: vi.fn(),
    onLimitChange: vi.fn(),
  };

  it('renders pagination info correctly', () => {
    render(<TracePagination {...defaultProps} />);

    const paginationInfo = screen.getByTestId('trace-pagination-info');
    expect(paginationInfo).toHaveTextContent('Showing 1 to 20 of 100 traces');
  });

  it('renders page indicator correctly', () => {
    render(<TracePagination {...defaultProps} />);

    expect(screen.getByTestId('trace-page-indicator')).toHaveTextContent('Page 1 of 5');
  });

  it('calls onPageChange when clicking next', () => {
    const onPageChange = vi.fn();
    render(<TracePagination {...defaultProps} onPageChange={onPageChange} />);

    fireEvent.click(screen.getByTestId('trace-next-page-button'));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when clicking previous', () => {
    const onPageChange = vi.fn();
    render(<TracePagination {...defaultProps} page={3} onPageChange={onPageChange} />);

    fireEvent.click(screen.getByTestId('trace-previous-page-button'));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('disables previous button on first page', () => {
    render(<TracePagination {...defaultProps} page={1} />);

    expect(screen.getByTestId('trace-previous-page-button')).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<TracePagination {...defaultProps} page={5} />);

    expect(screen.getByTestId('trace-next-page-button')).toBeDisabled();
  });

  it('displays no traces message when total is 0', () => {
    render(<TracePagination {...defaultProps} total={0} totalPages={0} />);

    expect(screen.getByTestId('trace-pagination-info')).toHaveTextContent('No traces');
  });

  it('renders page size selector when onLimitChange is provided', () => {
    render(<TracePagination {...defaultProps} />);

    expect(screen.getByTestId('trace-page-size-select')).toBeInTheDocument();
    expect(screen.getByText('Show')).toBeInTheDocument();
    expect(screen.getByText('per page')).toBeInTheDocument();
  });

  it('does not render page size selector when onLimitChange is not provided', () => {
    render(<TracePagination {...defaultProps} onLimitChange={undefined} />);

    expect(screen.queryByTestId('trace-page-size-select')).not.toBeInTheDocument();
  });

  it('disables buttons when isLoading is true', () => {
    render(<TracePagination {...defaultProps} page={3} isLoading={true} />);

    expect(screen.getByTestId('trace-previous-page-button')).toBeDisabled();
    expect(screen.getByTestId('trace-next-page-button')).toBeDisabled();
  });

  it('calculates correct range for middle pages', () => {
    render(<TracePagination {...defaultProps} page={3} />);

    // Page 3 with limit 20 shows items 41-60
    expect(screen.getByTestId('trace-pagination-info')).toHaveTextContent('41');
    expect(screen.getByTestId('trace-pagination-info')).toHaveTextContent('60');
  });

  it('calculates correct range for last page with partial results', () => {
    // 95 total items, page 5, limit 20 = items 81-95
    render(<TracePagination {...defaultProps} page={5} total={95} totalPages={5} />);

    expect(screen.getByTestId('trace-pagination-info')).toHaveTextContent('81');
    expect(screen.getByTestId('trace-pagination-info')).toHaveTextContent('95');
  });

  it('shows Page 1 of 1 when there are no pages', () => {
    render(<TracePagination {...defaultProps} total={0} totalPages={0} />);

    expect(screen.getByTestId('trace-page-indicator')).toHaveTextContent('Page 1 of 1');
  });
});
