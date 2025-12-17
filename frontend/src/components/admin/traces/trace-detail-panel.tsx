/**
 * Trace Detail Panel Component
 *
 * Story 9-8: Trace Viewer UI Component
 * AC3: Click trace row to view detail panel (slide-out)
 * AC4: Trace detail shows timeline of spans in waterfall view
 */
'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  Clock,
  Layers,
  User,
  FileText,
  Hash,
  Calendar,
  AlertCircle,
  CheckCircle,
  Timer,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { useTraceDetail } from '@/hooks/useTraces';
import type { SpanDetail } from '@/hooks/useTraces';

import { SpanDetailCard } from './span-detail';
import { WaterfallTimeline } from './waterfall-timeline';

interface TraceDetailPanelProps {
  traceId: string | null;
  onClose: () => void;
}

/**
 * Status badge for trace
 */
function TraceStatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
    in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300',
  };

  return <Badge className={cn(variants[status] || variants.completed)}>{status}</Badge>;
}

/**
 * Loading skeleton for trace detail
 */
function TraceDetailSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <div className="space-y-2 pt-4">
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    </div>
  );
}

/**
 * Error display component
 */
function ErrorDisplay({ message }: { message: string }) {
  return (
    <div className="p-4">
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
        <p className="text-sm text-destructive">{message}</p>
      </div>
    </div>
  );
}

/**
 * Format a metadata value for display
 */
function formatMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return value.toLocaleString();
  if (typeof value === 'string') {
    // Check if it looks like a date/timestamp
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
      try {
        return format(new Date(value), 'yyyy-MM-dd HH:mm:ss');
      } catch {
        return value;
      }
    }
    return value;
  }
  if (Array.isArray(value)) return `[${value.length} items]`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/**
 * Get an icon for a metadata key
 */
function getMetadataIcon(key: string) {
  const iconMap: Record<string, React.ReactNode> = {
    document_id: <FileText className="h-4 w-4 text-blue-500" />,
    task_id: <Hash className="h-4 w-4 text-purple-500" />,
    chunk_count: <Layers className="h-4 w-4 text-green-500" />,
    extracted_chars: <FileText className="h-4 w-4 text-orange-500" />,
    page_count: <FileText className="h-4 w-4 text-cyan-500" />,
    section_count: <Layers className="h-4 w-4 text-pink-500" />,
    total_duration_ms: <Timer className="h-4 w-4 text-yellow-500" />,
    error_message: <AlertCircle className="h-4 w-4 text-red-500" />,
    status: <CheckCircle className="h-4 w-4 text-green-500" />,
    timestamp: <Calendar className="h-4 w-4 text-gray-500" />,
  };
  return iconMap[key] || <Hash className="h-4 w-4 text-gray-400" />;
}

/**
 * Format a metadata key for display
 */
function formatMetadataKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Metadata display component - shows metadata as key-value pairs in a nice format
 */
function MetadataDisplay({ metadata }: { metadata: Record<string, unknown> }) {
  // Group important keys first
  const priorityKeys = [
    'document_id',
    'task_id',
    'status',
    'chunk_count',
    'extracted_chars',
    'page_count',
    'section_count',
    'total_duration_ms',
    'error_message',
  ];
  const sortedKeys = [
    ...priorityKeys.filter((k) => k in metadata),
    ...Object.keys(metadata).filter((k) => !priorityKeys.includes(k)),
  ];

  return (
    <Card className="bg-muted/50">
      <CardContent className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {sortedKeys.map((key) => {
            const value = metadata[key];
            const isError = key === 'error_message' && value;

            return (
              <div
                key={key}
                className={cn(
                  'flex items-start gap-2 p-2 rounded-md',
                  isError ? 'bg-red-50 dark:bg-red-900/20' : 'bg-background'
                )}
              >
                <div className="mt-0.5 shrink-0">{getMetadataIcon(key)}</div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-muted-foreground">
                    {formatMetadataKey(key)}
                  </div>
                  <div
                    className={cn(
                      'text-sm font-mono break-all',
                      isError ? 'text-red-600 dark:text-red-400' : ''
                    )}
                  >
                    {formatMetadataValue(value)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export function TraceDetailPanel({ traceId, onClose }: TraceDetailPanelProps) {
  const { data: trace, isLoading, error } = useTraceDetail(traceId);
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);

  // Find the selected span for detail display
  const selectedSpan: SpanDetail | undefined = trace?.spans.find(
    (s) => s.span_id === selectedSpanId
  );

  return (
    <Sheet open={!!traceId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-2xl lg:max-w-4xl overflow-y-auto"
        data-testid="trace-detail-panel"
      >
        {isLoading ? (
          <TraceDetailSkeleton />
        ) : error ? (
          <>
            <SheetHeader>
              <SheetTitle>Trace Detail</SheetTitle>
            </SheetHeader>
            <ErrorDisplay
              message={error instanceof Error ? error.message : 'Failed to load trace'}
            />
          </>
        ) : trace ? (
          <>
            <SheetHeader className="pb-4">
              <div className="flex items-center gap-2">
                <SheetTitle className="text-xl">
                  {trace.name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </SheetTitle>
                <TraceStatusBadge status={trace.status} />
              </div>
              <SheetDescription>
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {trace.duration_ms !== null ? `${trace.duration_ms}ms` : 'In progress'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Layers className="h-4 w-4" />
                    {trace.spans.length} spans
                  </span>
                  {trace.user_id && (
                    <span className="flex items-center gap-1">
                      <User className="h-4 w-4" />
                      {trace.user_id.slice(0, 8)}...
                    </span>
                  )}
                  <span className="text-muted-foreground">
                    {format(new Date(trace.started_at), 'yyyy-MM-dd HH:mm:ss')}
                  </span>
                </div>
              </SheetDescription>
            </SheetHeader>

            {/* Trace ID for reference */}
            <div className="mb-4 text-xs text-muted-foreground font-mono">
              Trace ID: {trace.trace_id}
            </div>

            {/* Waterfall Timeline */}
            <div className="mb-6">
              <h3 className="text-sm font-medium mb-2">Timeline</h3>
              <WaterfallTimeline
                spans={trace.spans}
                totalDuration={trace.duration_ms || 1}
                selectedSpanId={selectedSpanId}
                onSelectSpan={setSelectedSpanId}
              />
            </div>

            {/* Selected Span Detail */}
            {selectedSpan && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-2">Span Detail</h3>
                <SpanDetailCard span={selectedSpan} />
              </div>
            )}

            {/* Trace metadata if available - show as formatted key-value pairs */}
            {trace.metadata && Object.keys(trace.metadata).length > 0 && (
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-medium mb-3">Trace Metadata</h3>
                <MetadataDisplay metadata={trace.metadata as Record<string, unknown>} />
              </div>
            )}
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
