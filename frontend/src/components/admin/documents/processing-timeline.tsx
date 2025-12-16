/**
 * Processing Timeline Component
 *
 * Story 9-10: Document Timeline UI
 * AC2: Timeline visualization shows all processing steps in vertical layout
 * AC8: Total processing time summarized at top of timeline
 */
'use client';

import { AlertCircle } from 'lucide-react';

import { TimelineStep } from './timeline-step';
import { useDocumentTimeline } from '@/hooks/useDocumentTimeline';
import { formatDuration } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface ProcessingTimelineProps {
  documentId: string;
}

export function ProcessingTimeline({ documentId }: ProcessingTimelineProps) {
  const { data, isLoading, error } = useDocumentTimeline(documentId);

  if (isLoading) {
    return <TimelineSkeleton />;
  }

  if (error) {
    return <TimelineError error={error} />;
  }

  if (!data || data.events.length === 0) {
    return <TimelineEmpty />;
  }

  const { events, total_duration_ms } = data;

  return (
    <div className="space-y-4" data-testid="processing-timeline">
      {/* Summary header */}
      <div className="flex items-center justify-between border-b pb-2">
        <h3 className="font-medium">Processing Timeline</h3>
        <span className="text-sm text-muted-foreground" data-testid="total-duration">
          Total: {formatDuration(total_duration_ms)}
        </span>
      </div>

      {/* Timeline steps */}
      <div className="relative pl-6">
        {/* Vertical connector line */}
        <div className="absolute left-[9px] top-0 bottom-6 w-0.5 bg-border" aria-hidden="true" />

        <div className="space-y-4">
          {events.map((event, index) => (
            <TimelineStep
              key={event.id}
              event={event}
              isLast={index === events.length - 1}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function TimelineSkeleton() {
  return (
    <div className="space-y-4" data-testid="timeline-skeleton">
      <div className="flex items-center justify-between border-b pb-2">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-20" />
      </div>
      <div className="pl-6 space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-5 w-5 rounded-full" />
            <div className="flex-1 border rounded-lg p-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface TimelineErrorProps {
  error: Error;
}

function TimelineError({ error }: TimelineErrorProps) {
  return (
    <div
      className="flex flex-col items-center justify-center p-6 text-center"
      data-testid="timeline-error"
    >
      <AlertCircle className="h-10 w-10 text-destructive mb-2" />
      <h3 className="font-medium text-destructive mb-1">Failed to load timeline</h3>
      <p className="text-sm text-muted-foreground">{error.message}</p>
    </div>
  );
}

function TimelineEmpty() {
  return (
    <div
      className="flex flex-col items-center justify-center p-6 text-center"
      data-testid="timeline-empty"
    >
      <p className="text-muted-foreground">No processing events found for this document</p>
    </div>
  );
}

export { TimelineSkeleton };
