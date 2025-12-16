/**
 * Factory for Duplicate Detection and Replace test data (Stories 6.5, 6.6, 6.9)
 * Provides mock data for duplicate upload scenarios and document replacement workflows
 */

// ============================================================
// Types
// ============================================================

export type DuplicateResolution = 'replace' | 'skip' | 'keep_both';

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  new_file_name: string;
  new_file_hash: string;
  existing_document: ExistingDocumentInfo | null;
  match_type: 'exact_hash' | 'same_name' | 'similar_content' | null;
}

export interface ExistingDocumentInfo {
  id: string;
  name: string;
  file_hash: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  status: 'completed' | 'processing' | 'failed' | 'archived';
  chunk_count: number;
}

export interface NameCollisionInfo {
  archived_document_id: string;
  archived_document_name: string;
  existing_document_id: string;
  existing_document_name: string;
  created_at: string;
}

export interface ReplaceResult {
  success: boolean;
  old_document_id: string;
  new_document_id: string;
  old_document_archived: boolean;
  message: string;
}

export interface UploadWithDuplicateResponse {
  document_id: string | null;
  duplicate_detected: boolean;
  duplicate_info: DuplicateCheckResult | null;
  action_required: boolean;
  suggested_actions: DuplicateResolution[];
}

// ============================================================
// Duplicate Detection Results
// ============================================================

/**
 * Create a result for no duplicate detected
 */
export function createNoDuplicateResult(fileName: string): DuplicateCheckResult {
  return {
    is_duplicate: false,
    new_file_name: fileName,
    new_file_hash: `hash-${crypto.randomUUID()}`,
    existing_document: null,
    match_type: null,
  };
}

/**
 * Create a result for exact hash match (identical file)
 */
export function createExactDuplicateResult(
  fileName: string,
  existingDoc: Partial<ExistingDocumentInfo> = {}
): DuplicateCheckResult {
  const fileHash = `hash-${crypto.randomUUID()}`;
  return {
    is_duplicate: true,
    new_file_name: fileName,
    new_file_hash: fileHash,
    existing_document: {
      id: `doc-${crypto.randomUUID()}`,
      name: fileName,
      file_hash: fileHash, // Same hash = exact duplicate
      file_size: 1024 * 1024,
      created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'completed',
      chunk_count: 35,
      ...existingDoc,
    },
    match_type: 'exact_hash',
  };
}

/**
 * Create a result for same name match (different content)
 */
export function createSameNameDuplicateResult(
  fileName: string,
  existingDoc: Partial<ExistingDocumentInfo> = {}
): DuplicateCheckResult {
  return {
    is_duplicate: true,
    new_file_name: fileName,
    new_file_hash: `hash-new-${crypto.randomUUID()}`,
    existing_document: {
      id: `doc-${crypto.randomUUID()}`,
      name: fileName,
      file_hash: `hash-old-${crypto.randomUUID()}`, // Different hash
      file_size: 1024 * 1024,
      created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'completed',
      chunk_count: 35,
      ...existingDoc,
    },
    match_type: 'same_name',
  };
}

/**
 * Create a result for similar content match
 */
export function createSimilarContentDuplicateResult(
  fileName: string,
  existingFileName: string,
  existingDoc: Partial<ExistingDocumentInfo> = {}
): DuplicateCheckResult {
  return {
    is_duplicate: true,
    new_file_name: fileName,
    new_file_hash: `hash-new-${crypto.randomUUID()}`,
    existing_document: {
      id: `doc-${crypto.randomUUID()}`,
      name: existingFileName,
      file_hash: `hash-old-${crypto.randomUUID()}`,
      file_size: 1024 * 1024,
      created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'completed',
      chunk_count: 35,
      ...existingDoc,
    },
    match_type: 'similar_content',
  };
}

// ============================================================
// Name Collision Scenarios (for restore operations)
// ============================================================

/**
 * Create name collision info for restore operation
 */
export function createNameCollision(
  archivedDocName: string,
  existingDocName: string
): NameCollisionInfo {
  return {
    archived_document_id: `doc-archived-${crypto.randomUUID()}`,
    archived_document_name: archivedDocName,
    existing_document_id: `doc-existing-${crypto.randomUUID()}`,
    existing_document_name: existingDocName,
    created_at: new Date().toISOString(),
  };
}

/**
 * Create collision with same exact name
 */
export function createExactNameCollision(docName: string): NameCollisionInfo {
  return createNameCollision(docName, docName);
}

// ============================================================
// Upload Responses
// ============================================================

/**
 * Create successful upload response (no duplicate)
 */
export function createSuccessfulUploadResponse(documentId: string): UploadWithDuplicateResponse {
  return {
    document_id: documentId,
    duplicate_detected: false,
    duplicate_info: null,
    action_required: false,
    suggested_actions: [],
  };
}

/**
 * Create response requiring duplicate resolution
 */
export function createDuplicateUploadResponse(
  duplicateResult: DuplicateCheckResult
): UploadWithDuplicateResponse {
  const suggestedActions: DuplicateResolution[] = ['replace', 'skip'];

  // For same name but different content, also suggest keep_both
  if (duplicateResult.match_type === 'same_name') {
    suggestedActions.push('keep_both');
  }

  return {
    document_id: null,
    duplicate_detected: true,
    duplicate_info: duplicateResult,
    action_required: true,
    suggested_actions: suggestedActions,
  };
}

