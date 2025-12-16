'use client';

import { useState, useCallback, useMemo, Suspense } from 'react';
import { FileTextIcon } from 'lucide-react';
import { DocumentList, type SortField, type SortOrder } from './document-list';
import { DocumentDetailModal } from './document-detail-modal';
import { DocumentFilterBar } from './document-filter-bar';
import { DocumentPagination } from './document-pagination';
import { UploadDropzone } from './upload-dropzone';
import { useDocuments, type DocumentListItem } from '@/lib/hooks/use-documents';
import { useDocumentFilters } from '@/lib/hooks/use-document-filters';
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
  tags?: string[];
}

interface DocumentsPanelProps {
  /** Knowledge Base ID */
  kbId: string;
  /** User's permission level on the KB */
  userPermission?: PermissionLevel;
  /** Additional CSS classes */
  className?: string;
  /** Enable filtering UI (Story 5-24) */
  showFilters?: boolean;
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
 * - Filtering by search, status, type, tags, date range (Story 5-24)
 *
 * @example
 * <DocumentsPanel
 *   kbId="kb-uuid"
 *   userPermission="WRITE"
 *   showFilters
 * />
 */
export function DocumentsPanel({ kbId, userPermission = 'READ', className, showFilters = true }: DocumentsPanelProps) {
  const [selectedDocument, setSelectedDocument] = useState<DocumentForList | null>(null);

  // Use filter state from URL (Story 5-24)
  const { filters, actions, hasActiveFilters, activeFilterCount } = useDocumentFilters();

  // Memoize the document filters object to prevent unnecessary re-renders
  const documentFilters = useMemo(
    () => ({
      search: filters.search,
      status: filters.status,
      mimeType: filters.mimeType,
      tags: filters.tags,
      dateFrom: filters.dateFrom,
      dateTo: filters.dateTo,
    }),
    [filters.search, filters.status, filters.mimeType, filters.tags, filters.dateFrom, filters.dateTo]
  );

  const { documents, total, totalPages, isLoading, error, refetch } = useDocuments({
    kbId,
    page: filters.page,
    limit: filters.limit,
    sortBy: filters.sortBy,
    sortOrder: filters.sortOrder,
    filters: documentFilters,
  });

  // Extract unique tags from all documents for filter options
  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    documents.forEach((doc) => {
      doc.tags?.forEach((tag) => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [documents]);

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

  // Close detail modal if the currently viewed document was deleted/archived
  const handleDocumentRemoved = useCallback(
    (documentId: string) => {
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null);
      }
      refetch();
    },
    [selectedDocument?.id, refetch]
  );

  const canUpload = userPermission === 'WRITE' || userPermission === 'ADMIN';
  const canManage = userPermission === 'ADMIN';

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
      tags: doc.tags,
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

      {/* Filter Bar (Story 5-24) */}
      {showFilters && (
        <Suspense fallback={<div className="h-10 bg-muted/30 animate-pulse rounded-md" />}>
          <DocumentFilterBar
            filters={filters}
            actions={actions}
            hasActiveFilters={hasActiveFilters}
            activeFilterCount={activeFilterCount}
            availableTags={availableTags}
          />
        </Suspense>
      )}

      {/* Document List */}
      {documentsForList.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <FileTextIcon className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">
            {hasActiveFilters ? 'No documents match your filters' : 'No documents yet'}
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            {hasActiveFilters ? (
              <>
                Try adjusting your filters or{' '}
                <button
                  onClick={() => actions.resetFilters()}
                  className="text-primary underline hover:no-underline"
                >
                  clear all filters
                </button>
              </>
            ) : canUpload ? (
              'Upload your first document by dragging files above or clicking to browse.'
            ) : (
              'No documents have been uploaded to this knowledge base yet.'
            )}
          </p>
        </div>
      ) : (
        <>
          {/* Pagination Bar - Above Table (Story 5-24) */}
          {/* Only show pagination when we have documents or are loading with existing data */}
          {(total > 0 || (isLoading && documentsForList.length > 0)) && (
            <DocumentPagination
              page={filters.page}
              totalPages={totalPages}
              total={total}
              limit={filters.limit}
              onPageChange={actions.setPage}
              onLimitChange={actions.setLimit}
              isLoading={isLoading}
            />
          )}

          <DocumentList
            documents={documentsForList}
            kbId={kbId}
            onRetry={handleRetry}
            onDocumentClick={handleDocumentClick}
            onDeleted={handleDocumentRemoved}
            showSort
            sortBy={filters.sortBy}
            sortOrder={filters.sortOrder}
            onSortByChange={actions.setSortBy}
            onSortOrderChange={actions.setSortOrder}
            isLoading={isLoading}
            total={total}
            canManage={canManage}
          />
        </>
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
