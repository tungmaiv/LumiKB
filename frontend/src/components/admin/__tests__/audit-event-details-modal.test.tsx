/**
 * Unit tests for AuditEventDetailsModal component
 *
 * Tests modal display, JSON formatting, and event detail rendering.
 * Story: 5-2 (Audit Log Viewer) - AC-5.2.3
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuditEventDetailsModal } from '../audit-event-details-modal';
import type { AuditEvent } from '@/types/audit';

describe('AuditEventDetailsModal Component', () => {
  const mockOnClose = vi.fn();

  const mockAuditEvent: AuditEvent = {
    id: '1',
    timestamp: '2025-12-02T10:00:00Z',
    action: 'search',
    user_id: 'user-123',
    user_email: 'test@example.com',
    resource_type: 'knowledge_base',
    resource_id: 'kb-456',
    status: 'success',
    duration_ms: 150,
    ip_address: 'XXX.XXX.XXX.XXX', // Redacted
    details: {
      query: 'test search',
      results_count: 10,
      password: '[REDACTED]', // Sensitive field redacted
      token: '[REDACTED]',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P1] Modal displays event details', () => {
    it('should display modal when isOpen is true', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/audit event details/i)).toBeInTheDocument();
    });

    it('should not display modal when isOpen is false', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={false}
          onClose={mockOnClose}
        />
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should display event ID', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Event ID label and value
      expect(screen.getByText('Event ID')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('should display event type (action)', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Event Type')).toBeInTheDocument();
      expect(screen.getByText('search')).toBeInTheDocument();
    });

    it('should display timestamp in formatted format', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Timestamp')).toBeInTheDocument();
      // Formatted: 2025-12-02 10:00:00 UTC
      expect(screen.getByText(/2025-12-02.*10:00:00.*UTC/)).toBeInTheDocument();
    });

    it('should display status', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('success')).toBeInTheDocument();
    });

    it('should display user information', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('User ID')).toBeInTheDocument();
      expect(screen.getByText('user-123')).toBeInTheDocument();
      expect(screen.getByText('User Email')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    it('should display resource information', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Resource Type')).toBeInTheDocument();
      expect(screen.getByText('knowledge_base')).toBeInTheDocument();
      expect(screen.getByText('Resource ID')).toBeInTheDocument();
      expect(screen.getByText('kb-456')).toBeInTheDocument();
    });

    it('should display duration in milliseconds', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Duration')).toBeInTheDocument();
      expect(screen.getByText('150ms')).toBeInTheDocument();
    });

    it('should return null when event is null', () => {
      const { container } = render(
        <AuditEventDetailsModal
          event={null}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should render nothing
      expect(container.firstChild).toBeNull();
    });
  });

  describe('[P1] IP address and PII display', () => {
    it('should display redacted IP address with privacy note', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('IP Address')).toBeInTheDocument();
      expect(screen.getByText('XXX.XXX.XXX.XXX')).toBeInTheDocument();
      expect(screen.getByText(/pii redacted for privacy/i)).toBeInTheDocument();
    });

    it('should display unredacted IP address without privacy note', () => {
      const unredactedEvent: AuditEvent = {
        ...mockAuditEvent,
        ip_address: '192.168.1.100',
      };

      render(
        <AuditEventDetailsModal
          event={unredactedEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
      expect(screen.queryByText(/pii redacted for privacy/i)).not.toBeInTheDocument();
    });

    it('should display N/A when IP address is null', () => {
      const eventWithoutIP: AuditEvent = {
        ...mockAuditEvent,
        ip_address: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithoutIP}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Find the N/A after IP Address label
      const ipSection = screen.getByText('IP Address').parentElement;
      expect(ipSection).toHaveTextContent('N/A');
    });
  });

  describe('[P1] Event details JSON display', () => {
    it('should display event details as formatted JSON', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Event Details')).toBeInTheDocument();
      // Check for JSON content
      const preElement = document.querySelector('pre');
      expect(preElement).toBeInTheDocument();
      expect(preElement?.textContent).toContain('query');
      expect(preElement?.textContent).toContain('test search');
    });

    it('should display sensitive field warning when password present', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/sensitive fields have been redacted/i)).toBeInTheDocument();
    });

    it('should not display sensitive field warning when no sensitive keys', () => {
      const eventWithoutSensitiveData: AuditEvent = {
        ...mockAuditEvent,
        details: {
          query: 'test search',
          results_count: 10,
        },
      };

      render(
        <AuditEventDetailsModal
          event={eventWithoutSensitiveData}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.queryByText(/sensitive fields have been redacted/i)).not.toBeInTheDocument();
    });

    it('should display N/A when details is null', () => {
      const eventWithoutDetails: AuditEvent = {
        ...mockAuditEvent,
        details: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithoutDetails}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const preElement = document.querySelector('pre');
      expect(preElement?.textContent).toBe('N/A');
    });
  });

  describe('[P2] Modal close functionality', () => {
    it('should call onClose when dialog is closed via onOpenChange', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Shadcn Dialog uses onOpenChange prop which maps to onClose
      // Find and click the close button
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('[P2] N/A displays for missing fields', () => {
    it('should display N/A for null status', () => {
      const eventWithNullStatus: AuditEvent = {
        ...mockAuditEvent,
        status: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithNullStatus}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Find Status section and verify N/A
      const statusSection = screen.getByText('Status').parentElement;
      expect(statusSection).toHaveTextContent('N/A');
    });

    it('should display N/A for null duration', () => {
      const eventWithNullDuration: AuditEvent = {
        ...mockAuditEvent,
        duration_ms: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithNullDuration}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Find Duration section and verify N/A
      const durationSection = screen.getByText('Duration').parentElement;
      expect(durationSection).toHaveTextContent('N/A');
    });

    it('should display System for null user_email', () => {
      const eventWithNullEmail: AuditEvent = {
        ...mockAuditEvent,
        user_email: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithNullEmail}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Find User Email section and verify System
      const emailSection = screen.getByText('User Email').parentElement;
      expect(emailSection).toHaveTextContent('System');
    });

    it('should display N/A for null resource_type', () => {
      const eventWithNullResourceType: AuditEvent = {
        ...mockAuditEvent,
        resource_type: null,
      };

      render(
        <AuditEventDetailsModal
          event={eventWithNullResourceType}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Find Resource Type section and verify N/A
      const resourceTypeSection = screen.getByText('Resource Type').parentElement;
      expect(resourceTypeSection).toHaveTextContent('N/A');
    });
  });

  describe('[P2] Accessibility', () => {
    it('should have accessible dialog role', () => {
      render(
        <AuditEventDetailsModal
          event={mockAuditEvent}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });
});
