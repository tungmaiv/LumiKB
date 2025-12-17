/**
 * Queue Status Factory
 * Story 5-4 Automation: Reusable mock data for queue monitoring tests
 *
 * Provides factory functions to generate consistent mock queue status
 * data for E2E and component tests.
 */

export interface WorkerInfo {
  worker_id: string;
  status: 'online' | 'offline';
  active_tasks: number;
}

export interface QueueStatus {
  queue_name: string;
  pending_tasks: number;
  active_tasks: number;
  workers: WorkerInfo[];
  status: 'available' | 'unavailable';
}

export interface TaskInfo {
  task_id: string;
  task_name: string;
  status: 'active';
  started_at: string | null;
  estimated_duration: number | null;
}

/**
 * Create default queue status with realistic data
 */
export function createQueueStatus(
  queueName: string,
  overrides?: Partial<QueueStatus>
): QueueStatus {
  const defaults: QueueStatus = {
    queue_name: queueName,
    pending_tasks: 5,
    active_tasks: 2,
    workers: [createWorker(`worker-${queueName}-1`, 'online')],
    status: 'available',
  };

  return { ...defaults, ...overrides };
}

/**
 * Create worker info with default data
 */
export function createWorker(
  workerId: string,
  status: 'online' | 'offline' = 'online',
  overrides?: Partial<WorkerInfo>
): WorkerInfo {
  const defaults: WorkerInfo = {
    worker_id: workerId,
    status,
    active_tasks: status === 'online' ? 2 : 0,
  };

  return { ...defaults, ...overrides };
}

/**
 * Create task info with default data
 */
export function createTask(
  taskId: string,
  status: TaskInfo['status'] = 'active',
  overrides?: Partial<TaskInfo>
): TaskInfo {
  const defaults: TaskInfo = {
    task_id: taskId,
    task_name: 'app.workers.document_tasks.process_document',
    status,
    started_at: new Date().toISOString(),
    estimated_duration: 3500,
  };

  return { ...defaults, ...overrides };
}

/**
 * Create all 3 default queues (document_processing, embedding_generation, export_generation)
 */
export function createAllQueues(overrides?: {
  documentProcessing?: Partial<QueueStatus>;
  embeddingGeneration?: Partial<QueueStatus>;
  exportGeneration?: Partial<QueueStatus>;
}): QueueStatus[] {
  return [
    createQueueStatus('document_processing', {
      pending_tasks: 10,
      active_tasks: 3,
      workers: [createWorker('worker-doc-1', 'online'), createWorker('worker-doc-2', 'online')],
      ...overrides?.documentProcessing,
    }),
    createQueueStatus('embedding_generation', {
      pending_tasks: 5,
      active_tasks: 1,
      workers: [createWorker('worker-embed-1', 'online')],
      ...overrides?.embeddingGeneration,
    }),
    createQueueStatus('export_generation', {
      pending_tasks: 2,
      active_tasks: 0,
      workers: [createWorker('worker-export-1', 'online')],
      ...overrides?.exportGeneration,
    }),
  ];
}

/**
 * Create queue status with no workers (warning state)
 */
export function createQueueWithNoWorkers(queueName: string = 'document_processing'): QueueStatus {
  return createQueueStatus(queueName, {
    pending_tasks: 20,
    active_tasks: 0,
    workers: [],
    status: 'available',
  });
}

/**
 * Create queue status with high load (>100 pending tasks)
 */
export function createQueueWithHighLoad(queueName: string = 'document_processing'): QueueStatus {
  return createQueueStatus(queueName, {
    pending_tasks: 150,
    active_tasks: 10,
    workers: [
      createWorker('worker-1', 'online'),
      createWorker('worker-2', 'online'),
      createWorker('worker-3', 'online'),
    ],
    status: 'available',
  });
}

/**
 * Create queue status with offline workers
 */
export function createQueueWithOfflineWorkers(
  queueName: string = 'document_processing'
): QueueStatus {
  return createQueueStatus(queueName, {
    pending_tasks: 25,
    active_tasks: 0,
    workers: [
      createWorker('worker-1', 'online'),
      createWorker('worker-2', 'offline'),
      createWorker('worker-3', 'offline'),
    ],
    status: 'available',
  });
}

/**
 * Create unavailable queue status (Celery broker offline)
 */
export function createUnavailableQueue(queueName: string = 'document_processing'): QueueStatus {
  return createQueueStatus(queueName, {
    pending_tasks: 0,
    active_tasks: 0,
    workers: [],
    status: 'unavailable',
  });
}

/**
 * Create list of tasks (for modal testing)
 * @param count - Number of tasks to create
 * @param pending - Whether tasks are pending (started_at: null) or active
 */
export function createTaskList(count: number, pending = false): TaskInfo[] {
  return Array.from({ length: count }, (_, i) =>
    createTask(`task-${i + 1}`, 'active', {
      task_name: `app.workers.document_tasks.${
        ['process_document', 'generate_embeddings', 'export_document'][i % 3]
      }`,
      started_at: pending ? null : new Date().toISOString(),
      estimated_duration: pending ? null : 3500,
    })
  );
}

// =============================================================================
// Story 7-27: Queue Monitoring Enhancement Types and Factories
// =============================================================================

/**
 * Processing step status for document processing pipeline
 * AC-7.27.4: Color-coded status badges
 */
export type StepStatus = 'done' | 'in_progress' | 'pending' | 'error';

/**
 * Individual processing step information
 * AC-7.27.2: Step breakdown table columns
 */
