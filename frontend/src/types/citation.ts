/**
 * Citation type definitions for document sources.
 */

export interface Citation {
  /** Citation number [n] */
  number: number;
  /** Source document ID */
  document_id: string;
  /** Display name of document */
  document_name: string;
  /** Page number (if applicable) */
  page_number?: number | null;
  /** Section header (if applicable) */
  section_header?: string | null;
  /** Excerpt text from source */
  excerpt: string;
  /** Character start position in document */
  char_start: number;
  /** Character end position in document */
  char_end: number;
  /** Citation confidence score (0-1) */
  confidence: number;
}
