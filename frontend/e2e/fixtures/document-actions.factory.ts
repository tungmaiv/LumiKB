/**
 * Factory for Document Archive/Restore/Purge test data (Epic 6)
 * Provides mock data for document lifecycle management operations
 */

// ============================================================
// Types
// ============================================================

export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'archived';

export interface ArchivedDocument {
  id: string;
  name: string;
  status: DocumentStatus;
  kb_id: string;
  file_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  archived_by: string | null;
  failure_reason: string | null;
  chunk_count: number;
}

export interface ArchiveStats {
  total_active: number;
  total_archived: number;
  total_failed: number;
  total_processing: number;
}

export interface ArchiveOperation {
  document_id: string;
  operation: 'archive' | 'restore' | 'purge' | 'clear';
  status: 'success' | 'failed';
  message: string;
  timestamp: string;
}

export interface BulkOperationResult {
  success_count: number;
  failure_count: number;
  operations: ArchiveOperation[];
}

// ============================================================
// Document State Factories
// ============================================================

/**
 * Create a mock document with specified status
 */
export function createMockDocument(
  status: DocumentStatus,
  overrides: Partial<ArchivedDocument> = {}
): ArchivedDocument {
  const now = new Date().toISOString();
  const isArchived = status === 'archived';
  const isFailed = status === 'failed';

  return {
    id: `doc-${crypto.randomUUID()}`,
    name: `test-document-${status}.pdf`,
    status,
    kb_id: `kb-${crypto.randomUUID()}`,
    file_type: 'application/pdf',
    file_size: 1024 * 1024,
    created_at: now,
    updated_at: now,
    archived_at: isArchived ? now : null,
    archived_by: isArchived ? 'user-123' : null,
    failure_reason: isFailed ? 'Processing failed: Invalid document format' : null,
    chunk_count: isArchived ? 0 : isFailed ? 0 : 25,
    ...overrides,
  };
}

/**
 * Create an active (completed) document
 */
export function createActiveDocument(overrides: Partial<ArchivedDocument> = {}): ArchivedDocument {
  return createMockDocument('completed', {
    name: 'active-document.pdf',
    chunk_count: 42,
    ...overrides,
  });
}

/**
 * Create an archived document
 */
export function createArchivedDocument(overrides: Partial<ArchivedDocument> = {}): ArchivedDocument {
  return createMockDocument('archived', {
    name: 'archived-document.pdf',
    archived_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
    archived_by: 'admin-user',
    ...overrides,
  });
}

/**
 * Create a failed document
 */
export function createFailedDocument(
  failureReason: string = 'Processing failed: Unsupported file format',
  overrides: Partial<ArchivedDocument> = {}
): ArchivedDocument {
  return createMockDocument('failed', {
    name: 'failed-document.pdf',
    failure_reason: failureReason,
    ...overrides,
  });
}

/**
 * Create a processing document
 */
export function createProcessingDocument(overrides: Partial<ArchivedDocument> = {}): ArchivedDocument {
  return createMockDocument('processing', {
    name: 'processing-document.pdf',
    chunk_count: 0,
    ...overrides,
  });
}

/**
 * Create a pending document
 */
export function createPendingDocument(overrides: Partial<ArchivedDocument> = {}): ArchivedDocument {
  return createMockDocument('pending', {
    name: 'pending-document.pdf',
    chunk_count: 0,
    ...overrides,
  });
}

// ============================================================
// Document List Factories
// ============================================================

/**
 * Create a mixed list of documents with various statuses
 */
export function createMixedDocumentList(kbId: string): ArchivedDocument[] {
  return [
    createActiveDocument({ kb_id: kbId, name: 'report-2024.pdf' }),
    createActiveDocument({ kb_id: kbId, name: 'manual-v2.pdf' }),
    createArchivedDocument({ kb_id: kbId, name: 'old-report.pdf' }),
    createArchivedDocument({ kb_id: kbId, name: 'deprecated-manual.pdf' }),
    createFailedDocument('Parsing error: Corrupted PDF', { kb_id: kbId, name: 'corrupted.pdf' }),
    createProcessingDocument({ kb_id: kbId, name: 'new-upload.pdf' }),
  ];
}

/**
 * Create only active documents
 */
export function createActiveDocumentList(kbId: string, count: number = 5): ArchivedDocument[] {
  return Array.from({ length: count }, (_, i) =>
    createActiveDocument({
      kb_id: kbId,
      name: `document-${i + 1}.pdf`,
    })
  );
}

/**
 * Create only archived documents
 */
export function createArchivedDocumentList(kbId: string, count: number = 5): ArchivedDocument[] {
  return Array.from({ length: count }, (_, i) =>
    createArchivedDocument({
      kb_id: kbId,
      name: `archived-${i + 1}.pdf`,
      archived_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
    })
  );
}

/**
 * Create only failed documents
 */
export function createFailedDocumentList(kbId: string): ArchivedDocument[] {
  const failureReasons = [
    'Processing failed: File too large',
    'Processing failed: Unsupported format',
    'Processing failed: Corrupted file',
    'Processing failed: Timeout exceeded',
    'Processing failed: Embedding service unavailable',
  ];

  return failureReasons.map((reason, i) =>
    createFailedDocument(reason, {
      kb_id: kbId,
      name: `failed-${i + 1}.pdf`,
    })
  );
}

// ============================================================
// Archive Statistics
// ============================================================

