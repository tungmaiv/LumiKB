/**
 * Queue monitoring types for Celery background tasks.
 *
 * Provides real-time visibility into:
 * - Active Celery queues (document_processing, default, etc.)
 * - Queue metrics: pending tasks, active tasks, worker count
 * - Worker health: online/offline status based on heartbeat
 * - Task details: task_id, task_name, status, timestamps
 */

export interface WorkerInfo {
  /** Worker ID (e.g., "worker1@localhost") */
  worker_id: string;

  /** Worker status (online if heartbeat <= 60s, offline otherwise) */
  status: "online" | "offline";

  /** Number of active tasks for this worker */
  active_tasks: number;
}

export interface QueueStatus {
  /** Queue name (e.g., "document_processing", "default") */
  queue_name: string;

  /** Number of pending tasks in queue */
  pending_tasks: number;

  /** Number of active tasks in queue */
  active_tasks: number;

  /** Workers assigned to this queue */
  workers: WorkerInfo[];

  /** Queue status (unavailable if Celery broker unreachable) */
  status: "available" | "unavailable";
}

export interface TaskInfo {
  /** Task UUID */
  task_id: string;

  /** Task name (e.g., "app.workers.document_tasks.process_document") */
  task_name: string;

  /** Task status (always "active" for Celery inspect API) */
  status: "active";

  /** Task start time (ISO 8601) */
  started_at: string | null;

  /** Elapsed time in milliseconds */
  estimated_duration: number | null;
}

/**
 * Story 7-27: Extended task info with processing steps
 */
export type StepStatus = 'done' | 'in_progress' | 'pending' | 'error';

export interface StepInfo {
  step: 'parse' | 'chunk' | 'embed' | 'index';
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
}

export interface TaskInfoWithSteps extends TaskInfo {
  /** Associated document UUID */
  document_id: string | null;

  /** Document name for display */
  document_name?: string | null;

  /** Document processing status */
  document_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

  /** Processing steps with timing */
  processing_steps: StepInfo[];

  /** Current step being processed */
  current_step: string | null;

  /** Errors by step */
  step_errors?: Record<string, string>;
}

export type DocumentStatusFilter = 'all' | 'PENDING' | 'PROCESSING' | 'READY' | 'FAILED';

export interface BulkRetryRequest {
  document_ids?: string[];
  retry_all_failed?: boolean;
  kb_id?: string;
}

export interface BulkRetryResponse {
  queued: number;
  failed: number;
  errors: Array<{ document_id: string; error: string }>;
}
