/**
 * Model Health Indicator Component
 * Story 7-2: Centralized LLM Configuration (AC-7.2.4)
 *
 * Displays health status for configured LLM models including:
 * - Connection status (healthy/unhealthy)
 * - Latency measurements
 * - Error messages when applicable
 */

'use client';

import { useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Zap,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LLMHealthResponse, ModelHealthStatus } from '@/types/llm-config';
import { cn } from '@/lib/utils';

interface ModelHealthIndicatorProps {
  health: LLMHealthResponse | undefined;
  isLoading: boolean;
  onRefresh: () => Promise<void>;
  isRefreshing: boolean;
}

interface SingleModelHealthProps {
  title: string;
  status: ModelHealthStatus | null;
  icon: React.ReactNode;
}

function SingleModelHealth({ title, status, icon }: SingleModelHealthProps) {
  if (!status) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-dashed p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
          {icon}
        </div>
        <div>
          <p className="font-medium">{title}</p>
          <p className="text-sm text-muted-foreground">Not configured</p>
        </div>
      </div>
    );
  }

  const isHealthy = status.is_healthy;
  const StatusIcon = isHealthy ? CheckCircle2 : AlertCircle;
  const statusColor = isHealthy ? 'text-green-500' : 'text-destructive';
  const bgColor = isHealthy ? 'bg-green-500/10' : 'bg-destructive/10';

  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border p-4',
        isHealthy ? 'border-green-500/20' : 'border-destructive/20'
      )}
    >
      <div className="flex items-center gap-3">
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-full', bgColor)}>
          {icon}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium">{title}</p>
            <StatusIcon className={cn('h-4 w-4', statusColor)} />
          </div>
          <p className="text-sm text-muted-foreground">{status.model_name}</p>
        </div>
      </div>

      <div className="flex flex-col items-end gap-1">
        {status.latency_ms !== null && (
          <div className="flex items-center gap-1 text-sm">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <span className={cn(
              status.latency_ms < 500 ? 'text-green-600' :
              status.latency_ms < 1000 ? 'text-yellow-600' : 'text-orange-600'
            )}>
              {status.latency_ms}ms
            </span>
          </div>
        )}
        {status.error_message && (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="cursor-help text-xs text-destructive">
                Error details
              </span>
            </TooltipTrigger>
            <TooltipContent side="left" className="max-w-sm">
              <p className="text-sm">{status.error_message}</p>
            </TooltipContent>
          </Tooltip>
        )}
        <p className="text-xs text-muted-foreground">
          Checked: {formatLastChecked(status.last_checked)}
        </p>
      </div>
    </div>
  );
}

function formatLastChecked(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return date.toLocaleTimeString();
}

export function ModelHealthIndicator({
  health,
  isLoading,
  onRefresh,
  isRefreshing,
}: ModelHealthIndicatorProps) {
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const handleRefresh = async () => {
    setRefreshError(null);
    try {
      await onRefresh();
    } catch (error) {
      setRefreshError(error instanceof Error ? error.message : 'Failed to refresh health status');
    }
  };

  const overallHealthy = health?.overall_healthy ?? false;
  const hasHealth = health?.embedding_health || health?.generation_health;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Model Health Status</CardTitle>
            {hasHealth && (
              <span
                className={cn(
                  'rounded-full px-2 py-0.5 text-xs font-medium',
                  overallHealthy
                    ? 'bg-green-500/10 text-green-600'
                    : 'bg-destructive/10 text-destructive'
                )}
              >
                {overallHealthy ? 'All Healthy' : 'Issues Detected'}
              </span>
            )}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="gap-2"
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
            Test Connection
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && !health ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            Loading health status...
          </div>
        ) : (
          <>
            <SingleModelHealth
              title="Embedding Model"
              status={health?.embedding_health ?? null}
              icon={<Zap className="h-5 w-5 text-blue-500" />}
            />
            <SingleModelHealth
              title="Generation Model"
              status={health?.generation_health ?? null}
              icon={<Activity className="h-5 w-5 text-purple-500" />}
            />
          </>
        )}

        {refreshError && (
          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {refreshError}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
