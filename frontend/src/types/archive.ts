/**
 * Archive types for document lifecycle management
 * Story 6-7: Archive Management UI
 */

export interface ArchivedDocument {
  id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: 'archived';
  chunk_count: number;
  kb_id: string;
  kb_name: string;
  archived_at: string; // ISO 8601
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
  uploader_email: string | null;
  tags: string[];
}

export interface ArchivedDocumentsFilter {
  kb_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedArchivedDocumentsResponse {
  data: ArchivedDocument[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface RestoreDocumentResponse {
  id: string;
  message: string;
}

export interface RestoreDocumentError {
  status: number;
  detail: string;
  error?: 'name_collision';
  conflicting_document_id?: string;
}

export interface PurgeDocumentResponse {
  id: string;
  message: string;
}

export interface BulkPurgeRequest {
  document_ids: string[];
}

export interface BulkPurgeResponse {
  purged_count: number;
  skipped_ids: string[];
  message: string;
}
