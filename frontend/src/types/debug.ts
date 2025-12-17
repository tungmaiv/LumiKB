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
  /** Time spent on query rewriting in milliseconds (Story 8-0) */
  query_rewrite_ms?: number;
}

/**
 * Debug information for query rewriting (Story 8-0)
 *
 * Shows the original query, rewritten query, and rewriting metadata.
 * Only populated when chat history exists and rewriting is attempted.
 */
export interface QueryRewriteDebugInfo {
  /** Original user query */
  original_query: string;
  /** Reformulated standalone query */
  rewritten_query: string;
  /** Whether the query was actually modified */
  was_rewritten: boolean;
  /** LLM model ID used for rewriting (empty if skipped) */
  model_used: string;
  /** Time spent on rewriting in milliseconds */
  latency_ms: number;
}

/**
 * Complete debug information for RAG pipeline telemetry (AC-9.15.10-13)
 *
 * Emitted as SSE event type="debug" when KB debug_mode is enabled.
 * Contains KB parameters, retrieved chunks with scores, timing metrics,
 * and query rewriting information (Story 8-0).
 */
export interface DebugInfo {
  /** KB prompt configuration parameters */
  kb_params: KBParamsDebugInfo;
  /** Retrieved chunks with similarity scores */
  chunks_retrieved: ChunkDebugInfo[];
  /** Pipeline timing breakdown */
  timing: TimingDebugInfo;
  /** Query rewriting info (Story 8-0) - present when history exists */
  query_rewrite?: QueryRewriteDebugInfo | null;
}
