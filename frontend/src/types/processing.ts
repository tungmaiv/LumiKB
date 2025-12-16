/**
 * Document processing progress types for Story 5-23.
 *
 * Provides visibility into document processing pipeline:
 * - Step-level progress: upload, parse, chunk, embed, index, complete
 * - Per-step timing: started_at, completed_at, duration_ms
 * - Error tracking: step-specific error messages
 * - Filtering: by name, file type, status, and current step
 */

/** Processing pipeline steps in order */
export type ProcessingStep =
  | "upload"
  | "parse"
  | "chunk"
  | "embed"
  | "index"
  | "complete";

/** Status of individual processing step */
export type StepStatus =
  | "pending"
  | "in_progress"
  | "done"
  | "error"
  | "skipped";

/** Document processing status */
export type DocumentStatus =
  | "pending"
  | "processing"
  | "ready"
  | "failed"
  | "archived";

/** Information about a single processing step */
export interface ProcessingStepInfo {
  /** The step name */
  step: ProcessingStep;

  /** Status of this step */
  status: StepStatus;

  /** When the step started (ISO 8601) */
  started_at: string | null;

  /** When the step completed (ISO 8601) */
  completed_at: string | null;

  /** Duration in milliseconds */
  duration_ms: number | null;

  /** Error message if step failed */
  error: string | null;
}

/** Document with processing status for list view */
export interface DocumentProcessingStatus {
  /** Document UUID */
  id: string;

  /** Original filename */
  original_filename: string;

  /** File type (e.g., "pdf", "docx") */
  file_type: string;

  /** File size in bytes */
  file_size: number;

  /** Overall document status */
  status: DocumentStatus;

  /** Current processing step */
  current_step: ProcessingStep;

  /** Number of chunks created (null if not yet indexed) */
  chunk_count: number | null;

  /** When document was created (ISO 8601) */
  created_at: string;

  /** When document was last updated (ISO 8601) */
  updated_at: string;
}

/** Detailed processing information for a single document */
export interface DocumentProcessingDetails {
  /** Document UUID */
  id: string;

  /** Original filename */
  original_filename: string;

  /** File type (e.g., "pdf", "docx") */
  file_type: string;

  /** File size in bytes */
  file_size: number;

  /** Overall document status */
  status: DocumentStatus;

  /** Current processing step */
  current_step: ProcessingStep;

  /** Number of chunks created (null if not yet indexed) */
  chunk_count: number | null;

  /** Total processing duration in milliseconds */
  total_duration_ms: number | null;

  /** Step-by-step processing information (list of steps) */
  steps: ProcessingStepInfo[];

  /** When document was created (ISO 8601) */
  created_at: string;

  /** When processing started (ISO 8601) */
  processing_started_at: string | null;

  /** When processing completed (ISO 8601) */
  processing_completed_at: string | null;
}

/** Paginated response for document processing list */
export interface PaginatedDocumentProcessingResponse {
  /** List of documents with processing status */
  documents: DocumentProcessingStatus[];

  /** Total number of documents matching filters */
  total: number;

  /** Current page number */
  page: number;

  /** Page size */
  page_size: number;
}

/** Filter parameters for processing status list */
export interface ProcessingFilters {
  /** Filter by document name (partial match) */
  name?: string;

  /** Filter by file type */
  file_type?: string;

  /** Filter by overall status */
  status?: DocumentStatus;

  /** Filter by current processing step */
  current_step?: ProcessingStep;

  /** Page number (1-indexed) */
  page?: number;

  /** Items per page */
  page_size?: number;

  /** Sort field */
  sort_by?: "created_at" | "updated_at" | "original_filename" | "status";

  /** Sort order */
  sort_order?: "asc" | "desc";
}

/** Human-readable labels for processing steps */
export const STEP_LABELS: Record<ProcessingStep, string> = {
  upload: "Upload",
  parse: "Parse",
  chunk: "Chunk",
  embed: "Embed",
  index: "Index",
  complete: "Complete",
};

/** Human-readable labels for step statuses */
export const STATUS_LABELS: Record<StepStatus, string> = {
  pending: "Pending",
  in_progress: "In Progress",
  done: "Done",
  error: "Error",
  skipped: "Skipped",
};

/** Human-readable labels for document statuses */
export const DOC_STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
  archived: "Archived",
};

/** Processing steps in order for progress display */
export const PROCESSING_STEPS_ORDER: ProcessingStep[] = [
  "upload",
  "parse",
  "chunk",
  "embed",
  "index",
  "complete",
];
