/**
 * Processing details modal component
 * Story 5-23 (AC-5.23.3): Shows step-by-step processing details with timing
 */

"use client";

import {
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  XCircle,
  AlertCircle,
  SkipForward,
  Timer,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useDocumentProcessingDetails } from "@/hooks/useDocumentProcessingDetails";
import type { ProcessingStepInfo, StepStatus } from "@/types/processing";
import {
  STEP_LABELS,
  DOC_STATUS_LABELS,
  PROCESSING_STEPS_ORDER,
} from "@/types/processing";

export interface ProcessingDetailsModalProps {
  kbId: string;
  docId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Get icon for step status
 */
function getStepStatusIcon(status: StepStatus) {
  switch (status) {
    case "done":
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    case "in_progress":
      return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
    case "error":
      return <XCircle className="h-5 w-5 text-red-600" />;
    case "skipped":
      return <SkipForward className="h-5 w-5 text-gray-400" />;
    case "pending":
    default:
      return <Clock className="h-5 w-5 text-gray-400" />;
  }
}

/**
 * Format duration in milliseconds to human-readable string
 */
function formatDuration(ms: number | null): string {
  if (ms === null) return "-";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const mins = Math.floor(ms / 60000);
  const secs = Math.round((ms % 60000) / 1000);
  return `${mins}m ${secs}s`;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(dateStr: string | null): string {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * Format file size for display
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Convert steps array to a map for easier lookup
 */
function stepsToMap(
  steps: ProcessingStepInfo[]
): Map<string, ProcessingStepInfo> {
  const map = new Map<string, ProcessingStepInfo>();
  for (const step of steps) {
    map.set(step.step, step);
  }
  return map;
}

/**
 * Calculate overall progress percentage
 */
function calculateOverallProgress(steps: ProcessingStepInfo[]): number {
  let completed = 0;
  const total = PROCESSING_STEPS_ORDER.length;
  const stepsMap = stepsToMap(steps);

  for (const step of PROCESSING_STEPS_ORDER) {
    const stepInfo = stepsMap.get(step);
    if (stepInfo?.status === "done" || stepInfo?.status === "skipped") {
      completed++;
    } else if (stepInfo?.status === "in_progress") {
      completed += 0.5;
    }
  }

  return Math.round((completed / total) * 100);
}

export function ProcessingDetailsModal({
  kbId,
  docId,
  isOpen,
  onClose,
}: ProcessingDetailsModalProps) {
  const { data, isLoading, error } = useDocumentProcessingDetails({
    kbId,
    docId: docId || "",
    enabled: isOpen && !!docId,
  });

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Processing Details
          </DialogTitle>
          <DialogDescription>
            View step-by-step processing status and timing information
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-12 text-destructive">
            <AlertCircle className="h-12 w-12 mb-4" />
            <p className="text-lg font-medium">Error loading details</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Document Info Header */}
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h3
                    className="font-medium break-words"
                    title={data.original_filename}
                  >
                    {data.original_filename}
                  </h3>
                  <div className="mt-1 flex flex-wrap gap-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Badge variant="outline" className="font-mono text-xs">
                        {data.file_type.toUpperCase()}
                      </Badge>
                    </span>
                    <span>{formatFileSize(data.file_size)}</span>
                    {data.chunk_count !== null && (
                      <span>{data.chunk_count} chunks</span>
                    )}
                  </div>
                </div>
                <Badge
                  variant={
                    data.status.toLowerCase() === "ready"
                      ? "default"
                      : data.status.toLowerCase() === "failed"
                        ? "destructive"
                        : "secondary"
                  }
                  className={
                    data.status.toLowerCase() === "ready" ? "bg-green-600" : undefined
                  }
                >
                  {DOC_STATUS_LABELS[data.status.toLowerCase() as keyof typeof DOC_STATUS_LABELS] || data.status}
                </Badge>
              </div>

              {/* Overall Progress */}
              <div className="mt-4 space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Overall Progress</span>
                  <span className="font-medium">
                    {calculateOverallProgress(data.steps)}%
                  </span>
                </div>
                <Progress
                  value={calculateOverallProgress(data.steps)}
                  className="h-2"
                />
              </div>

              {/* Total Duration */}
              {data.total_duration_ms !== null && (
                <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                  <Timer className="h-4 w-4" />
                  <span>Total processing time: {formatDuration(data.total_duration_ms)}</span>
                </div>
              )}
            </div>

            {/* Processing Steps Timeline */}
            <div className="space-y-1">
              <h4 className="font-medium">Processing Steps</h4>
              <div className="rounded-lg border">
                {(() => {
                  const stepsMap = stepsToMap(data.steps);
                  return PROCESSING_STEPS_ORDER.map((step, index) => {
                    const stepInfo = stepsMap.get(step);
                    const isLast = index === PROCESSING_STEPS_ORDER.length - 1;

                    return (
                      <div
                        key={step}
                        className={`flex items-start gap-4 p-4 ${
                          !isLast ? "border-b" : ""
                        }`}
                      >
                        {/* Status Icon */}
                        <div className="flex-shrink-0 mt-0.5">
                          {getStepStatusIcon(stepInfo?.status || "pending")}
                        </div>

                        {/* Step Details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium">
                              {STEP_LABELS[step]}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-xs ${
                                stepInfo?.status === "done"
                                  ? "border-green-600 text-green-600"
                                  : stepInfo?.status === "in_progress"
                                    ? "border-blue-600 text-blue-600"
                                    : stepInfo?.status === "error"
                                      ? "border-red-600 text-red-600"
                                      : ""
                              }`}
                            >
                              {stepInfo?.status || "pending"}
                            </Badge>
                          </div>

                          {/* Timing Info */}
                          {stepInfo && (stepInfo.started_at || stepInfo.duration_ms !== null) && (
                            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                              {stepInfo.started_at && (
                                <span>
                                  Started: {formatTimestamp(stepInfo.started_at)}
                                </span>
                              )}
                              {stepInfo.completed_at && (
                                <span>
                                  Completed: {formatTimestamp(stepInfo.completed_at)}
                                </span>
                              )}
                              {stepInfo.duration_ms !== null && (
                                <span className="font-medium">
                                  Duration: {formatDuration(stepInfo.duration_ms)}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Error Message */}
                          {stepInfo?.error && (
                            <div className="mt-2 rounded bg-red-50 p-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                              <span className="font-medium">Error: </span>
                              {stepInfo.error}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>

            {/* Timestamps */}
            <div className="rounded-lg border bg-muted/30 p-4">
              <h4 className="font-medium mb-2">Timestamps</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Created:</span>
                  <span className="ml-2">
                    {new Date(data.created_at).toLocaleString()}
                  </span>
                </div>
                {data.processing_completed_at && (
                  <div>
                    <span className="text-muted-foreground">Completed:</span>
                    <span className="ml-2">
                      {new Date(data.processing_completed_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