/**
 * Create mock archive statistics
 */
export function createArchiveStats(overrides: Partial<ArchiveStats> = {}): ArchiveStats {
  return {
    total_active: 45,
    total_archived: 12,
    total_failed: 3,
    total_processing: 2,
    ...overrides,
  };
}

/**
 * Create stats for empty KB
 */
export function createEmptyKBStats(): ArchiveStats {
  return {
    total_active: 0,
    total_archived: 0,
    total_failed: 0,
    total_processing: 0,
  };
}

/**
 * Create stats with many archived documents
 */
export function createHighArchiveStats(): ArchiveStats {
  return {
    total_active: 100,
    total_archived: 250,
    total_failed: 15,
    total_processing: 0,
  };
}

// ============================================================
// Operation Results
// ============================================================

/**
 * Create successful archive operation result
 */
export function createSuccessfulArchiveOperation(documentId: string): ArchiveOperation {
  return {
    document_id: documentId,
    operation: 'archive',
    status: 'success',
    message: 'Document archived successfully',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create successful restore operation result
 */
export function createSuccessfulRestoreOperation(documentId: string): ArchiveOperation {
  return {
    document_id: documentId,
    operation: 'restore',
    status: 'success',
    message: 'Document restored successfully',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create successful purge operation result
 */
export function createSuccessfulPurgeOperation(documentId: string): ArchiveOperation {
  return {
    document_id: documentId,
    operation: 'purge',
    status: 'success',
    message: 'Document permanently deleted',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create successful clear failed operation result
 */
export function createSuccessfulClearOperation(documentId: string): ArchiveOperation {
  return {
    document_id: documentId,
    operation: 'clear',
    status: 'success',
    message: 'Failed document cleared',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create successful cancel processing operation result
 */
export function createSuccessfulCancelOperation(documentId: string): { message: string } {
  return {
    message: 'Document processing cancelled',
  };
}

/**
 * Create failed operation result
 */
export function createFailedOperation(
  documentId: string,
  operation: 'archive' | 'restore' | 'purge' | 'clear',
  reason: string
): ArchiveOperation {
  return {
    document_id: documentId,
    operation,
    status: 'failed',
    message: reason,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create bulk operation result
 */
export function createBulkOperationResult(
  documentIds: string[],
  operation: 'archive' | 'restore' | 'purge' | 'clear',
  failureRate: number = 0
): BulkOperationResult {
  const operations: ArchiveOperation[] = documentIds.map((id, index) => {
    const shouldFail = index < Math.floor(documentIds.length * failureRate);
    if (shouldFail) {
      return createFailedOperation(id, operation, `Failed to ${operation} document`);
    }
    return {
      document_id: id,
      operation,
      status: 'success' as const,
      message: `Document ${operation}d successfully`,
      timestamp: new Date().toISOString(),
    };
  });

  return {
    success_count: operations.filter((op) => op.status === 'success').length,
    failure_count: operations.filter((op) => op.status === 'failed').length,
    operations,
  };
}

// ============================================================
// Error Responses
// ============================================================

/**
 * Document not found error
 */
export function createDocumentNotFoundError(): { error: string; status: number } {
  return {
    error: 'Document not found',
    status: 404,
  };
}

/**
 * Permission denied error
 */
export function createPermissionDeniedError(): { error: string; status: number } {
  return {
    error: 'You do not have permission to perform this action',
    status: 403,
  };
}

/**
 * Invalid state error (e.g., trying to archive already archived document)
 */
export function createInvalidStateError(
  currentState: DocumentStatus,
  attemptedOperation: string
): { error: string; status: number } {
  return {
    error: `Cannot ${attemptedOperation} a document with status: ${currentState}`,
    status: 400,
  };
}

/**
 * Purge requires archived state error
 */
export function createPurgeRequiresArchivedError(): { error: string; status: number } {
  return {
    error: 'Document must be archived before it can be permanently deleted',
    status: 400,
  };
}

/**
 * Server error during operation
 */
export function createServerError(): { error: string; status: number } {
  return {
    error: 'An unexpected error occurred. Please try again later.',
    status: 500,
  };
}

// ============================================================
// API Route Patterns
// ============================================================

/**
 * Get API route patterns for document actions
 */
export function getDocumentActionRoutes(kbId: string) {
  return {
    listDocuments: `/api/v1/knowledge-bases/${kbId}/documents`,
    archiveDocument: `/api/v1/knowledge-bases/${kbId}/documents/*/archive`,
    restoreDocument: `/api/v1/knowledge-bases/${kbId}/documents/*/restore`,
    purgeDocument: `/api/v1/knowledge-bases/${kbId}/documents/*/purge`,
    clearFailed: `/api/v1/knowledge-bases/${kbId}/documents/*/clear`,
    cancelProcessing: `/api/v1/knowledge-bases/${kbId}/documents/*/cancel`,
    bulkArchive: `/api/v1/knowledge-bases/${kbId}/documents/bulk-archive`,
    bulkRestore: `/api/v1/knowledge-bases/${kbId}/documents/bulk-restore`,
    bulkPurge: `/api/v1/knowledge-bases/${kbId}/documents/bulk-purge`,
    bulkClear: `/api/v1/knowledge-bases/${kbId}/documents/bulk-clear`,
    archiveStats: `/api/v1/knowledge-bases/${kbId}/documents/stats`,
  };
}
