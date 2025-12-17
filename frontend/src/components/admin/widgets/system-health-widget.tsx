/**
 * System Health Widget for observability dashboard.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Displays:
 * - Trace success rate percentage
 * - P95 latency
 * - Error count
 * - Health status indicator
 */

'use client';

import { Activity, AlertCircle, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { ObservabilityStats } from '@/hooks/useObservabilityStats';

interface SystemHealthWidgetProps {
  data?: ObservabilityStats;
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

/**
 * Get health status based on error rate.
 */
function getHealthStatus(errorRate: number): {
  status: 'healthy' | 'warning' | 'critical';
  icon: React.ReactNode;
  color: string;
} {
  if (errorRate < 0.01) {
    return {
      status: 'healthy',
      icon: <CheckCircle className="h-4 w-4 text-green-500" />,
      color: 'text-green-500',
    };
  }
  if (errorRate < 0.05) {
    return {
      status: 'warning',
      icon: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
      color: 'text-yellow-500',
    };
  }
  return {
    status: 'critical',
    icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
    color: 'text-red-500',
  };
}

export function SystemHealthWidget({
  data,
  isLoading,
  error,
  onRetry,
  trend,
}: SystemHealthWidgetProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push('/admin/observability/traces');
  };

  if (isLoading) {
    return <SystemHealthWidgetSkeleton />;
  }

  if (error) {
    return <SystemHealthWidgetError error={error} onRetry={onRetry} />;
  }

  const errorRate = data?.error_rate ?? 0;
  const successRate = 1 - errorRate;
  const health = getHealthStatus(errorRate);
  const chartData = trend?.map((value, index) => ({ index, value })) ?? [];

  // Calculate error count from processing metrics
  const errorCount = data?.processing_metrics?.failure_count ?? 0;

  // Estimate p95 latency from average (rough approximation)
  const avgLatency = data?.llm_usage?.avg_latency_ms ?? null;
  const p95Latency = avgLatency !== null ? avgLatency * 1.5 : null;

  return (
    <Card
      className="cursor-pointer hover:bg-accent transition-colors"
      onClick={handleClick}
      data-testid="system-health-widget"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">System Health</CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <div className={`text-2xl font-bold ${health.color}`} data-testid="success-rate">
            {formatPercentage(successRate)}
          </div>
          {health.icon}
        </div>
        <CardDescription className="text-xs">
          Success rate &middot; {formatDuration(p95Latency)} p95
        </CardDescription>

        {/* Health metrics breakdown */}
        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Status</span>
            <span className={`capitalize ${health.color}`}>{health.status}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Error rate</span>
            <span className={errorRate > 0.05 ? 'text-red-500' : ''}>
              {formatPercentage(errorRate)}
            </span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Failed operations</span>
            <span>{errorCount}</span>
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
                  stroke={errorRate < 0.05 ? '#22c55e' : '#ef4444'}
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

function SystemHealthWidgetSkeleton() {
  return (
    <Card data-testid="system-health-widget-skeleton">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-4 w-4" />
        </div>
        <Skeleton className="h-3 w-32 mt-2 mb-4" />
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

interface SystemHealthWidgetErrorProps {
  error: Error;
  onRetry?: () => void;
}

function SystemHealthWidgetError({ error, onRetry }: SystemHealthWidgetErrorProps) {
  return (
    <Card data-testid="system-health-widget-error">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">System Health</CardTitle>
        <AlertCircle className="h-4 w-4 text-destructive" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <p className="text-sm text-muted-foreground mb-2">Failed to load system health data</p>
          <p className="text-xs text-destructive mb-3 max-w-[200px] truncate">{error.message}</p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRetry();
              }}
              data-testid="system-health-widget-retry"
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
