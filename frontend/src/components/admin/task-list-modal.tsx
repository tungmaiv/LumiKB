/**
 * Modal for displaying active tasks in a specific queue.
 *
 * Story 7-27: Enhanced with:
 * - AC-7.27.1-3: Expandable rows with step breakdown
 * - AC-7.27.4-5: Color-coded status badges with error tooltips
 * - AC-7.27.6-9: Bulk retry functionality
 * - AC-7.27.11-14: Filter tabs (All, Active, Pending, Failed)
 *
 * Tasks sorted by started_at DESC (newest first).
 */

import { useState, useMemo, Fragment } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { useQueueTasks } from '@/hooks/useQueueTasks';
import { useBulkRetry } from '@/hooks/useBulkRetry';
import { StepBreakdown } from './step-breakdown';
import { FilterTabs, type FilterType, type FilterCounts } from './filter-tabs';
import { BulkRetryDialog, BulkRetryButton } from './bulk-retry-dialog';
import type { DocumentStatusFilter } from '@/types/queue';

interface TaskListModalProps {
  queueName: string;
  open: boolean;
  onClose: () => void;
}

// Map UI filter to API document_status filter
function filterToDocumentStatus(filter: FilterType): DocumentStatusFilter {
  switch (filter) {
    case 'active':
      return 'PROCESSING';
    case 'pending':
      return 'PENDING';
    case 'failed':
      return 'FAILED';
    default:
      return 'all';
  }
}

