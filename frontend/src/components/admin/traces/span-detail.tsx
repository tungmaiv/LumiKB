/**
 * Span Detail Component
 *
 * Story 9-8: Trace Viewer UI Component
 * AC5: Span details show type-specific metrics
 * AC6: Error spans highlighted in red with error message displayed
 * AC7: LLM spans prominently show model name, token counts, and cost
 */
'use client';

import { format } from 'date-fns';
import {
  AlertCircle,
  Brain,
  Clock,
  Code,
  Database,
  ExternalLink,
  Layers,
  Server,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { SpanDetail as SpanDetailType } from '@/hooks/useTraces';

interface SpanDetailProps {
  span: SpanDetailType;
}

/**
 * Icon for span type
 */
function SpanTypeIcon({ type }: { type: string }) {
  const icons: Record<string, typeof Brain> = {
    llm: Brain,
    embedding: Layers,
    retrieval: Database,
    generation: Code,
    db: Database,
    external: ExternalLink,
    internal: Server,
  };

  const Icon = icons[type] || Server;
  return <Icon className="h-5 w-5" />;
}

/**
 * Status badge with appropriate styling
 */
function SpanStatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
    in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300',
  };

  return <Badge className={cn(variants[status] || variants.completed)}>{status}</Badge>;
}

/**
 * Key-value metric row
 */
function MetricRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number | null | undefined;
  highlight?: boolean;
}) {
  if (value === null || value === undefined) return null;

  return (
    <div className="flex justify-between py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn('font-mono', highlight && 'font-semibold text-primary')}>{value}</span>
    </div>
  );
}

/**
 * LLM-specific metrics component (AC7)
 */
function LLMMetrics({ span }: { span: SpanDetailType }) {
  const metadata = span.metadata as Record<string, unknown> | null;
  const cost = metadata?.cost_usd as number | undefined;

  return (
    <div className="space-y-2">
      <h4 className="font-medium flex items-center gap-2">
        <Brain className="h-4 w-4 text-purple-500" />
        LLM Metrics
      </h4>
      <div className="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
        <MetricRow label="Model" value={span.model} highlight />
        <MetricRow label="Input Tokens" value={span.input_tokens?.toLocaleString()} />
        <MetricRow label="Output Tokens" value={span.output_tokens?.toLocaleString()} />
        {span.input_tokens && span.output_tokens && (
          <MetricRow
            label="Total Tokens"
            value={(span.input_tokens + span.output_tokens).toLocaleString()}
            highlight
          />
        )}
        {cost !== undefined && <MetricRow label="Cost" value={`$${cost.toFixed(4)}`} highlight />}
      </div>
    </div>
  );
}

/**
 * Database-specific metrics
 */
function DBMetrics({ span }: { span: SpanDetailType }) {
  const metadata = span.metadata as Record<string, unknown> | null;
  if (!metadata) return null;

  return (
    <div className="space-y-2">
      <h4 className="font-medium flex items-center gap-2">
        <Database className="h-4 w-4 text-amber-500" />
        Database Metrics
      </h4>
      <div className="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
        <MetricRow label="Operation" value={metadata.operation as string} />
        <MetricRow label="Table" value={metadata.table as string} />
        <MetricRow label="Rows Affected" value={metadata.rows_affected as number} />
        {typeof metadata.query === 'string' && (
          <div className="pt-2">
            <span className="text-muted-foreground text-xs">Query:</span>
            <pre className="mt-1 p-2 bg-background rounded text-xs overflow-x-auto">
              {metadata.query}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * External call metrics
 */
function ExternalMetrics({ span }: { span: SpanDetailType }) {
  const metadata = span.metadata as Record<string, unknown> | null;
  if (!metadata) return null;

  return (
    <div className="space-y-2">
      <h4 className="font-medium flex items-center gap-2">
        <ExternalLink className="h-4 w-4 text-cyan-500" />
        External Call
      </h4>
      <div className="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
        <MetricRow label="URL" value={metadata.url as string} />
        <MetricRow label="Method" value={metadata.method as string} />
        <MetricRow label="Status Code" value={metadata.status_code as number} />
      </div>
    </div>
  );
}

/**
 * Generic metadata display
 */
function GenericMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata);
  if (entries.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="font-medium">Additional Metadata</h4>
      <div className="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
        {entries.slice(0, 10).map(([key, value]) => (
          <MetricRow
            key={key}
            label={key.replace(/_/g, ' ')}
            value={typeof value === 'object' ? JSON.stringify(value) : String(value)}
          />
        ))}
        {entries.length > 10 && (
          <p className="text-xs text-muted-foreground pt-2">+{entries.length - 10} more fields</p>
        )}
      </div>
    </div>
  );
}

/**
 * Error message display (AC6)
 */
function ErrorDisplay({ errorMessage }: { errorMessage: string }) {
  return (
    <div className="rounded-lg border border-destructive bg-destructive/10 p-3">
      <div className="flex items-start gap-2">
        <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-destructive">Error</p>
          <p className="text-sm text-destructive/90 mt-1">{errorMessage}</p>
        </div>
      </div>
    </div>
  );
}

export function SpanDetailCard({ span }: SpanDetailProps) {
  const startTime = new Date(span.started_at);
  const endTime = span.ended_at ? new Date(span.ended_at) : null;

  return (
    <Card
      className={cn(span.status === 'failed' && 'border-destructive')}
      data-testid="span-detail-card"
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SpanTypeIcon type={span.span_type} />
            <CardTitle className="text-lg">{span.name}</CardTitle>
          </div>
          <SpanStatusBadge status={span.status} />
        </div>
        <CardDescription className="flex items-center gap-4">
          <span className="capitalize">{span.span_type}</span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {span.duration_ms !== null ? `${span.duration_ms}ms` : 'In progress'}
          </span>
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error message if failed */}
        {span.status === 'failed' && span.error_message && (
          <ErrorDisplay errorMessage={span.error_message} />
        )}

        {/* Timing information */}
        <div className="space-y-2">
          <h4 className="font-medium">Timing</h4>
          <div className="bg-muted/50 rounded-lg p-3 text-sm space-y-1">
            <MetricRow label="Started" value={format(startTime, 'yyyy-MM-dd HH:mm:ss.SSS')} />
            {endTime && (
              <MetricRow label="Ended" value={format(endTime, 'yyyy-MM-dd HH:mm:ss.SSS')} />
            )}
            <MetricRow
              label="Duration"
              value={span.duration_ms !== null ? `${span.duration_ms}ms` : '-'}
              highlight
            />
          </div>
        </div>

        {/* Type-specific metrics */}
        {span.span_type === 'llm' && <LLMMetrics span={span} />}
        {span.span_type === 'db' && <DBMetrics span={span} />}
        {span.span_type === 'external' && <ExternalMetrics span={span} />}

        {/* Generic metadata for other types */}
        {!['llm', 'db', 'external'].includes(span.span_type) &&
          span.metadata &&
          Object.keys(span.metadata).length > 0 && (
            <GenericMetadata metadata={span.metadata as Record<string, unknown>} />
          )}

        {/* Span IDs for debugging */}
        <div className="pt-2 border-t">
          <details className="text-xs text-muted-foreground">
            <summary className="cursor-pointer hover:text-foreground">Span IDs</summary>
            <div className="mt-2 space-y-1 font-mono">
              <p>Span: {span.span_id}</p>
              {span.parent_span_id && <p>Parent: {span.parent_span_id}</p>}
            </div>
          </details>
        </div>
      </CardContent>
    </Card>
  );
}
