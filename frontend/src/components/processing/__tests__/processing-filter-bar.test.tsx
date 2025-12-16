/**
 * Unit tests for ProcessingFilterBar component
 * Story 5-23 (AC-5.23.2): Filter by file type, status, or processing step
 *
 * Tests filter controls, collapsible behavior, and filter application.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProcessingFilterBar } from '../processing-filter-bar';
import type { ProcessingFilters } from '@/types/processing';

describe('ProcessingFilterBar', () => {
  const mockOnFiltersChange = vi.fn();
  const defaultFilters: ProcessingFilters = {};

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should render search input - AC-5.23.2', () => {
    // Arrange & Act
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Assert
    expect(screen.getByPlaceholderText('Search documents...')).toBeInTheDocument();
  });

  it('[P0] should render Filters toggle button - AC-5.23.2', () => {
    // Arrange & Act
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Assert
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('[P0] should show filter panel when Filters is clicked - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Act - click the Filters button
    await user.click(screen.getByText('Filters'));

    // Assert - filter labels should be visible
    expect(screen.getByText('File Type')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Processing Step')).toBeInTheDocument();
    expect(screen.getByText('Sort By')).toBeInTheDocument();
  });

  it('[P0] should have Apply and Reset buttons in filter panel - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Act - expand filters
    await user.click(screen.getByText('Filters'));

    // Assert
    expect(screen.getByRole('button', { name: 'Apply Filters' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset' })).toBeInTheDocument();
  });

  it('[P0] should call onFiltersChange when Apply is clicked - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Expand filters
    await user.click(screen.getByText('Filters'));

    // Act - click Apply
    await user.click(screen.getByRole('button', { name: 'Apply Filters' }));

    // Assert
    expect(mockOnFiltersChange).toHaveBeenCalled();
  });

  it('[P0] should apply filters on Enter key in search - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Act - type in search and press Enter
    const searchInput = screen.getByPlaceholderText('Search documents...');
    await user.type(searchInput, 'test.pdf{Enter}');

    // Assert
    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'test.pdf' })
    );
  });

  it('[P0] should reset filters when Reset is clicked - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    const filtersWithValues: ProcessingFilters = {
      name: 'test',
      status: 'processing',
      file_type: 'pdf',
    };
    render(
      <ProcessingFilterBar
        filters={filtersWithValues}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Expand filters
    await user.click(screen.getByText('Filters'));

    // Act - click Reset
    await user.click(screen.getByRole('button', { name: 'Reset' }));

    // Assert
    expect(mockOnFiltersChange).toHaveBeenCalledWith({});
  });

  it('[P1] should show active filter count badge - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Expand and type in search
    const searchInput = screen.getByPlaceholderText('Search documents...');
    await user.type(searchInput, 'test');

    // Assert - badge with count should appear
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('[P1] should preserve search input value from filters prop', () => {
    // Arrange
    const filtersWithName: ProcessingFilters = { name: 'existing-search' };

    // Act
    render(
      <ProcessingFilterBar
        filters={filtersWithName}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Assert
    const searchInput = screen.getByPlaceholderText('Search documents...');
    expect(searchInput).toHaveValue('existing-search');
  });

  it('[P1] should trim whitespace from search when applying - AC-5.23.2', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Type search with whitespace
    const searchInput = screen.getByPlaceholderText('Search documents...');
    await user.type(searchInput, '  test.pdf  ');

    // Expand and apply
    await user.click(screen.getByText('Filters'));
    await user.click(screen.getByRole('button', { name: 'Apply Filters' }));

    // Assert - should be trimmed
    expect(mockOnFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'test.pdf' })
    );
  });

  it('[P2] should have filter labels for accessibility', async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <ProcessingFilterBar
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
      />
    );

    // Expand filters
    await user.click(screen.getByText('Filters'));

    // Assert - labels should be present
    expect(screen.getByLabelText('File Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Processing Step')).toBeInTheDocument();
    expect(screen.getByLabelText('Sort By')).toBeInTheDocument();
  });
});