export interface StepInfo {
  step: 'parse' | 'chunk' | 'embed' | 'index';
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
}

/**
 * Extended task info with processing steps (Story 7-27)
 * AC-7.27.1-5: Per-step tracking and status visibility
 */
export interface TaskInfoWithSteps extends TaskInfo {
  document_id: string | null;
  document_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  processing_steps: StepInfo[];
  current_step: string | null;
}

/**
 * Bulk retry request schema
 * AC-7.27.10: Bulk retry API
 */
export interface BulkRetryRequest {
  document_ids?: string[];
  retry_all_failed?: boolean;
  kb_id?: string;
}

/**
 * Bulk retry response schema
 * AC-7.27.9-10: Retry success feedback
 */
export interface BulkRetryResponse {
  queued: number;
  failed: number;
  errors: Array<{ document_id: string; error: string }>;
}

/**
 * Create a single step info entry
 */
export function createStepInfo(
  step: StepInfo['step'],
  status: StepStatus = 'pending',
  overrides?: Partial<StepInfo>
): StepInfo {
  const defaults: StepInfo = {
    step,
    status,
    started_at: status !== 'pending' ? new Date().toISOString() : null,
    completed_at: status === 'done' ? new Date().toISOString() : null,
    duration_ms: status === 'done' ? 1500 : status === 'in_progress' ? 500 : null,
    error_message: status === 'error' ? `${step} processing failed: timeout exceeded` : null,
  };

  return { ...defaults, ...overrides };
}

/**
 * Create a complete set of processing steps for a task
 * AC-7.27.2: Each processing step (parse, chunk, embed, index) is displayed
 */
export function createProcessingSteps(
  currentStep: 'parse' | 'chunk' | 'embed' | 'index' | 'completed' = 'parse',
  hasError = false
): StepInfo[] {
  const steps: Array<StepInfo['step']> = ['parse', 'chunk', 'embed', 'index'];
  const currentIndex = currentStep === 'completed' ? steps.length : steps.indexOf(currentStep);

  return steps.map((step, index) => {
    let status: StepStatus;
    if (index < currentIndex) {
      status = 'done';
    } else if (index === currentIndex) {
      status = hasError ? 'error' : 'in_progress';
    } else {
      status = 'pending';
    }

    return createStepInfo(step, status, {
      duration_ms: status === 'done' ? 1000 + index * 500 : status === 'in_progress' ? 200 : null,
      error_message:
        hasError && index === currentIndex ? `${step} failed: Connection timeout` : null,
    });
  });
}

/**
 * Create task with processing steps (Story 7-27)
 */
export function createTaskWithSteps(
  taskId: string,
  documentStatus: TaskInfoWithSteps['document_status'] = 'PROCESSING',
  currentStep: 'parse' | 'chunk' | 'embed' | 'index' | 'completed' = 'chunk',
  overrides?: Partial<TaskInfoWithSteps>
): TaskInfoWithSteps {
  const hasError = documentStatus === 'FAILED';

  const defaults: TaskInfoWithSteps = {
    task_id: taskId,
    task_name: 'app.workers.document_tasks.process_document',
    status: 'active',
    started_at: new Date().toISOString(),
    estimated_duration: 5000,
    document_id: `doc-${taskId.slice(-8)}`,
    document_status: documentStatus,
    processing_steps: createProcessingSteps(currentStep, hasError),
    current_step: hasError || currentStep === 'completed' ? null : currentStep,
  };

  return { ...defaults, ...overrides };
}

/**
 * Create list of tasks with steps for testing
 * AC-7.27.11-14: Filter tabs testing
 */
export function createTaskListWithSteps(options?: {
  activeCount?: number;
  pendingCount?: number;
  failedCount?: number;
  completedCount?: number;
}): TaskInfoWithSteps[] {
  const { activeCount = 2, pendingCount = 1, failedCount = 1, completedCount = 1 } = options || {};
  const tasks: TaskInfoWithSteps[] = [];
  let taskIndex = 0;

  // Active tasks (currently processing)
  for (let i = 0; i < activeCount; i++) {
    tasks.push(
      createTaskWithSteps(
        `task-active-${++taskIndex}`,
        'PROCESSING',
        ['parse', 'chunk', 'embed', 'index'][i % 4] as 'parse' | 'chunk' | 'embed' | 'index'
      )
    );
  }

  // Pending tasks (not started)
  for (let i = 0; i < pendingCount; i++) {
    tasks.push(
      createTaskWithSteps(`task-pending-${++taskIndex}`, 'PENDING', 'parse', {
        started_at: null,
        processing_steps: createProcessingSteps('parse').map((s) => ({
          ...s,
          status: 'pending' as StepStatus,
          started_at: null,
        })),
      })
    );
  }

  // Failed tasks
  for (let i = 0; i < failedCount; i++) {
    tasks.push(
      createTaskWithSteps(`task-failed-${++taskIndex}`, 'FAILED', 'embed', {
        processing_steps: createProcessingSteps('embed', true),
      })
    );
  }

  // Completed tasks
  for (let i = 0; i < completedCount; i++) {
    tasks.push(
      createTaskWithSteps(`task-completed-${++taskIndex}`, 'COMPLETED', 'completed', {
        processing_steps: createProcessingSteps('completed'),
      })
    );
  }

  return tasks;
}

/**
 * Create bulk retry response
 * AC-7.27.9: Retry success feedback
 */
export function createBulkRetryResponse(
  queued: number,
  failed: number = 0,
  errors: BulkRetryResponse['errors'] = []
): BulkRetryResponse {
  return { queued, failed, errors };
}
