/**
 * Document Chunk types for Story 5-26.
 *
 * Types matching the backend API response schemas from Story 5-25.
 */

/**
 * Single document chunk from Qdrant.
 * AC-5.25.1: chunk_id, chunk_index, text, char_start, char_end, page_number, section_header
 */
export interface DocumentChunk {
  /** Qdrant point ID (UUID) */
  chunk_id: string;
  /** Position in document (0-indexed) */
  chunk_index: number;
  /** Chunk text content */
  text: string;
  /** Start character offset in document */
  char_start: number;
  /** End character offset in document */
  char_end: number;
  /** Page number if PDF */
  page_number: number | null;
  /** Section header if available */
  section_header: string | null;
  /** Search relevance score (if search query was used) */
  score: number | null;
}

/**
 * Paginated response for document chunks endpoint.
 * AC-5.25.2: Cursor-based pagination with has_more indicator.
 */
export interface DocumentChunksResponse {
  /** List of chunks */
  chunks: DocumentChunk[];
  /** Total number of chunks for this document */
  total: number;
  /** Whether more chunks exist after cursor */
  has_more: boolean;
  /** Next chunk_index for pagination */
  next_cursor: number | null;
}

/**
 * Response for document content endpoint.
 * AC-5.25.4: Returns text, mime_type, and optional HTML for DOCX.
 */
export interface DocumentContentResponse {
  /** Full document text content */
  text: string;
  /** Document MIME type */
  mime_type: string;
  /** HTML rendering for DOCX documents */
  html: string | null;
}
