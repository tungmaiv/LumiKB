/**
 * Factory functions for document processing test fixtures.
 * Story 5-23: Document Processing Progress Screen
 */

// Re-declare types locally for E2E tests (to avoid @/ import issues)
// These match the types in src/types/processing.ts

type ProcessingStep = 'upload' | 'parse' | 'chunk' | 'embed' | 'index' | 'complete';
type StepStatus = 'pending' | 'in_progress' | 'done' | 'error' | 'skipped';
type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed' | 'archived';

interface ProcessingStepInfo {
  step: ProcessingStep;
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error: string | null;
}

interface DocumentProcessingStatus {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  current_step: ProcessingStep;
  chunk_count: number | null;
  created_at: string;
  updated_at: string;
}

interface DocumentProcessingDetails {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  current_step: ProcessingStep;
  chunk_count: number | null;
  total_duration_ms: number | null;
  steps: ProcessingStepInfo[];
  created_at: string;
  processing_started_at: string | null;
  processing_completed_at: string | null;
}

interface PaginatedDocumentProcessingResponse {
  documents: DocumentProcessingStatus[];
  total: number;
  page: number;
  page_size: number;
}

const PROCESSING_STEPS: ProcessingStep[] = [
  'upload',
  'parse',
  'chunk',
  'embed',
  'index',
  'complete',
];

/**
 * Create a single processing step info
 */
export function createStepInfo(
  step: ProcessingStep,
  status: StepStatus = 'pending',
  options: {
    started_at?: string;
    completed_at?: string;
    duration_ms?: number;
    error?: string;
  } = {}
): ProcessingStepInfo {
  const now = new Date();
  const started = options.started_at || (status !== 'pending' ? now.toISOString() : null);
  const completed = options.completed_at || (status === 'done' ? now.toISOString() : null);

  return {
    step,
    status,
    started_at: started,
    completed_at: completed,
    duration_ms: options.duration_ms ?? (status === 'done' ? 1500 : null),
    error: options.error ?? null,
  };
}

/**
 * Create steps array for a document at a specific processing stage
 */
export function createStepsForStage(
  currentStep: ProcessingStep,
  status: 'processing' | 'done' | 'error' = 'processing'
): ProcessingStepInfo[] {
  const currentIndex = PROCESSING_STEPS.indexOf(currentStep);
  const steps: ProcessingStepInfo[] = [];

  for (let i = 0; i < PROCESSING_STEPS.length; i++) {
    const step = PROCESSING_STEPS[i];

    if (i < currentIndex) {
      // Previous steps are done
      steps.push(createStepInfo(step, 'done', { duration_ms: 500 + Math.random() * 2000 }));
    } else if (i === currentIndex) {
      // Current step
      if (status === 'done') {
        steps.push(createStepInfo(step, 'done', { duration_ms: 500 + Math.random() * 2000 }));
      } else if (status === 'error') {
        steps.push(createStepInfo(step, 'error', { error: `Failed at ${step} step` }));
      } else {
        steps.push(createStepInfo(step, 'in_progress'));
      }
    } else {
      // Future steps are pending
      steps.push(createStepInfo(step, 'pending'));
    }
  }

  return steps;
}

/**
 * Create a document with processing status
 */
export function createDocumentProcessingStatus(
  options: Partial<DocumentProcessingStatus> = {}
): DocumentProcessingStatus {
  const id = options.id || `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const status = options.status || 'processing';
  const currentStep = options.current_step || 'parse';

  return {
    id,
    original_filename: options.original_filename || `document_${id.slice(-6)}.pdf`,
    file_type: options.file_type || 'pdf',
    file_size: options.file_size || 1024 * 1024 * 2, // 2MB
    status,
    current_step: currentStep,
    chunk_count: options.chunk_count ?? (status === 'ready' ? 25 : null),
    created_at: options.created_at || new Date().toISOString(),
    updated_at: options.updated_at || new Date().toISOString(),
  };
}

/**
 * Create detailed processing information for a document
 */
export function createDocumentProcessingDetails(
  options: Partial<DocumentProcessingDetails> = {}
): DocumentProcessingDetails {
  const id = options.id || `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const status = options.status || 'processing';
  const currentStep = options.current_step || 'parse';
  const steps =
    options.steps ||
    createStepsForStage(
      currentStep,
      status === 'ready' ? 'done' : status === 'failed' ? 'error' : 'processing'
    );

  // Calculate total duration from completed steps
  const totalDuration = steps
    .filter((s) => s.status === 'done')
    .reduce((sum, s) => sum + (s.duration_ms || 0), 0);

  return {
    id,
    original_filename: options.original_filename || `document_${id.slice(-6)}.pdf`,
    file_type: options.file_type || 'pdf',
    file_size: options.file_size || 1024 * 1024 * 2, // 2MB
    status,
    current_step: currentStep,
    chunk_count: options.chunk_count ?? (status === 'ready' ? 25 : null),
    total_duration_ms: options.total_duration_ms ?? (status === 'ready' ? totalDuration : null),
    steps,
    created_at: options.created_at || new Date().toISOString(),
    processing_started_at: options.processing_started_at || new Date().toISOString(),
    processing_completed_at:
      options.processing_completed_at ?? (status === 'ready' ? new Date().toISOString() : null),
  };
}

