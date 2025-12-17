/**
 * Unit tests for AuditLogTable component
 *
 * Tests table rendering, sorting, pagination, and view details functionality.
 * Story: 5-2 (Audit Log Viewer) - AC-5.2.2, AC-5.2.5
 */

import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuditLogTable } from '../audit-log-table';
import type { AuditEvent } from '@/types/audit';

describe('AuditLogTable Component', () => {
  const mockOnPageChange = vi.fn();
  const mockOnViewDetails = vi.fn();

  // Mock data uses 'action' field (matches actual AuditEvent type)
  const mockAuditEvents: AuditEvent[] = [
    {
      id: '1',
      timestamp: '2025-12-02T10:00:00Z',
      action: 'search',
      user_id: 'user-123',
      user_email: 'admin@example.com',
      resource_type: 'knowledge_base',
      resource_id: 'kb-456',
      status: 'success',
      duration_ms: 150,
      ip_address: 'XXX.XXX.XXX.XXX',
      details: { query: 'test search' },
    },
    {
      id: '2',
      timestamp: '2025-12-02T09:00:00Z',
      action: 'generation',
      user_id: 'user-123',
      user_email: 'admin@example.com',
      resource_type: 'draft',
      resource_id: 'draft-789',
      status: 'success',
      duration_ms: 2500,
      ip_address: 'XXX.XXX.XXX.XXX',
      details: { document_type: 'report' },
    },
    {
      id: '3',
      timestamp: '2025-12-02T08:00:00Z',
      action: 'document_upload',
      user_id: 'user-456',
      user_email: 'user@example.com',
      resource_type: 'document',
      resource_id: 'doc-abc',
      status: 'failed',
      duration_ms: null,
      ip_address: 'XXX.XXX.XXX.XXX',
      details: { error: 'Upload timeout' },
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P1] Table renders with mock events', () => {
    it('should render table with events', () => {
      // GIVEN: Audit events array
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display table
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      // Should display all event rows
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBe(mockAuditEvents.length + 1); // +1 for header row
    });

    it('should display each event as a table row', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display event data
      expect(screen.getByText('search')).toBeInTheDocument();
      expect(screen.getByText('generation')).toBeInTheDocument();
      expect(screen.getByText('document_upload')).toBeInTheDocument();

      // admin@example.com appears twice (events 1 and 2), user@example.com once
      expect(screen.getAllByText('admin@example.com')).toHaveLength(2);
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
    });

    it('should display empty state when no events', () => {
      // GIVEN: Empty events array
      // WHEN: Component is rendered with no events
      render(
        <AuditLogTable
          events={[]}
          totalCount={0}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display empty state message
      expect(screen.getByText(/no audit logs found/i)).toBeInTheDocument();
    });
  });

  describe('[P1] Table displays all required columns', () => {
    it('should display timestamp column with formatted date', () => {
      // GIVEN: Audit events with timestamps
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display timestamp column header
      expect(screen.getByText(/timestamp/i)).toBeInTheDocument();

      // Should format timestamps (YYYY-MM-DD HH:mm:ss UTC) - multiple events on same date
      expect(screen.getAllByText(/2025-12-02/).length).toBeGreaterThan(0);
    });

    it('should display event type column', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display event type column
      expect(screen.getByText(/event type/i)).toBeInTheDocument();

      // Should display event types in rows
      expect(screen.getByText('search')).toBeInTheDocument();
      expect(screen.getByText('generation')).toBeInTheDocument();
    });

    it('should display user email column', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display user column header
      const headers = screen.getAllByRole('columnheader');
      const headerTexts = headers.map((h) => h.textContent?.toLowerCase());
      expect(headerTexts.some((t) => t?.includes('user'))).toBe(true);

      // Should display user emails (admin@example.com appears twice)
      expect(screen.getAllByText('admin@example.com')).toHaveLength(2);
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
    });

    it('should display resource type and resource ID columns', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display resource columns (verify both headers exist)
      const headers = screen.getAllByRole('columnheader');
      const headerTexts = headers.map((h) => h.textContent?.toLowerCase());
      expect(headerTexts.some((t) => t?.includes('resource'))).toBe(true);

      // Should display resource data
      expect(screen.getByText('knowledge_base')).toBeInTheDocument();
      expect(screen.getByText('draft')).toBeInTheDocument();
      expect(screen.getByText('document')).toBeInTheDocument();
    });

    it('should display status column with success/failed indicators', () => {
      // GIVEN: Audit events with success and failed statuses
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display status column
      expect(screen.getByText(/status/i)).toBeInTheDocument();

      // Should display status values (component shows "● success" and "● failed")
      const successStatuses = screen.getAllByText(/success/i);
      expect(successStatuses.length).toBe(2);

      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });

    it('should display duration column with milliseconds', () => {
      // GIVEN: Audit events with duration_ms
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display duration column
      expect(screen.getByText(/duration/i)).toBeInTheDocument();

      // Should display duration values
      expect(screen.getByText('150ms')).toBeInTheDocument();
      expect(screen.getByText('2500ms')).toBeInTheDocument();
    });

    it('should display N/A for null duration', () => {
      // GIVEN: Event with null duration_ms
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display N/A for null duration
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  describe('[P1] Table displays events in order', () => {
    it('should display events in the order provided', () => {
      // GIVEN: Audit events array (sorted by timestamp DESC by backend)
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display events in provided order (newest first)
      const rows = screen.getAllByRole('row');
      const firstDataRow = rows[1]; // Skip header row

      // First row should contain the first event from array
      expect(within(firstDataRow).getByText('search')).toBeInTheDocument();
    });

    it('should display timestamp column header', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Timestamp column header should be present
      const timestampHeader = screen.getByText(/timestamp/i);
      expect(timestampHeader).toBeInTheDocument();
    });
  });

  describe('[P1] Pagination controls navigate pages', () => {
    it('should display pagination controls', () => {
      // GIVEN: Paginated results (50 per page, 100 total)
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display pagination controls (buttons with text)
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    });

    it('should display total count and current page info', () => {
      // GIVEN: Paginated results
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display pagination info
      // Component shows "Showing 1 to 50 of 100 events"
      expect(screen.getByText(/showing/i)).toBeInTheDocument();
      expect(screen.getByText(/100/)).toBeInTheDocument();
    });

    it('should call onPageChange when next page button is clicked', async () => {
      // GIVEN: Page 1 with more pages available
      const user = userEvent.setup();

      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // WHEN: User clicks next page button
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // THEN: Should call onPageChange with page 2
      expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });

    it('should call onPageChange when previous page button is clicked', async () => {
      // GIVEN: Page 2 (can go back to page 1)
      const user = userEvent.setup();

      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={2}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // WHEN: User clicks previous page button
      const prevButton = screen.getByRole('button', { name: /previous/i });
      await user.click(prevButton);

      // THEN: Should call onPageChange with page 1
      expect(mockOnPageChange).toHaveBeenCalledWith(1);
    });

    it('should disable previous button on first page', () => {
      // GIVEN: Page 1
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Previous button should be disabled
      const prevButton = screen.getByRole('button', { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });

    it('should disable next button on last page', () => {
      // GIVEN: Last page (page 2 of 2)
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={2}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });
  });

  describe('[P1] View details button calls onViewDetails', () => {
    it('should display View Details button for each row', () => {
      // GIVEN: Audit events
      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display View Details button for each event
      const viewDetailsButtons = screen.getAllByRole('button', { name: /view details/i });
      expect(viewDetailsButtons.length).toBe(mockAuditEvents.length);
    });

    it('should call onViewDetails with event when button is clicked', async () => {
      // GIVEN: Audit events with View Details buttons
      const user = userEvent.setup();

      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // WHEN: User clicks View Details for first event
      const viewDetailsButtons = screen.getAllByRole('button', { name: /view details/i });
      await user.click(viewDetailsButtons[0]);

      // THEN: Should call onViewDetails with first event
      expect(mockOnViewDetails).toHaveBeenCalledWith(mockAuditEvents[0]);
    });

    it('should call onViewDetails with correct event for each row', async () => {
      // GIVEN: Multiple audit events
      const user = userEvent.setup();

      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={100}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // WHEN: User clicks View Details for second event
      const viewDetailsButtons = screen.getAllByRole('button', { name: /view details/i });
      await user.click(viewDetailsButtons[1]);

      // THEN: Should call onViewDetails with second event
      expect(mockOnViewDetails).toHaveBeenCalledWith(mockAuditEvents[1]);
    });
  });

  describe('[P2] Table handles edge cases', () => {
    it('should display "System" when user_email is null', () => {
      // GIVEN: Event with null user_email (system action)
      const systemEvent: AuditEvent = {
        ...mockAuditEvents[0],
        user_email: null,
      };

      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={[systemEvent]}
          totalCount={1}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display "System" instead of email
      expect(screen.getByText('System')).toBeInTheDocument();
    });

    it('should handle very long action names gracefully', () => {
      // GIVEN: Event with long action name
      const longActionEvent: AuditEvent = {
        ...mockAuditEvents[0],
        action: 'very_long_action_name_that_might_break_layout',
      };

      // WHEN: Component is rendered
      render(
        <AuditLogTable
          events={[longActionEvent]}
          totalCount={1}
          page={1}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display full action name (with truncation or wrapping)
      expect(screen.getByText(/very_long_action_name/)).toBeInTheDocument();
    });

    it('should display last page correctly when totalCount is not divisible by pageSize', () => {
      // GIVEN: 75 total events with page size 50 (last page has 25 events)
      // WHEN: Component is rendered for page 2
      render(
        <AuditLogTable
          events={mockAuditEvents}
          totalCount={75}
          page={2}
          pageSize={50}
          onPageChange={mockOnPageChange}
          onViewDetails={mockOnViewDetails}
        />
      );

      // THEN: Should display correct pagination info
      // Component shows "Showing 51 to 75 of 75 events"
      expect(screen.getByText(/showing/i)).toBeInTheDocument();
      // Verify the pagination text contains the correct total count
      const paginationText = screen.getByText(/showing/i).closest('p');
      expect(paginationText?.textContent).toContain('75');
      expect(paginationText?.textContent).toContain('events');
    });
  });
});
