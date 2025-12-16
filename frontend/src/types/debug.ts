/**
 * Debug Info Types - Story 9-15: KB Debug Mode & Prompt Configuration
 *
 * Types for RAG pipeline debug telemetry displayed in chat UI.
 * Mirrors backend schemas from backend/app/schemas/chat.py.
 */

/**
 * Debug information for a single retrieved chunk (AC-9.15.11)
 */
export interface ChunkDebugInfo {
  /** First 100 characters of chunk text */
  preview: string;
  /** Relevance/similarity score (0.0-1.0) */
  similarity_score: number;
  /** Source document name */
  document_name: string;
  /** Page number if available */
  page_number?: number | null;
}

/**
 * Debug information for KB prompt parameters (AC-9.15.11)
 */
export interface KBParamsDebugInfo {
  /** First 100 chars of system prompt */
  system_prompt_preview: string;
  /** Citation style (inline/footnote/none) */
  citation_style: string;
  /** Response language code */
  response_language: string;
  /** Uncertainty handling strategy */
  uncertainty_handling: string;
}

/**
 * Debug timing metrics (AC-9.15.11)
 */
export interface TimingDebugInfo {
  /** Time spent on retrieval in milliseconds */
  retrieval_ms: number;
  /** Time spent on context assembly in milliseconds */
  context_assembly_ms: number;
}

/**
 * Complete debug information for RAG pipeline telemetry (AC-9.15.10-13)
 *
 * Emitted as SSE event type="debug" when KB debug_mode is enabled.
 * Contains KB parameters, retrieved chunks with scores, and timing metrics.
 */
export interface DebugInfo {
  /** KB prompt configuration parameters */
  kb_params: KBParamsDebugInfo;
  /** Retrieved chunks with similarity scores */
  chunks_retrieved: ChunkDebugInfo[];
  /** Pipeline timing breakdown */
  timing: TimingDebugInfo;
}