// ============================================================
// Replace Operation Results
// ============================================================

/**
 * Create successful replace result
 */
export function createSuccessfulReplaceResult(
  oldDocId: string,
  newDocId: string,
  archiveOld: boolean = true
): ReplaceResult {
  return {
    success: true,
    old_document_id: oldDocId,
    new_document_id: newDocId,
    old_document_archived: archiveOld,
    message: archiveOld
      ? 'Document replaced successfully. Previous version has been archived.'
      : 'Document replaced successfully. Previous version has been removed.',
  };
}

/**
 * Create failed replace result
 */
export function createFailedReplaceResult(
  oldDocId: string,
  reason: string
): ReplaceResult {
  return {
    success: false,
    old_document_id: oldDocId,
    new_document_id: '',
    old_document_archived: false,
    message: reason,
  };
}

// ============================================================
// Test Scenario Factories
// ============================================================

/**
 * Create scenario: upload exact duplicate of existing file
 */
export function createExactDuplicateScenario() {
  const fileName = 'quarterly-report.pdf';
  const existingDocId = `doc-${crypto.randomUUID()}`;

  return {
    fileName,
    duplicateResult: createExactDuplicateResult(fileName, { id: existingDocId }),
    uploadResponse: createDuplicateUploadResponse(
      createExactDuplicateResult(fileName, { id: existingDocId })
    ),
    expectedWarningText: /identical file already exists/i,
    suggestedAction: 'skip' as DuplicateResolution,
  };
}

/**
 * Create scenario: upload file with same name but different content
 */
export function createSameNameScenario() {
  const fileName = 'user-manual.pdf';
  const existingDocId = `doc-${crypto.randomUUID()}`;

  return {
    fileName,
    duplicateResult: createSameNameDuplicateResult(fileName, { id: existingDocId }),
    uploadResponse: createDuplicateUploadResponse(
      createSameNameDuplicateResult(fileName, { id: existingDocId })
    ),
    expectedWarningText: /file with the same name already exists/i,
    suggestedAction: 'replace' as DuplicateResolution,
  };
}

/**
 * Create scenario: restore archived doc that now has name conflict
 */
export function createRestoreCollisionScenario() {
  const docName = 'important-doc.pdf';

  return {
    archivedDocName: docName,
    existingDocName: docName,
    collision: createExactNameCollision(docName),
    expectedWarningText: /document with this name already exists/i,
    resolutionOptions: ['rename_restored', 'replace_existing', 'cancel'],
  };
}

/**
 * Create scenario: bulk upload with some duplicates
 */
export function createBulkUploadWithDuplicatesScenario() {
  return {
    files: [
      { name: 'new-doc-1.pdf', isDuplicate: false },
      { name: 'existing-doc.pdf', isDuplicate: true, matchType: 'same_name' as const },
      { name: 'new-doc-2.pdf', isDuplicate: false },
      { name: 'identical-copy.pdf', isDuplicate: true, matchType: 'exact_hash' as const },
    ],
    expectedDuplicateCount: 2,
    expectedNewCount: 2,
  };
}

// ============================================================
// Error Responses
// ============================================================

/**
 * Document being replaced is still processing
 */
export function createReplaceProcessingError(): { error: string; status: number } {
  return {
    error: 'Cannot replace a document that is still being processed',
    status: 400,
  };
}

/**
 * Permission denied for replace operation
 */
export function createReplacePermissionError(): { error: string; status: number } {
  return {
    error: 'You do not have permission to replace this document',
    status: 403,
  };
}

/**
 * Target document not found for replacement
 */
export function createReplaceNotFoundError(): { error: string; status: number } {
  return {
    error: 'Target document not found',
    status: 404,
  };
}

/**
 * Generic server error during duplicate check
 */
export function createDuplicateCheckError(): { error: string; status: number } {
  return {
    error: 'Failed to check for duplicates. Please try again.',
    status: 500,
  };
}

// ============================================================
// Auto-Clear Duplicate Scenarios (Story 6.5)
// ============================================================

/**
 * Create auto-clear suggestion for exact duplicate
 */
export function createAutoClearSuggestion(existingDocId: string) {
  return {
    action: 'auto_clear',
    reason: 'Identical file already exists in knowledge base',
    existing_document_id: existingDocId,
    confidence: 1.0,
    message: 'This file is identical to an existing document. Upload was automatically skipped.',
  };
}

/**
 * Create manual review suggestion for similar content
 */
export function createManualReviewSuggestion(existingDocId: string, similarity: number) {
  return {
    action: 'manual_review',
    reason: 'Similar content detected in existing document',
    existing_document_id: existingDocId,
    confidence: similarity,
    message: `This file has ${Math.round(similarity * 100)}% similarity with an existing document. Please review.`,
  };
}

// ============================================================
// API Route Patterns
// ============================================================

/**
 * Get API route patterns for duplicate detection
 */
export function getDuplicateDetectionRoutes(kbId: string) {
  return {
    checkDuplicate: `/api/v1/knowledge-bases/${kbId}/documents/check-duplicate`,
    uploadWithCheck: `/api/v1/knowledge-bases/${kbId}/documents/upload`,
    replaceDocument: `/api/v1/knowledge-bases/${kbId}/documents/*/replace`,
    resolveConflict: `/api/v1/knowledge-bases/${kbId}/documents/resolve-conflict`,
  };
}
