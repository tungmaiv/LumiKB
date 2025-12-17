/**
 * Observability Dashboard with monitoring widgets.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Provides:
 * - 2x2 grid layout for widgets (desktop)
 * - Single column layout (mobile)
 * - Time period selector
 * - Auto-refresh controls
 * - Last updated timestamp
 */

'use client';

import { RefreshCw } from 'lucide-react';
import { useState, useCallback } from 'react';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useObservabilityStats,
  useRefreshObservabilityStats,
  type TimePeriod,
} from '@/hooks/useObservabilityStats';

import {
  LLMUsageWidget,
  ProcessingWidget,
  ChatActivityWidget,
  SystemHealthWidget,
} from './widgets';

interface ObservabilityDashboardProps {
  /** Initial time period selection. Default: 'day' */
  initialPeriod?: TimePeriod;
  /** Auto-refresh interval in milliseconds. Default: 30000 */
  refreshInterval?: number;
}

/**
 * Format timestamp to human-readable relative time.
 */
function formatLastUpdated(timestamp: Date | null): string {
  if (!timestamp) return 'Never';

  const now = new Date();
  const diff = now.getTime() - timestamp.getTime();

  if (diff < 60000) {
    return 'Just now';
  }
  if (diff < 3600000) {
    const mins = Math.floor(diff / 60000);
    return `${mins} minute${mins > 1 ? 's' : ''} ago`;
  }
  return timestamp.toLocaleTimeString();
}

export function ObservabilityDashboard({
  initialPeriod = 'day',
  refreshInterval = 30000,
}: ObservabilityDashboardProps) {
  const [period, setPeriod] = useState<TimePeriod>(initialPeriod);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refreshStats = useRefreshObservabilityStats();

  const { data, isLoading, isFetching, dataUpdatedAt } = useObservabilityStats({
    period,
    refreshInterval,
    enabled: true,
  });

  // Update last updated timestamp when data changes
  if (dataUpdatedAt && (!lastUpdated || dataUpdatedAt > lastUpdated.getTime())) {
    setLastUpdated(new Date(dataUpdatedAt));
  }

  const handleRefresh = useCallback(() => {
    refreshStats(period);
  }, [refreshStats, period]);

  const handlePeriodChange = useCallback((value: string) => {
    setPeriod(value as TimePeriod);
  }, []);

  // Generate mock trend data for sparklines (in production, this would come from API)
  const generateTrend = (base: number, variance: number = 0.2): number[] => {
    return Array.from({ length: 12 }, () => base * (1 + (Math.random() - 0.5) * variance));
  };

  const llmTrend = data
    ? generateTrend(
        (data.llm_usage?.total_input_tokens ?? 0) + (data.llm_usage?.total_output_tokens ?? 0)
      )
    : undefined;

  const processingTrend = data
    ? generateTrend(data.processing_metrics?.total_documents ?? 0)
    : undefined;

  const chatTrend = data ? generateTrend(data.chat_metrics?.total_messages ?? 0) : undefined;

  const healthTrend = data ? generateTrend((1 - (data.error_rate ?? 0)) * 100, 0.05) : undefined;

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Observability</h2>
          <p className="text-sm text-muted-foreground">
            Monitor system health and performance metrics
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Time period selector */}
          <Select value={period} onValueChange={handlePeriodChange}>
            <SelectTrigger className="w-32" data-testid="period-selector">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="hour">Last hour</SelectItem>
              <SelectItem value="day">Last 24h</SelectItem>
              <SelectItem value="week">Last 7 days</SelectItem>
              <SelectItem value="month">Last 30 days</SelectItem>
            </SelectContent>
          </Select>

          {/* Refresh button */}
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isFetching}
            data-testid="refresh-button"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Last updated timestamp */}
      <div className="text-xs text-muted-foreground">
        Last updated: {formatLastUpdated(lastUpdated)}
        {refreshInterval > 0 && (
          <span className="ml-2">(auto-refresh every {refreshInterval / 1000}s)</span>
        )}
      </div>

      {/* Widget grid */}
      <div className="grid gap-4 md:grid-cols-2" data-testid="widget-grid">
        <LLMUsageWidget data={data?.llm_usage} isLoading={isLoading} trend={llmTrend} />
        <ProcessingWidget
          data={data?.processing_metrics}
          isLoading={isLoading}
          trend={processingTrend}
        />
        <ChatActivityWidget data={data?.chat_metrics} isLoading={isLoading} trend={chatTrend} />
        <SystemHealthWidget data={data} isLoading={isLoading} trend={healthTrend} />
      </div>
    </div>
  );
}