/**
 * Create a paginated response with multiple documents
 */
export function createPaginatedProcessingResponse(
  count: number = 10,
  options: {
    page?: number;
    page_size?: number;
    total?: number;
    statuses?: DocumentStatus[];
  } = {}
): PaginatedDocumentProcessingResponse {
  const page = options.page || 1;
  const page_size = options.page_size || 20;
  const total = options.total || count;
  const statuses = options.statuses || ['pending', 'processing', 'ready', 'failed'];

  const documents: DocumentProcessingStatus[] = [];
  const steps: ProcessingStep[] = ['upload', 'parse', 'chunk', 'embed', 'index', 'complete'];

  for (let i = 0; i < count; i++) {
    const status = statuses[i % statuses.length];
    const currentStep = steps[Math.min(i % 6, 5)];

    documents.push(
      createDocumentProcessingStatus({
        id: `doc-${i + 1}`,
        original_filename: `document_${i + 1}.pdf`,
        status,
        current_step: currentStep,
        file_size: 1024 * 1024 * (1 + (i % 5)),
        chunk_count: status === 'ready' ? 20 + i * 2 : null,
      })
    );
  }

  return {
    documents,
    total,
    page,
    page_size,
  };
}

/**
 * Create a response with documents in various processing states
 */
export function createMixedProcessingResponse(): PaginatedDocumentProcessingResponse {
  return {
    documents: [
      createDocumentProcessingStatus({
        id: 'doc-pending',
        original_filename: 'waiting_doc.pdf',
        status: 'pending',
        current_step: 'upload',
      }),
      createDocumentProcessingStatus({
        id: 'doc-parsing',
        original_filename: 'parsing_doc.pdf',
        status: 'processing',
        current_step: 'parse',
      }),
      createDocumentProcessingStatus({
        id: 'doc-chunking',
        original_filename: 'chunking_doc.docx',
        status: 'processing',
        current_step: 'chunk',
        file_type: 'docx',
      }),
      createDocumentProcessingStatus({
        id: 'doc-embedding',
        original_filename: 'embedding_doc.md',
        status: 'processing',
        current_step: 'embed',
        file_type: 'md',
      }),
      createDocumentProcessingStatus({
        id: 'doc-ready',
        original_filename: 'completed_doc.pdf',
        status: 'ready',
        current_step: 'complete',
        chunk_count: 42,
      }),
      createDocumentProcessingStatus({
        id: 'doc-failed',
        original_filename: 'failed_doc.txt',
        status: 'failed',
        current_step: 'embed',
        file_type: 'txt',
      }),
    ],
    total: 6,
    page: 1,
    page_size: 20,
  };
}

/**
 * Create an empty processing response
 */
export function createEmptyProcessingResponse(): PaginatedDocumentProcessingResponse {
  return {
    documents: [],
    total: 0,
    page: 1,
    page_size: 20,
  };
}

/**
 * Create a failed document with error details
 */
export function createFailedDocumentDetails(
  failedStep: ProcessingStep = 'embed',
  errorMessage: string = 'Failed to generate embeddings: Model unavailable'
): DocumentProcessingDetails {
  return createDocumentProcessingDetails({
    id: 'doc-failed',
    original_filename: 'failed_document.pdf',
    status: 'failed',
    current_step: failedStep,
    steps: createStepsForStage(failedStep, 'error').map((s) =>
      s.step === failedStep ? { ...s, error: errorMessage } : s
    ),
  });
}

/**
 * Create a completed document with full timing details
 */
export function createCompletedDocumentDetails(): DocumentProcessingDetails {
  const now = new Date();
  const startTime = new Date(now.getTime() - 30000); // 30 seconds ago

  return createDocumentProcessingDetails({
    id: 'doc-complete',
    original_filename: 'completed_document.pdf',
    status: 'ready',
    current_step: 'complete',
    chunk_count: 35,
    total_duration_ms: 28500,
    processing_started_at: startTime.toISOString(),
    processing_completed_at: now.toISOString(),
    steps: PROCESSING_STEPS.map((step, index) =>
      createStepInfo(step, 'done', {
        started_at: new Date(startTime.getTime() + index * 5000).toISOString(),
        completed_at: new Date(startTime.getTime() + (index + 1) * 5000 - 500).toISOString(),
        duration_ms: 4500 + Math.floor(Math.random() * 1000),
      })
    ),
  });
}
