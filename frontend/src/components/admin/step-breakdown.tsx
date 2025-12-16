/**
 * StepBreakdown Component (Story 7-27, AC-7.27.1-3)
 *
 * Expandable task row showing processing step breakdown:
 * - Step name (parse, chunk, embed, index)
 * - Status badge
 * - Started timestamp
 * - Completed timestamp
 * - Duration (with live elapsed time for in_progress)
 */

import { useEffect, useState } from 'react';
import { type StepInfo } from '@/types/queue';
import { StepStatusBadge } from './step-status-badge';

interface StepBreakdownProps {
  steps: StepInfo[];
  isExpanded: boolean;
  onToggleExpand: () => void;
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

function formatDuration(durationMs: number | null): string {
  if (durationMs === null) return '-';
  if (durationMs < 1000) return `${durationMs}ms`;
  return `${(durationMs / 1000).toFixed(1)}s`;
}

function calculateElapsed(startedAt: string | null): number | null {
  if (!startedAt) return null;
  return Date.now() - new Date(startedAt).getTime();
}

export function StepBreakdown({ steps, isExpanded, onToggleExpand }: StepBreakdownProps) {
  const [, setTick] = useState(0);

  // Update elapsed time every second for in_progress steps
  useEffect(() => {
    const hasInProgress = steps.some((s) => s.status === 'in_progress');
    if (!hasInProgress || !isExpanded) return;

    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [steps, isExpanded]);

  if (!isExpanded) {
    return (
      <button
        onClick={onToggleExpand}
        aria-label="Expand step breakdown"
        className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        Show steps
      </button>
    );
  }

  return (
    <div data-testid="step-breakdown" className="mt-2">
      <button
        onClick={onToggleExpand}
        aria-label="Collapse step breakdown"
        className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 mb-2"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
        Hide steps
      </button>
      <table className="min-w-full text-sm border border-gray-200 rounded">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Step</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Status</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Started</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Completed</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Duration</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {steps.map((step) => {
            // Calculate live elapsed time for in_progress steps
            const displayDuration =
              step.status === 'in_progress'
                ? calculateElapsed(step.started_at)
                : step.duration_ms;

            return (
              <tr key={step.step} data-testid={`step-row-${step.step}`}>
                <td className="px-3 py-2 capitalize">{step.step}</td>
                <td className="px-3 py-2" data-testid={`step-status-${step.step}`}>
                  <StepStatusBadge status={step.status} errorMessage={step.error_message} />
                </td>
                <td className="px-3 py-2 text-gray-500">{formatTimestamp(step.started_at)}</td>
                <td className="px-3 py-2 text-gray-500">{formatTimestamp(step.completed_at)}</td>
                <td className="px-3 py-2" data-testid={`step-duration-${step.step}`}>
                  {formatDuration(displayDuration)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
