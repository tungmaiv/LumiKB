/**
 * Queue Status Dashboard Page (Operations section)
 *
 * Displays real-time status for all Celery queues:
 * - Dynamically discovers active queues (currently: default, document_processing)
 * - Queue metrics: pending tasks, active tasks, worker count
 * - Auto-refreshes every 10 seconds via React Query
 * - Click queue card to view active task details
 *
 * Story 7.11: Navigation Restructure - moved to /operations/queue
 * Available to Operators (level 2+)
 */

'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Activity } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { QueueStatusCard } from '@/components/admin/queue-status-card';
import { TaskListModal } from '@/components/admin/task-list-modal';
import { useQueueStatus } from '@/hooks/useQueueStatus';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

export default function OperationsQueuePage() {
  const { data: queues, isLoading, error, dataUpdatedAt } = useQueueStatus();
  const [selectedQueue, setSelectedQueue] = useState<string | null>(null);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Queue Status</h1>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Queue Status</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load queue status'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const lastUpdated = dataUpdatedAt
    ? formatDistanceToNow(dataUpdatedAt, { addSuffix: true })
    : 'never';

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <Activity className="h-8 w-8" />
            <h1 className="text-2xl font-bold">Queue Status</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time monitoring of background task queues
          </p>
          <p className="text-xs text-muted-foreground mt-1">Last updated: {lastUpdated}</p>
        </div>

        {queues && queues.length === 0 && (
          <div className="rounded-lg border border-muted bg-muted/10 p-4">
            <p className="text-sm text-muted-foreground">
              No active queues found. Ensure Celery workers are running.
            </p>
          </div>
        )}

        {queues && queues.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {queues.map((queue) => (
              <QueueStatusCard
                key={queue.queue_name}
                queue={queue}
                onClick={() => setSelectedQueue(queue.queue_name)}
              />
            ))}
          </div>
        )}

        {selectedQueue && (
          <TaskListModal
            queueName={selectedQueue}
            open={!!selectedQueue}
            onClose={() => setSelectedQueue(null)}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
