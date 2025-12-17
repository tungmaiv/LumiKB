/**
 * Audit event details modal
 * Story 5.2: Audit Log Viewer
 */

'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { AuditEvent } from '@/types/audit';

export interface AuditEventDetailsModalProps {
  event: AuditEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

export function AuditEventDetailsModal({ event, isOpen, onClose }: AuditEventDetailsModalProps) {
  if (!event) {
    return null;
  }

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    } catch {
      return timestamp;
    }
  };

  const formatJson = (obj: Record<string, unknown> | null): string => {
    if (!obj) return 'N/A';
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return 'Invalid JSON';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-h-[80vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Audit Event Details</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-semibold text-muted-foreground">Event ID</label>
              <p className="mt-1 font-mono text-sm">{event.id}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Timestamp</label>
              <p className="mt-1 text-sm">{formatTimestamp(event.timestamp)}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Event Type</label>
              <p className="mt-1 text-sm">{event.action}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Status</label>
              <p className="mt-1 text-sm">{event.status || 'N/A'}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">User ID</label>
              <p className="mt-1 font-mono text-sm">{event.user_id || 'N/A'}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">User Email</label>
              <p className="mt-1 text-sm">{event.user_email || 'System'}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Resource Type</label>
              <p className="mt-1 text-sm">{event.resource_type || 'N/A'}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Resource ID</label>
              <p className="mt-1 font-mono text-sm">{event.resource_id || 'N/A'}</p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">Duration</label>
              <p className="mt-1 text-sm">
                {event.duration_ms !== null && event.duration_ms !== undefined
                  ? `${event.duration_ms}ms`
                  : 'N/A'}
              </p>
            </div>

            <div>
              <label className="text-sm font-semibold text-muted-foreground">IP Address</label>
              <p className="mt-1 font-mono text-sm">{event.ip_address || 'N/A'}</p>
              {event.ip_address === 'XXX.XXX.XXX.XXX' && (
                <p className="mt-1 text-xs text-muted-foreground">(PII redacted for privacy)</p>
              )}
            </div>
          </div>

          {/* Details JSON */}
          <div>
            <label className="text-sm font-semibold text-muted-foreground">Event Details</label>
            <div className="mt-2 rounded-md border bg-muted p-4">
              <pre className="overflow-x-auto text-xs">{formatJson(event.details)}</pre>
            </div>
            {event.details &&
              Object.keys(event.details).some((key) =>
                ['password', 'token', 'api_key', 'secret'].includes(key)
              ) && (
                <p className="mt-2 text-xs text-muted-foreground">
                  ⚠️ Sensitive fields have been redacted for security
                </p>
              )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
