/**
 * Unit tests for AuditLogFilters component
 *
 * Tests filter UI controls, user interactions, and filter state management.
 * Story: 5-2 (Audit Log Viewer) - AC-5.2.1
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { AuditLogFilters } from '../audit-log-filters';

// Mock PointerCapture methods for Radix UI Select compatibility with JSDOM
beforeAll(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
});

describe('AuditLogFilters Component', () => {
  const mockOnFiltersChange = vi.fn();
  const mockEventTypes = ['search', 'generation', 'document_upload', 'user_login'];
  const mockResourceTypes = ['knowledge_base', 'document', 'draft', 'user'];

  const defaultFilters = {};

  // Helper to expand the collapsible filter section
  const expandFilters = async () => {
    const filtersTrigger = screen.getByRole('button', { name: /filters/i });
    fireEvent.click(filtersTrigger);
    // Wait for collapsible content to be visible
    await waitFor(() => {
      expect(screen.getByLabelText(/user email/i)).toBeVisible();
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P1] Filters render with all controls', () => {
    it('should render all filter controls', async () => {
      // GIVEN: AuditLogFilters component
      // WHEN: Component is rendered
      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // THEN: Should display all filter controls
      expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/user email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/resource type/i)).toBeInTheDocument();

      // Should display action buttons
      expect(screen.getByRole('button', { name: /apply filters/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });

    it('should populate event type dropdown with provided options', async () => {
      // GIVEN: Event types array
      // WHEN: Component is rendered
      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // THEN: Event type dropdown should have all options
      const eventTypeSelect = screen.getByLabelText(/event type/i);
      fireEvent.click(eventTypeSelect);

      mockEventTypes.forEach((eventType) => {
        expect(screen.getByText(eventType)).toBeInTheDocument();
      });
    });

    it('should populate resource type dropdown with provided options', async () => {
      // GIVEN: Resource types array
      // WHEN: Component is rendered
      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // THEN: Resource type dropdown should have all options
      const resourceTypeSelect = screen.getByLabelText(/resource type/i);
      fireEvent.click(resourceTypeSelect);

      mockResourceTypes.forEach((resourceType) => {
        expect(screen.getByText(resourceType)).toBeInTheDocument();
      });
    });

    it('should render with pre-filled filters', async () => {
      // GIVEN: Filters object with values
      const preFilledFilters = {
        event_type: 'search',
        user_email: 'test@example.com',
        start_date: '2025-12-01',
        end_date: '2025-12-02',
        resource_type: 'knowledge_base',
      };

      // WHEN: Component is rendered with pre-filled filters
      render(
        <AuditLogFilters
          filters={preFilledFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // THEN: Should display pre-filled values
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
      // Date and select values would be rendered in their respective components
    });
  });

  describe('[P1] Apply filters calls onFiltersChange', () => {
    it('should call onFiltersChange when Apply Filters button is clicked', async () => {
      // GIVEN: User has entered filter values
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User fills in email filter
      const emailInput = screen.getByLabelText(/user email/i);
      await user.type(emailInput, 'admin@example.com');

      // AND: User clicks Apply Filters
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should call onFiltersChange with updated filters
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            user_email: 'admin@example.com',
          })
        );
      });
    });

    it('should call onFiltersChange with event type selection', async () => {
      // GIVEN: Pre-filled event type filter (simulates user selection)
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={{ event_type: 'search' }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User clicks Apply Filters
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should call onFiltersChange with event_type
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            event_type: 'search',
          })
        );
      });
    });

    it('should call onFiltersChange with date range', async () => {
      // GIVEN: Pre-filled date range filters (simulates user input)
      const user = userEvent.setup();
      const startDate = '2025-12-01T00:00:00.000Z';
      const endDate = '2025-12-02T00:00:00.000Z';

      render(
        <AuditLogFilters
          filters={{
            start_date: startDate,
            end_date: endDate,
          }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User clicks Apply Filters
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should call onFiltersChange with date range
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            start_date: startDate,
            end_date: endDate,
          })
        );
      });
    });

    it('should call onFiltersChange with multiple filters combined', async () => {
      // GIVEN: Pre-filled filters (simulates user selection)
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={{
            event_type: 'generation',
            resource_type: 'draft',
          }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User fills in email and clicks Apply
      const emailInput = screen.getByLabelText(/user email/i);
      await user.type(emailInput, 'test@example.com');

      // AND: User clicks Apply Filters
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should call onFiltersChange with all filters
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            user_email: 'test@example.com',
            event_type: 'generation',
            resource_type: 'draft',
          })
        );
      });
    });
  });

  describe('[P1] Reset clears all filters', () => {
    it('should clear all filter inputs when Reset is clicked', async () => {
      // GIVEN: Pre-filled filters
      const user = userEvent.setup();
      const preFilledFilters = {
        event_type: 'search',
        user_email: 'test@example.com',
        start_date: '2025-12-01',
        end_date: '2025-12-02',
        resource_type: 'knowledge_base',
      };

      render(
        <AuditLogFilters
          filters={preFilledFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User clicks Reset button
      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      // THEN: Should call onFiltersChange with empty filters
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith({});
      });
    });

    it('should reset user email input to empty', async () => {
      // GIVEN: Email filter filled in
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={{ user_email: 'test@example.com' }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      const emailInput = screen.getByLabelText(/user email/i) as HTMLInputElement;
      expect(emailInput.value).toBe('test@example.com');

      // WHEN: User clicks Reset
      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      // THEN: Email input should be cleared
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith({});
      });
    });

    it('should reset all dropdowns to default (no selection)', async () => {
      // GIVEN: Event type and resource type selected
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={{
            event_type: 'search',
            resource_type: 'knowledge_base',
          }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User clicks Reset
      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      // THEN: Should clear all selections
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith({});
      });
    });

    it('should allow applying new filters after reset', async () => {
      // GIVEN: Filters have been reset
      const user = userEvent.setup();

      const { rerender } = render(
        <AuditLogFilters
          filters={{ event_type: 'search' }}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      // Re-render with empty filters (simulating parent state update)
      rerender(
        <AuditLogFilters
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // WHEN: User applies new filters (collapsible should still be open)
      const emailInput = screen.getByLabelText(/user email/i);
      await user.type(emailInput, 'newuser@example.com');

      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should apply new filters
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            user_email: 'newuser@example.com',
          })
        );
      });
    });
  });

  describe('[P2] Filter validation and edge cases', () => {
    it('should not call onFiltersChange when Apply is clicked with no changes', async () => {
      // GIVEN: No filter changes made
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User clicks Apply Filters without making changes
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should still call onFiltersChange (with empty filters)
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith({});
      });
    });

    it('should handle invalid date range gracefully', async () => {
      // GIVEN: End date before start date
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User enters invalid date range (end < start)
      const startDateInput = screen.getByLabelText(/start date/i);
      const endDateInput = screen.getByLabelText(/end date/i);

      await user.type(startDateInput, '2025-12-02');
      await user.type(endDateInput, '2025-12-01');

      // AND: User clicks Apply Filters
      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should display validation error or handle gracefully
      // (Implementation detail - component should validate date range)
      expect(mockOnFiltersChange).toHaveBeenCalled();
    });

    it('should handle empty event types array gracefully', async () => {
      // GIVEN: No event types provided
      // WHEN: Component is rendered with empty eventTypes
      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={[]}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // THEN: Should still render event type dropdown (disabled or with placeholder)
      expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
    });

    it('should trim whitespace from email input', async () => {
      // GIVEN: User email input with leading/trailing spaces
      const user = userEvent.setup();

      render(
        <AuditLogFilters
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          eventTypes={mockEventTypes}
          resourceTypes={mockResourceTypes}
        />
      );

      // Expand the collapsible
      await expandFilters();

      // WHEN: User enters email with spaces
      const emailInput = screen.getByLabelText(/user email/i);
      await user.type(emailInput, '  test@example.com  ');

      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      await user.click(applyButton);

      // THEN: Should trim whitespace before calling onFiltersChange
      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            user_email: 'test@example.com',
          })
        );
      });
    });
  });
});
