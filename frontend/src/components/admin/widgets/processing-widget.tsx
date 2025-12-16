/**
 * Processing Pipeline Widget for observability dashboard.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Displays:
 * - Documents processed count
 * - Average processing time
 * - Error rate percentage
 * - Success/failure breakdown
 */

'use client';

import { AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { ProcessingMetrics } from '@/hooks/useObservabilityStats';

interface ProcessingWidgetProps {
  data?: ProcessingMetrics;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  trend?: number[];
}

/**
 * Format duration in milliseconds to human-readable string.
 */
function formatDuration(ms: number | null): string {
  if (ms === null) return 'N/A';
  if (ms >= 60000) {
    return `${(ms / 60000).toFixed(1)}m`;
  }
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  return `${Math.round(ms)}ms`;
}

/**
 * Format percentage with one decimal place.
 */
function formatPercentage(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function ProcessingWidget({ data, isLoading, error, onRetry, trend }: ProcessingWidgetProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push('/admin/observability/documents');
  };

  if (isLoading) {
    return <ProcessingWidgetSkeleton />;
  }

  if (error) {
    return <ProcessingWidgetError error={error} onRetry={onRetry} />;
  }

  const total = (data?.success_count ?? 0) + (data?.failure_count ?? 0);
  const errorRate = total > 0 ? (data?.failure_count ?? 0) / total : 0;
  const chartData = trend?.map((value, index) => ({ index, value })) ?? [];

  return (
    <Card
      className="cursor-pointer hover:bg-accent transition-colors"
      onClick={handleClick}
      data-testid="processing-widget"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Processing Pipeline</CardTitle>
        <FileText className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold" data-testid="documents-processed">
          {data?.total_documents ?? 0} docs
        </div>
        <CardDescription className="text-xs">
          {formatDuration(data?.avg_processing_time_ms ?? null)} avg &middot;{' '}
          <span className={errorRate > 0.1 ? 'text-destructive' : ''}>
            {formatPercentage(errorRate)} errors
          </span>
        </CardDescription>

        {/* Success/Failure breakdown */}
        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span className="text-green-600">Successful</span>
            <span>{data?.success_count ?? 0}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span className="text-red-600">Failed</span>
            <span>{data?.failure_count ?? 0}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Total chunks</span>
            <span>{data?.total_chunks ?? 0}</span>
          </div>
        </div>

        {/* Sparkline trend */}
        {chartData.length > 0 && (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={chartData}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ProcessingWidgetSkeleton() {
  return (
    <Card data-testid="processing-widget-skeleton">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-24 mb-2" />
        <Skeleton className="h-3 w-36 mb-4" />
        <div className="space-y-1">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
        </div>
        <Skeleton className="h-10 w-full mt-4" />
      </CardContent>
    </Card>
  );
}

interface ProcessingWidgetErrorProps {
  error: Error;
  onRetry?: () => void;
}

function ProcessingWidgetError({ error, onRetry }: ProcessingWidgetErrorProps) {
  return (
    <Card data-testid="processing-widget-error">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Processing Pipeline</CardTitle>
        <AlertCircle className="h-4 w-4 text-destructive" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <p className="text-sm text-muted-foreground mb-2">
            Failed to load processing data
          </p>
          <p className="text-xs text-destructive mb-3 max-w-[200px] truncate">
            {error.message}
          </p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRetry();
              }}
              data-testid="processing-widget-retry"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
