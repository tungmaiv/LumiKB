/**
 * Waterfall Timeline Component
 *
 * Story 9-8: Trace Viewer UI Component
 * AC4: Trace detail shows timeline of spans in waterfall view with duration bars
 */
'use client';

import { cn } from '@/lib/utils';
import type { SpanDetail } from '@/hooks/useTraces';

interface WaterfallTimelineProps {
  spans: SpanDetail[];
  totalDuration: number;
  selectedSpanId: string | null;
  onSelectSpan: (spanId: string) => void;
}

/**
 * Format time scale label based on duration
 */
function formatTimeLabel(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

/**
 * Time scale header showing duration markers
 */
function TimeScaleHeader({ totalDuration }: { totalDuration: number }) {
  const markers = [0, 25, 50, 75, 100];

  return (
    <div className="flex h-6 border-b text-xs text-muted-foreground">
      <div className="w-48 flex-shrink-0" />
      <div className="flex-1 relative">
        {markers.map((percent) => (
          <div
            key={percent}
            className="absolute top-0 h-full border-l border-muted"
            style={{ left: `${percent}%` }}
          >
            <span className="absolute top-0 -translate-x-1/2 px-1 bg-background">
              {formatTimeLabel((totalDuration * percent) / 100)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Color classes for different span types
 */
function getSpanColor(spanType: string, status: string): string {
  if (status === 'failed') {
    return 'bg-red-500 dark:bg-red-600';
  }

  const colors: Record<string, string> = {
    llm: 'bg-purple-500 dark:bg-purple-600',
    embedding: 'bg-indigo-500 dark:bg-indigo-600',
    retrieval: 'bg-blue-500 dark:bg-blue-600',
    generation: 'bg-green-500 dark:bg-green-600',
    db: 'bg-amber-500 dark:bg-amber-600',
    external: 'bg-cyan-500 dark:bg-cyan-600',
  };

  return colors[spanType] || 'bg-primary';
}

/**
 * Calculate span position on the timeline
 */
function calculateSpanPosition(
  span: SpanDetail,
  traceStartTime: Date,
  totalDuration: number
) {
  const spanStart = new Date(span.started_at);
  const relativeStartMs = spanStart.getTime() - traceStartTime.getTime();
  const startPercent = (relativeStartMs / totalDuration) * 100;
  const widthPercent = ((span.duration_ms || 1) / totalDuration) * 100;

  return {
    left: `${Math.max(0, startPercent)}%`,
    width: `${Math.max(widthPercent, 0.5)}%`, // Minimum 0.5% width for visibility
  };
}

/**
 * Single span row in the waterfall
 */
function SpanRow({
  span,
  traceStartTime,
  totalDuration,
  depth,
  isSelected,
  onClick,
}: {
  span: SpanDetail;
  traceStartTime: Date;
  totalDuration: number;
  depth: number;
  isSelected: boolean;
  onClick: () => void;
}) {
  const barStyle = calculateSpanPosition(span, traceStartTime, totalDuration);

  return (
    <div
      className={cn(
        'flex items-center h-8 cursor-pointer hover:bg-muted/50 transition-colors',
        isSelected && 'bg-muted'
      )}
      onClick={onClick}
      data-testid={`span-row-${span.span_id}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      {/* Span name with indentation for nesting */}
      <div
        className="w-48 flex-shrink-0 truncate text-sm px-2"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        title={span.name}
      >
        {span.name}
      </div>

      {/* Timeline bar */}
      <div className="flex-1 relative h-6 rounded">
        <div
          className={cn(
            'absolute h-4 top-1 rounded-sm transition-all',
            getSpanColor(span.span_type, span.status),
            isSelected && 'ring-2 ring-ring'
          )}
          style={barStyle}
          title={`${span.name}: ${span.duration_ms || 0}ms`}
        />
      </div>

      {/* Duration label */}
      <div className="w-20 flex-shrink-0 text-right text-xs text-muted-foreground px-2">
        {span.duration_ms !== null ? formatTimeLabel(span.duration_ms) : '-'}
      </div>
    </div>
  );
}

/**
 * Build span tree structure from flat list
 */
function buildSpanTree(spans: SpanDetail[]): Map<string | null, SpanDetail[]> {
  const tree = new Map<string | null, SpanDetail[]>();

  spans.forEach((span) => {
    const parentId = span.parent_span_id;
    const existing = tree.get(parentId) || [];
    tree.set(parentId, [...existing, span]);
  });

  return tree;
}

/**
 * Flatten span tree with depth information for rendering
 */
function flattenSpanTree(
  tree: Map<string | null, SpanDetail[]>,
  parentId: string | null = null,
  depth: number = 0
): Array<{ span: SpanDetail; depth: number }> {
  const result: Array<{ span: SpanDetail; depth: number }> = [];
  const children = tree.get(parentId) || [];

  children.forEach((span) => {
    result.push({ span, depth });
    result.push(...flattenSpanTree(tree, span.span_id, depth + 1));
  });

  return result;
}

export function WaterfallTimeline({
  spans,
  totalDuration,
  selectedSpanId,
  onSelectSpan,
}: WaterfallTimelineProps) {
  if (spans.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        No spans found for this trace
      </div>
    );
  }

  // Get trace start time from first span
  const traceStartTime = new Date(
    Math.min(...spans.map((s) => new Date(s.started_at).getTime()))
  );

  // Build hierarchical span tree and flatten for rendering
  const spanTree = buildSpanTree(spans);
  const flattenedSpans = flattenSpanTree(spanTree);

  return (
    <div className="border rounded-lg overflow-hidden">
      <TimeScaleHeader totalDuration={totalDuration} />
      <div className="divide-y">
        {flattenedSpans.map(({ span, depth }) => (
          <SpanRow
            key={span.span_id}
            span={span}
            traceStartTime={traceStartTime}
            totalDuration={totalDuration}
            depth={depth}
            isSelected={selectedSpanId === span.span_id}
            onClick={() => onSelectSpan(span.span_id)}
          />
        ))}
      </div>
    </div>
  );
}
