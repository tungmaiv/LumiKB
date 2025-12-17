/**
 * Chat Activity Widget for observability dashboard.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Displays:
 * - Total messages for period
 * - Total conversations
 * - Average response time
 * - Average tokens per response
 */

'use client';

import { AlertCircle, MessageSquare, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { ChatMetrics } from '@/hooks/useObservabilityStats';

interface ChatActivityWidgetProps {
  data?: ChatMetrics;
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
 * Format duration in milliseconds to human-readable string.
 */
function formatDuration(ms: number | null): string {
  if (ms === null) return 'N/A';
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  return `${Math.round(ms)}ms`;
}

export function ChatActivityWidget({
  data,
  isLoading,
  error,
  onRetry,
  trend,
}: ChatActivityWidgetProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push('/admin/observability/chats');
  };

  if (isLoading) {
    return <ChatActivityWidgetSkeleton />;
  }

  if (error) {
    return <ChatActivityWidgetError error={error} onRetry={onRetry} />;
  }

  const chartData = trend?.map((value, index) => ({ index, value })) ?? [];

  return (
    <Card
      className="cursor-pointer hover:bg-accent transition-colors"
      onClick={handleClick}
      data-testid="chat-activity-widget"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Chat Activity</CardTitle>
        <MessageSquare className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold" data-testid="message-count">
          {formatNumber(data?.total_messages ?? 0)} messages
        </div>
        <CardDescription className="text-xs">
          {data?.total_conversations ?? 0} conversations &middot;{' '}
          {formatDuration(data?.avg_response_time_ms ?? null)} avg
        </CardDescription>

        {/* Metrics breakdown */}
        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Conversations</span>
            <span>{data?.total_conversations ?? 0}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Avg response time</span>
            <span>{formatDuration(data?.avg_response_time_ms ?? null)}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Avg tokens/response</span>
            <span>{data?.avg_tokens_per_response?.toFixed(0) ?? 'N/A'}</span>
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
                  stroke="#8b5cf6"
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

function ChatActivityWidgetSkeleton() {
  return (
    <Card data-testid="chat-activity-widget-skeleton">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-44 mb-4" />
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

interface ChatActivityWidgetErrorProps {
  error: Error;
  onRetry?: () => void;
}

function ChatActivityWidgetError({ error, onRetry }: ChatActivityWidgetErrorProps) {
  return (
    <Card data-testid="chat-activity-widget-error">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Chat Activity</CardTitle>
        <AlertCircle className="h-4 w-4 text-destructive" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <p className="text-sm text-muted-foreground mb-2">Failed to load chat activity data</p>
          <p className="text-xs text-destructive mb-3 max-w-[200px] truncate">{error.message}</p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRetry();
              }}
              data-testid="chat-activity-widget-retry"
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
