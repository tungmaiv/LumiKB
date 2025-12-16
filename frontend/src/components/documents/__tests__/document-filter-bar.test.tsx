import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentFilterBar } from '../document-filter-bar';
import { DocumentFilterState, DocumentFilterActions } from '@/lib/hooks/use-document-filters';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the useDocumentFilters hook
vi.mock('@/lib/hooks/use-document-filters', () => ({
  useDocumentFilters: vi.fn(),
}));

describe('DocumentFilterBar', () => {
  const defaultFilters: DocumentFilterState = {
    page: 1,
    limit: 20,
    sortBy: 'created_at',
    sortOrder: 'desc',
    search: undefined,
    status: undefined,
    mimeType: undefined,
    tags: undefined,
    dateFrom: undefined,
    dateTo: undefined,
  };

  const mockActions: DocumentFilterActions = {
    setSearch: vi.fn(),
    setStatus: vi.fn(),
    setMimeType: vi.fn(),
    setTags: vi.fn(),
    setDateRange: vi.fn(),
    setPage: vi.fn(),
    setLimit: vi.fn(),
    setSortBy: vi.fn(),
    setSortOrder: vi.fn(),
    resetFilters: vi.fn(),
    updateFilters: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input', () => {
    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    expect(screen.getByTestId('document-search-input')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search documents...')).toBeInTheDocument();
  });

  it('renders status filter dropdown', () => {
    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    expect(screen.getByTestId('status-filter')).toBeInTheDocument();
  });

  it('renders type filter dropdown', () => {
    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    expect(screen.getByTestId('type-filter')).toBeInTheDocument();
  });

  it('renders advanced filters toggle', () => {
    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    expect(screen.getByTestId('advanced-filters-toggle')).toBeInTheDocument();
    expect(screen.getByText('Advanced')).toBeInTheDocument();
  });

  it('does not show clear filters button when no filters active', () => {
    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    expect(screen.queryByTestId('clear-filters-button')).not.toBeInTheDocument();
  });

  it('shows clear filters button when filters are active', () => {
    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, search: 'test' }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={1}
      />
    );

    expect(screen.getByTestId('clear-filters-button')).toBeInTheDocument();
  });

  it('calls resetFilters when clear button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, search: 'test' }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={1}
      />
    );

    await user.click(screen.getByTestId('clear-filters-button'));
    expect(mockActions.resetFilters).toHaveBeenCalled();
  });

  it('toggles advanced filters panel', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    // Panel should not be visible initially
    expect(screen.queryByTestId('advanced-filters-panel')).not.toBeInTheDocument();

    // Click to show
    await user.click(screen.getByTestId('advanced-filters-toggle'));
    expect(screen.getByTestId('advanced-filters-panel')).toBeInTheDocument();

    // Click again to hide
    await user.click(screen.getByTestId('advanced-filters-toggle'));
    expect(screen.queryByTestId('advanced-filters-panel')).not.toBeInTheDocument();
  });

  it('shows date range inputs in advanced panel', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
      />
    );

    await user.click(screen.getByTestId('advanced-filters-toggle'));

    expect(screen.getByTestId('date-from-input')).toBeInTheDocument();
    expect(screen.getByTestId('date-to-input')).toBeInTheDocument();
  });

  it('shows available tags in advanced panel', async () => {
    const user = userEvent.setup();
    const availableTags = ['finance', 'report', 'legal'];

    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
        availableTags={availableTags}
      />
    );

    await user.click(screen.getByTestId('advanced-filters-toggle'));

    expect(screen.getByTestId('tag-filters')).toBeInTheDocument();
    expect(screen.getByTestId('tag-filter-finance')).toBeInTheDocument();
    expect(screen.getByTestId('tag-filter-report')).toBeInTheDocument();
    expect(screen.getByTestId('tag-filter-legal')).toBeInTheDocument();
  });

  it('calls setTags when tag is clicked', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={defaultFilters}
        actions={mockActions}
        hasActiveFilters={false}
        activeFilterCount={0}
        availableTags={['finance']}
      />
    );

    await user.click(screen.getByTestId('advanced-filters-toggle'));
    await user.click(screen.getByTestId('tag-filter-finance'));

    expect(mockActions.setTags).toHaveBeenCalledWith(['finance']);
  });

  it('removes tag from filter when already selected', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, tags: ['finance'] }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={1}
        availableTags={['finance', 'legal']}
      />
    );

    await user.click(screen.getByTestId('advanced-filters-toggle'));
    await user.click(screen.getByTestId('tag-filter-finance'));

    expect(mockActions.setTags).toHaveBeenCalledWith([]);
  });

  it('shows active filter count badge', () => {
    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, search: 'test', status: 'READY' }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={2}
      />
    );

    const badge = screen.getByTestId('advanced-filters-toggle').querySelector('.rounded-full');
    expect(badge).toHaveTextContent('2');
  });

  it('displays pre-filled search value', () => {
    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, search: 'existing search' }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={1}
      />
    );

    expect(screen.getByTestId('document-search-input')).toHaveValue('existing search');
  });

  it('shows active filters summary when panel is open', async () => {
    const user = userEvent.setup();

    render(
      <DocumentFilterBar
        filters={{ ...defaultFilters, search: 'test', status: 'READY' }}
        actions={mockActions}
        hasActiveFilters={true}
        activeFilterCount={2}
      />
    );

    await user.click(screen.getByTestId('advanced-filters-toggle'));

    expect(screen.getByText('Active filters:')).toBeInTheDocument();
    expect(screen.getByText(/Search: "test"/)).toBeInTheDocument();
    expect(screen.getByText(/Status: READY/)).toBeInTheDocument();
  });
});
