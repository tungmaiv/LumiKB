/**
 * Trace List Component
 *
 * Story 9-8: Trace Viewer UI Component
 * AC1: Displays operation type, status, duration, user, and timestamp
 */
'use client';

import { formatDistanceToNow } from 'date-fns';
import { CheckCircle, Circle, Clock, FileText, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import type { TraceListItem } from '@/hooks/useTraces';

interface TraceListProps {
  traces: TraceListItem[];
  selectedTraceId: string | null;
  onSelectTrace: (traceId: string) => void;
  isLoading?: boolean;
}

/**
 * Format duration in human-readable format
 */
function formatDuration(ms: number | null): string {
  if (ms === null) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

/**
 * Status badge component with color coding
 * AC6: Error spans highlighted in red
 */
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: typeof CheckCircle; className: string }> = {
    completed: {
      icon: CheckCircle,
      className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    },
    failed: {
      icon: XCircle,
      className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    },
    in_progress: {
      icon: Clock,
      className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    },
    pending: {
      icon: Circle,
      className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    },
  };

  const { icon: Icon, className } = config[status] || config.pending;

  return (
    <Badge className={cn('gap-1', className)}>
      <Icon className="h-3 w-3" />
      {status}
    </Badge>
  );
}

/**
 * Format operation type for display
 */
function formatOperationType(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Loading skeleton for trace list
 */
export function TraceListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function TraceList({
  traces,
  selectedTraceId,
  onSelectTrace,
  isLoading,
}: TraceListProps) {
  if (isLoading) {
    return <TraceListSkeleton />;
  }

  if (traces.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        No traces found matching filters
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Operation</TableHead>
          <TableHead>Document</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Spans</TableHead>
          <TableHead>Time</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {traces.map((trace) => (
          <TableRow
            key={trace.trace_id}
            className={cn(
              'cursor-pointer',
              selectedTraceId === trace.trace_id && 'bg-muted'
            )}
            onClick={() => onSelectTrace(trace.trace_id)}
            data-testid={`trace-row-${trace.trace_id}`}
          >
            <TableCell className="font-medium">
              {formatOperationType(trace.name)}
            </TableCell>
            <TableCell>
              {trace.document_id ? (
                <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
                  <FileText className="h-3 w-3 flex-shrink-0" />
                  <span className="break-all">{trace.document_id}</span>
                </span>
              ) : (
                <span className="text-xs text-muted-foreground">-</span>
              )}
            </TableCell>
            <TableCell>
              <StatusBadge status={trace.status} />
            </TableCell>
            <TableCell className="font-mono text-sm">
              {formatDuration(trace.duration_ms)}
            </TableCell>
            <TableCell>{trace.span_count}</TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatDistanceToNow(new Date(trace.started_at), { addSuffix: true })}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
