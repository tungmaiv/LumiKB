import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentPagination } from '../document-pagination';
import { vi, describe, it, expect, beforeEach } from 'vitest';

describe('DocumentPagination', () => {
  const defaultProps = {
    page: 1,
    totalPages: 5,
    total: 100,
    limit: 25,
    onPageChange: vi.fn(),
    onLimitChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders pagination info', () => {
    render(<DocumentPagination {...defaultProps} />);

    expect(screen.getByTestId('pagination-info')).toHaveTextContent(
      'Showing 1 to 25 of 100 documents'
    );
  });

  it('shows correct item range for middle page', () => {
    render(<DocumentPagination {...defaultProps} page={3} />);

    expect(screen.getByTestId('pagination-info')).toHaveTextContent(
      'Showing 51 to 75 of 100 documents'
    );
  });

  it('shows correct item range for last page', () => {
    render(<DocumentPagination {...defaultProps} page={4} total={92} totalPages={4} />);

    expect(screen.getByTestId('pagination-info')).toHaveTextContent(
      'Showing 76 to 92 of 92 documents'
    );
  });

  it('shows "No documents" when total is 0', () => {
    render(<DocumentPagination {...defaultProps} total={0} totalPages={0} />);

    expect(screen.getByTestId('pagination-info')).toHaveTextContent('No documents');
  });

  it('renders navigation buttons', () => {
    render(<DocumentPagination {...defaultProps} />);

    expect(screen.getByTestId('previous-page-button')).toBeInTheDocument();
    expect(screen.getByTestId('next-page-button')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(<DocumentPagination {...defaultProps} page={1} />);

    expect(screen.getByTestId('previous-page-button')).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<DocumentPagination {...defaultProps} page={5} />);

    expect(screen.getByTestId('next-page-button')).toBeDisabled();
  });

  it('enables all buttons on middle page', () => {
    render(<DocumentPagination {...defaultProps} page={3} />);

    expect(screen.getByTestId('previous-page-button')).not.toBeDisabled();
    expect(screen.getByTestId('next-page-button')).not.toBeDisabled();
  });

  it('shows current page indicator in "Page X of Y" format', () => {
    render(<DocumentPagination {...defaultProps} page={3} />);

    expect(screen.getByTestId('page-indicator')).toHaveTextContent('Page 3 of 5');
  });

  it('calls onPageChange with previous page when previous button clicked', async () => {
    const user = userEvent.setup();

    render(<DocumentPagination {...defaultProps} page={3} />);

    await user.click(screen.getByTestId('previous-page-button'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange with next page when next button clicked', async () => {
    const user = userEvent.setup();

    render(<DocumentPagination {...defaultProps} page={3} />);

    await user.click(screen.getByTestId('next-page-button'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(4);
  });

  it('renders page size selector when onLimitChange provided', () => {
    render(<DocumentPagination {...defaultProps} />);

    expect(screen.getByTestId('page-size-select')).toBeInTheDocument();
  });

  it('renders "Show X per page" format', () => {
    render(<DocumentPagination {...defaultProps} />);

    expect(screen.getByText('Show')).toBeInTheDocument();
    expect(screen.getByText('per page')).toBeInTheDocument();
  });

  it('does not render page size selector when onLimitChange not provided', () => {
    const { onLimitChange, ...propsWithoutLimit } = defaultProps;

    render(<DocumentPagination {...propsWithoutLimit} />);

    expect(screen.queryByTestId('page-size-select')).not.toBeInTheDocument();
  });

  it('disables buttons when loading', () => {
    render(<DocumentPagination {...defaultProps} page={3} isLoading />);

    expect(screen.getByTestId('previous-page-button')).toBeDisabled();
    expect(screen.getByTestId('next-page-button')).toBeDisabled();
  });

  it('handles single page correctly', () => {
    render(<DocumentPagination {...defaultProps} page={1} totalPages={1} total={15} />);

    expect(screen.getByTestId('page-indicator')).toHaveTextContent('Page 1 of 1');
    expect(screen.getByTestId('previous-page-button')).toBeDisabled();
    expect(screen.getByTestId('next-page-button')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<DocumentPagination {...defaultProps} className="custom-class" />);

    expect(screen.getByTestId('document-pagination')).toHaveClass('custom-class');
  });

  it('shows Previous and Next text buttons', () => {
    render(<DocumentPagination {...defaultProps} page={2} />);

    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });
});
