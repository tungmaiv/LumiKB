/**
 * Audit log table component with sorting and pagination
 * Story 5.2: Audit Log Viewer
 */

'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AuditEvent } from '@/types/audit';

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;

export interface AuditLogTableProps {
  events: AuditEvent[];
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  onViewDetails: (event: AuditEvent) => void;
  isLoading?: boolean;
}

export function AuditLogTable({
  events,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onViewDetails,
  isLoading = false,
}: AuditLogTableProps) {
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, totalCount);
  const hasMore = page * pageSize < totalCount;
  const hasPrevious = page > 1;

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    } catch {
      return timestamp;
    }
  };

  const formatDuration = (durationMs: number | null): string => {
    if (durationMs === null || durationMs === undefined) {
      return 'N/A';
    }
    return `${durationMs}ms`;
  };

  const getStatusBadge = (status: string | null): React.JSX.Element => {
    if (!status) {
      return <span className="text-muted-foreground">N/A</span>;
    }

    if (status === 'success' || status.toLowerCase().includes('success')) {
      return (
        <span className="inline-flex items-center rounded-full bg-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-500">
          ● {status}
        </span>
      );
    }

    if (status === 'failed' || status.toLowerCase().includes('fail')) {
      return (
        <span className="inline-flex items-center rounded-full bg-red-500/20 px-2.5 py-0.5 text-xs font-medium text-red-500">
          ● {status}
        </span>
      );
    }

    return (
      <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
        {status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary mx-auto"></div>
          <p className="text-sm text-muted-foreground">Loading audit logs...</p>
        </div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
        <div className="text-center">
          <p className="text-lg font-medium">No audit logs found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try adjusting your filters or date range
          </p>
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-4">
      {/* Pagination Bar - Top */}
      <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
        <div className="flex items-center gap-4">
          {/* Page Size Selector */}
          {onPageSizeChange && (
            <div className="flex items-center gap-2">
              <label htmlFor="page-size" className="text-sm text-muted-foreground">
                Show
              </label>
              <Select
                value={pageSize.toString()}
                onValueChange={(value) => onPageSizeChange(parseInt(value, 10))}
              >
                <SelectTrigger id="page-size" className="w-[80px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <SelectItem key={size} value={size.toString()}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-sm text-muted-foreground">per page</span>
            </div>
          )}

          {/* Results Info */}
          <p className="text-sm text-muted-foreground">
            Showing <span className="font-medium">{totalCount > 0 ? startIndex : 0}</span> to{' '}
            <span className="font-medium">{endIndex}</span> of{' '}
            <span className="font-medium">{totalCount}</span> events
          </p>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={!hasPrevious}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground px-2">
            Page <span className="font-medium">{page}</span> of{' '}
            <span className="font-medium">{totalPages || 1}</span>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={!hasMore}
          >
            Next
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border bg-card">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Timestamp
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Event Type
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                User
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Resource
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Resource ID
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Status
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Duration
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {events.map((event) => (
              <tr key={event.id} className="hover:bg-muted/50">
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  {formatTimestamp(event.timestamp)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium">{event.action}</td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                  {event.user_email || 'System'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                  {event.resource_type || 'N/A'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-muted-foreground">
                  {event.resource_id ? event.resource_id.slice(0, 8) + '...' : 'N/A'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  {getStatusBadge(event.status)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                  {formatDuration(event.duration_ms)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewDetails(event)}
                    className="text-primary hover:text-primary/80"
                  >
                    View Details
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
