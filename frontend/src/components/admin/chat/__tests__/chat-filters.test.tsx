/**
 * Chat Filters Component Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 * AC6, AC7: Search and filters for user, KB, and date range
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ChatFilters } from '../chat-filters';
import type { ChatHistoryFilters } from '@/hooks/useChatHistory';

// Mock the useDebounce hook
vi.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: string) => value,
}));

describe('ChatFilters', () => {
  it('renders filter controls', () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {};

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} />);

    // Check filter elements are present
    expect(screen.getByPlaceholderText('Search messages...')).toBeInTheDocument();
    expect(screen.getByTestId('user-filter')).toBeInTheDocument();
    expect(screen.getByTestId('kb-filter')).toBeInTheDocument();
    expect(screen.getByTestId('date-range-filter')).toBeInTheDocument();
  });

  it('calls onFiltersChange when search input changes', async () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {};

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} />);

    const searchInput = screen.getByPlaceholderText('Search messages...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });

    // Wait for filter change to be called
    await waitFor(() => {
      expect(onFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          searchQuery: 'test query',
        })
      );
    });
  });

  it('displays current filter values', () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {
      searchQuery: 'existing search',
    };

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} />);

    const searchInput = screen.getByPlaceholderText('Search messages...') as HTMLInputElement;
    expect(searchInput.value).toBe('existing search');
  });

  it('shows clear button when filters are active', async () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {
      searchQuery: 'test',
    };

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} />);

    // Look for clear button
    const clearButton = screen.getByTestId('clear-filters');
    expect(clearButton).toBeInTheDocument();

    fireEvent.click(clearButton);
    await waitFor(() => {
      expect(onFiltersChange).toHaveBeenCalledWith({});
    });
  });

  it('does not show clear button when no filters are active', () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {};

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} />);

    // Clear button should not be present
    expect(screen.queryByTestId('clear-filters')).not.toBeInTheDocument();
  });

  it('renders user options when provided', () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {};
    const users = [
      { id: 'user-1', name: 'Alice' },
      { id: 'user-2', name: 'Bob' },
    ];

    render(<ChatFilters filters={filters} onFiltersChange={onFiltersChange} users={users} />);

    // User filter should be present
    expect(screen.getByTestId('user-filter')).toBeInTheDocument();
  });

  it('renders KB options when provided', () => {
    const onFiltersChange = vi.fn();
    const filters: ChatHistoryFilters = {};
    const knowledgeBases = [
      { id: 'kb-1', name: 'Tech Docs' },
      { id: 'kb-2', name: 'HR Policies' },
    ];

    render(
      <ChatFilters
        filters={filters}
        onFiltersChange={onFiltersChange}
        knowledgeBases={knowledgeBases}
      />
    );

    // KB filter should be present
    expect(screen.getByTestId('kb-filter')).toBeInTheDocument();
  });
});
