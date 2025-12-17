/**
 * Timeline Step Component
 *
 * Story 9-10: Document Timeline UI
 * AC3: Status icon for each step
 * AC4: Step duration in human-readable format
 * AC7: Retry count visible for failed steps
 */
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { StatusIcon, type StepStatus } from './status-icon';
import { StepDetail } from './step-detail';
import { formatDuration } from '@/lib/utils';

export interface DocumentEventItem {
  id: string;
  trace_id: string;
  step_name: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  metrics: Record<string, unknown> | null;
  error_message: string | null;
  retry_count?: number;
}

interface TimelineStepProps {
  event: DocumentEventItem;
  isLast: boolean;
}

const STEP_LABELS: Record<string, string> = {
  upload: 'Upload',
  parse: 'Parse',
  chunk: 'Chunk',
  embed: 'Embed',
  index: 'Index',
};

export function TimelineStep({ event, isLast }: TimelineStepProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const stepLabel = STEP_LABELS[event.step_name] || event.step_name;
  const hasRetries = event.retry_count && event.retry_count > 0;

  return (
    <div className="relative" data-testid={`timeline-step-${event.step_name}`}>
      {/* Status icon positioned on the connector line */}
      <div className="absolute -left-6 mt-1">
        <StatusIcon status={event.status as StepStatus} />
      </div>

      {/* Connector line extension for non-last items */}
      {!isLast && <div className="absolute -left-[11px] top-6 bottom-0 w-0.5 bg-border" />}

      {/* Step content */}
      <div
        className="cursor-pointer rounded-lg border p-3 hover:bg-muted/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded(!isExpanded);
          }
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" aria-hidden="true" />
            ) : (
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="font-medium">{stepLabel}</span>
            {hasRetries && (
              <span
                className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-700 dark:text-amber-400"
                data-testid="retry-badge"
              >
                Retry {event.retry_count}
              </span>
            )}
          </div>
          <span className="text-sm text-muted-foreground">{formatDuration(event.duration_ms)}</span>
        </div>

        {/* Expanded detail */}
        {isExpanded && (
          <StepDetail
            stepName={event.step_name}
            status={event.status}
            metrics={event.metrics as Record<string, unknown> | null}
            errorMessage={event.error_message}
          />
        )}
      </div>
    </div>
  );
}
