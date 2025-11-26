'use client';

import { useState, useCallback } from 'react';
import { FileTextIcon } from 'lucide-react';
import { DocumentList, type SortField, type SortOrder } from './document-list';
import { DocumentDetailModal } from './document-detail-modal';
import { UploadDropzone } from './upload-dropzone';
import { useDocuments, type DocumentListItem } from '@/lib/hooks/use-documents';
import type { DocumentStatus } from './document-status-badge';
import { cn } from '@/lib/utils';

type PermissionLevel = 'READ' | 'WRITE' | 'ADMIN';

/** Document type compatible with both DocumentList and DocumentDetailModal */
interface DocumentForList {
  id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  chunk_count?: number;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
  uploaded_by?: string | null;
  uploader_email?: string | null;
  version_number?: number;
}

interface DocumentsPanelProps {
  /** Knowledge Base ID */
  kbId: string;
  /** User's permission level on the KB */
  userPermission?: PermissionLevel;
  /** Additional CSS classes */
  className?: string;
}

/**
 * DocumentsPanel combines UploadDropzone and DocumentList for a complete document management UI.
 *
 * Features:
 * - Upload dropzone at the top (visible only for WRITE/ADMIN users)
 * - Document list with pagination and sorting
 * - Document detail modal on click
 * - Automatic refetch after upload
 * - Status polling for processing documents
 *
 * @example
 * <DocumentsPanel
 *   kbId="kb-uuid"
 *   userPermission="WRITE"
 * />
 */
export function DocumentsPanel({ kbId, userPermission = 'READ', className }: DocumentsPanelProps) {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedDocument, setSelectedDocument] = useState<DocumentForList | null>(null);

  const { documents, total, totalPages, isLoading, error, refetch } = useDocuments({
    kbId,
    page,
    limit: 20,
    sortBy,
    sortOrder,
  });

  const handleUploadComplete = useCallback(() => {
    // Refetch documents to show newly uploaded ones
    refetch();
  }, [refetch]);

  const handleDocumentClick = useCallback((doc: DocumentForList) => {
    setSelectedDocument(doc);
  }, []);

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleCloseModal = useCallback(() => {
    setSelectedDocument(null);
  }, []);

  const canUpload = userPermission === 'WRITE' || userPermission === 'ADMIN';

  // Transform documents to compatible type (filter out ARCHIVED status for now)
  const documentsForList: DocumentForList[] = documents
    .filter(
      (doc): doc is DocumentListItem & { status: DocumentStatus } => doc.status !== 'ARCHIVED'
    )
    .map((doc) => ({
      id: doc.id,
      name: doc.name,
      original_filename: doc.original_filename,
      mime_type: doc.mime_type,
      file_size_bytes: doc.file_size_bytes,
      status: doc.status as DocumentStatus,
      chunk_count: doc.chunk_count,
      created_at: doc.created_at,
      updated_at: doc.updated_at,
      uploaded_by: doc.uploaded_by,
      uploader_email: doc.uploader_email,
      version_number: doc.version_number,
    }));

  if (error) {
    return (
      <div className={cn('p-6 text-center', className)}>
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  // Create modal document with required fields
  const modalDocument = selectedDocument
    ? {
        id: selectedDocument.id,
        kb_id: kbId,
        name: selectedDocument.name,
        original_filename: selectedDocument.original_filename,
        mime_type: selectedDocument.mime_type,
        file_size_bytes: selectedDocument.file_size_bytes,
        file_path: null,
        checksum: '',
        status: selectedDocument.status,
        chunk_count: selectedDocument.chunk_count ?? 0,
        processing_started_at: selectedDocument.processing_started_at ?? null,
        processing_completed_at: selectedDocument.processing_completed_at ?? null,
        last_error: selectedDocument.last_error ?? null,
        retry_count: 0,
        uploaded_by: selectedDocument.uploaded_by ?? null,
        uploader_email: selectedDocument.uploader_email ?? null,
        created_at: selectedDocument.created_at,
        updated_at: selectedDocument.updated_at,
      }
    : null;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Upload Zone - Only for WRITE/ADMIN users */}
      {canUpload && (
        <UploadDropzone
          kbId={kbId}
          userPermission={userPermission}
          onUploadComplete={handleUploadComplete}
        />
      )}

      {/* Document List */}
      {documentsForList.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <FileTextIcon className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No documents yet</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            {canUpload
              ? 'Upload your first document by dragging files above or clicking to browse.'
              : 'No documents have been uploaded to this knowledge base yet.'}
          </p>
        </div>
      ) : (
        <DocumentList
          documents={documentsForList}
          kbId={kbId}
          onRetry={handleRetry}
          onDocumentClick={handleDocumentClick}
          showPagination
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          showSort
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortByChange={setSortBy}
          onSortOrderChange={setSortOrder}
          isLoading={isLoading}
          total={total}
        />
      )}

      {/* Document Detail Modal */}
      <DocumentDetailModal
        document={modalDocument}
        kbId={kbId}
        isOpen={!!selectedDocument}
        onClose={handleCloseModal}
        onRetrySuccess={refetch}
      />
    </div>
  );
}