export function TaskListModal({ queueName, open, onClose }: TaskListModalProps) {
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [expandedTaskIds, setExpandedTaskIds] = useState<Set<string>>(new Set());
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const [showRetryDialog, setShowRetryDialog] = useState(false);
  const [retryAll, setRetryAll] = useState(false);

  const documentStatus = filterToDocumentStatus(activeFilter);
  const { data: tasks, isLoading, error, refetch } = useQueueTasks(queueName, documentStatus, open);
  const bulkRetryMutation = useBulkRetry();

  // Calculate filter counts from tasks
  const filterCounts: FilterCounts = useMemo(() => {
    if (!tasks) return { all: 0, active: 0, pending: 0, failed: 0 };

    return {
      all: tasks.length,
      active: tasks.filter((t) => t.document_status === 'PROCESSING').length,
      pending: tasks.filter((t) => t.document_status === 'PENDING').length,
      failed: tasks.filter((t) => t.document_status === 'FAILED').length,
    };
  }, [tasks]);

  // Get failed document IDs for bulk retry
  const failedDocIds = useMemo(() => {
    if (!tasks) return [];
    return tasks
      .filter((t) => t.document_status === 'FAILED' && t.document_id)
      .map((t) => t.document_id as string);
  }, [tasks]);

  const formatDuration = (durationMs: number | null) => {
    if (!durationMs) return 'N/A';
    const seconds = Math.floor(durationMs / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatStartedAt = (startedAt: string | null) => {
    if (!startedAt) return 'N/A';
    try {
      return formatDistanceToNow(new Date(startedAt), { addSuffix: true });
    } catch {
      return 'Invalid date';
    }
  };

  const toggleTaskExpand = (taskId: string) => {
    setExpandedTaskIds((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  };

  const toggleDocSelection = (docId: string | null) => {
    if (!docId) return;
    setSelectedDocIds((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) {
        next.delete(docId);
      } else {
        next.add(docId);
      }
      return next;
    });
  };

  const handleRetryAll = () => {
    setRetryAll(true);
    setShowRetryDialog(true);
  };

  const handleRetrySelected = () => {
    setRetryAll(false);
    setShowRetryDialog(true);
  };

  const handleConfirmRetry = async () => {
    const request = retryAll
      ? { retry_all_failed: true }
      : { document_ids: Array.from(selectedDocIds) };

    const response = await bulkRetryMutation.mutateAsync(request);

    // Clear selections and refresh
    setSelectedDocIds(new Set());
    refetch();

    return response;
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'PROCESSING':
        return 'default';
      case 'COMPLETED':
        return 'secondary';
      case 'FAILED':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Queue Tasks: {queueName}</DialogTitle>
          <DialogDescription>
            Document processing tasks with step breakdown (sorted by newest first).
          </DialogDescription>
        </DialogHeader>

        {/* Story 7-27: Filter tabs */}
        <FilterTabs
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          counts={filterCounts}
        />

        {/* Story 7-27: Bulk retry controls */}
        {(failedDocIds.length > 0 || selectedDocIds.size > 0) && (
          <div className="mb-4">
            <BulkRetryButton
              failedCount={failedDocIds.length}
              selectedCount={selectedDocIds.size}
              onRetryAll={handleRetryAll}
              onRetrySelected={handleRetrySelected}
              disabled={bulkRetryMutation.isPending}
            />
          </div>
        )}

        {isLoading && (
          <div className="py-8 text-center text-muted-foreground">Loading tasks...</div>
        )}

        {error && (
          <div className="py-8 text-center text-destructive">
            Failed to load tasks. Please try again.
          </div>
        )}

        {!isLoading && !error && tasks && tasks.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            No tasks match the current filter.
          </div>
        )}

        {!isLoading && !error && tasks && tasks.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">{/* Selection checkbox header */}</TableHead>
                <TableHead>Document</TableHead>
                <TableHead>Task</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead className="w-10">Steps</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.map((task) => (
                <Fragment key={task.task_id}>
                  <TableRow data-testid={`task-row-${task.task_id}`}>
                    <TableCell>
                      {task.document_id && task.document_status === 'FAILED' && (
                        <Checkbox
                          checked={selectedDocIds.has(task.document_id)}
                          onCheckedChange={() => toggleDocSelection(task.document_id)}
                          aria-label={`Select ${task.document_name || task.document_id}`}
                          data-testid={`checkbox-${task.document_id}`}
                        />
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {task.document_name ||
                        (task.document_id ? task.document_id.substring(0, 8) + '...' : 'N/A')}
                    </TableCell>
                    <TableCell className="text-sm">{task.task_name.split('.').pop()}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(task.document_status)}>
                        {task.document_status}
                      </Badge>
                      {task.current_step && (
                        <span className="ml-2 text-xs text-muted-foreground">
                          ({task.current_step})
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatStartedAt(task.started_at)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDuration(task.estimated_duration)}
                    </TableCell>
                    <TableCell>
                      {task.processing_steps &&
                        task.processing_steps.length > 0 &&
                        !expandedTaskIds.has(task.task_id) && (
                          <StepBreakdown
                            steps={task.processing_steps}
                            isExpanded={false}
                            onToggleExpand={() => toggleTaskExpand(task.task_id)}
                          />
                        )}
                    </TableCell>
                  </TableRow>
                  {/* Expanded step breakdown row */}
                  {expandedTaskIds.has(task.task_id) && task.processing_steps && (
                    <TableRow>
                      <TableCell colSpan={7} className="bg-gray-50 p-4">
                        <StepBreakdown
                          steps={task.processing_steps}
                          isExpanded={true}
                          onToggleExpand={() => toggleTaskExpand(task.task_id)}
                        />
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              ))}
            </TableBody>
          </Table>
        )}

        {/* Bulk retry confirmation dialog */}
        <BulkRetryDialog
          open={showRetryDialog}
          onClose={() => setShowRetryDialog(false)}
          selectedDocumentIds={Array.from(selectedDocIds)}
          retryAll={retryAll}
          onConfirm={handleConfirmRetry}
          onRetrySuccess={(response) => {
            console.log(`Retry queued: ${response.queued}, failed: ${response.failed}`);
          }}
          onRetryError={(error) => {
            console.error('Bulk retry failed:', error);
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
