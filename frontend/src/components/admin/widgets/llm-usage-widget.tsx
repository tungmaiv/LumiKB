/**
 * LLM Usage Widget for observability dashboard.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Displays:
 * - Total LLM requests
 * - Total tokens (input + output)
 * - Average latency
 * - Breakdown by model
 */

'use client';

import { AlertCircle, Cpu, RefreshCw } from 'lucide-react';
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
import type { LLMUsageStats } from '@/hooks/useObservabilityStats';

interface LLMUsageWidgetProps {
  data?: LLMUsageStats;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  trend?: number[];
}

/**
 * Format large numbers with K/M suffix.
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * Format latency in milliseconds.
 */
function formatLatency(ms: number | null): string {
  if (ms === null) return 'N/A';
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  return `${Math.round(ms)}ms`;
}

export function LLMUsageWidget({ data, isLoading, error, onRetry, trend }: LLMUsageWidgetProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push('/admin/observability/traces');
  };

  if (isLoading) {
    return <LLMUsageWidgetSkeleton />;
  }

  if (error) {
    return <LLMUsageWidgetError error={error} onRetry={onRetry} />;
  }

  const totalTokens = (data?.total_input_tokens ?? 0) + (data?.total_output_tokens ?? 0);
  const chartData = trend?.map((value, index) => ({ index, value })) ?? [];

  return (
    <Card
      className="cursor-pointer hover:bg-accent transition-colors"
      onClick={handleClick}
      data-testid="llm-usage-widget"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">LLM Usage</CardTitle>
        <Cpu className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold" data-testid="total-tokens">
          {formatNumber(totalTokens)} tokens
        </div>
        <CardDescription className="text-xs">
          {formatNumber(data?.total_requests ?? 0)} requests &middot;{' '}
          {formatLatency(data?.avg_latency_ms ?? null)} avg
        </CardDescription>

        {/* Model breakdown */}
        {data?.by_model && Object.keys(data.by_model).length > 0 && (
          <div className="mt-2 space-y-1">
            {Object.entries(data.by_model).slice(0, 3).map(([model, stats]) => (
              <div key={model} className="flex justify-between text-xs text-muted-foreground">
                <span className="truncate max-w-[120px]">{model}</span>
                <span>{formatNumber(stats.input_tokens + stats.output_tokens)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Sparkline trend */}
        {chartData.length > 0 && (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={chartData}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
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

function LLMUsageWidgetSkeleton() {
  return (
    <Card data-testid="llm-usage-widget-skeleton">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-40 mb-4" />
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  );
}

interface LLMUsageWidgetErrorProps {
  error: Error;
  onRetry?: () => void;
}

function LLMUsageWidgetError({ error, onRetry }: LLMUsageWidgetErrorProps) {
  return (
    <Card data-testid="llm-usage-widget-error">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">LLM Usage</CardTitle>
        <AlertCircle className="h-4 w-4 text-destructive" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <p className="text-sm text-muted-foreground mb-2">
            Failed to load LLM usage data
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
              data-testid="llm-usage-widget-retry"
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
