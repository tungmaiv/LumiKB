'use client';

import { useState, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  RotateCwIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowUpDownIcon,
  InfoIcon,
  TrashIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DocumentStatusBadge, type DocumentStatus } from './document-status-badge';
import { DeleteConfirmDialog } from './delete-confirm-dialog';
import { useDocumentStatusPolling } from '@/lib/hooks/use-document-status-polling';
import { showDocumentStatusToast } from '@/lib/utils/document-toast';
import { cn } from '@/lib/utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type SortField = 'name' | 'created_at' | 'file_size_bytes' | 'status';
export type SortOrder = 'asc' | 'desc';

interface Document {
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

interface DocumentListItemProps {
  document: Document;
  kbId: string;
  onRetry?: (documentId: string) => void;
  onClick?: () => void;
  onDeleted?: (documentId: string) => void;
}

/**
 * Format bytes to human-readable size.
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Calculate processing duration in seconds.
 */
function calculateDuration(
  startedAt: string | null | undefined,
  completedAt: string | null | undefined
): number | null {
  if (!startedAt || !completedAt) return null;
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  return Math.round((end - start) / 1000);
}

/**
 * Format relative date with fallback.
 */
function formatRelativeDate(dateString: string): string {
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
}

/**
 * Single document row with status polling.
 */
function DocumentListItem({ document, kbId, onRetry, onClick, onDeleted }: DocumentListItemProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [localStatus, setLocalStatus] = useState<DocumentStatus>(document.status);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleStatusChange = useCallback(
    (newStatus: DocumentStatus) => {
      setLocalStatus(newStatus);
      if (newStatus === 'READY') {
        showDocumentStatusToast(document.name, 'ready');
      } else if (newStatus === 'FAILED') {
        showDocumentStatusToast(document.name, 'failed');
      }
    },
    [document.name]
  );

  const { status, chunkCount, error, isPolling } = useDocumentStatusPolling(
    document.id,
    kbId,
    localStatus,
    { onStatusChange: handleStatusChange }
  );

  const handleRetry = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRetrying(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${document.id}/retry`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (response.ok) {
        showDocumentStatusToast(document.name, 'retry');
        setLocalStatus('PENDING');
        onRetry?.(document.id);
      }
    } catch (err) {
      console.error('Failed to retry document processing:', err);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleClick = () => {
    onClick?.();
  };

  const duration = calculateDuration(
    document.processing_started_at,
    document.processing_completed_at
  );

  const relativeDate = formatRelativeDate(document.created_at);

  return (
    <div
      className={cn(
        'flex items-center justify-between border-b px-4 py-3',
        'hover:bg-muted/50 transition-colors cursor-pointer'
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      <div className="flex flex-col gap-1 min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{document.name}</span>
          <span className="text-xs text-muted-foreground shrink-0">
            ({formatBytes(document.file_size_bytes)})
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
          <span className="truncate">{document.original_filename}</span>
          <span className="shrink-0">{relativeDate}</span>
          {document.uploader_email && (
            <span className="shrink-0">by {document.uploader_email}</span>
          )}
          {status === 'READY' && duration !== null && (
            <span className="shrink-0">Processed in {duration}s</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0 ml-4">
        <DocumentStatusBadge
          status={status}
          errorMessage={error}
          chunkCount={status === 'READY' ? chunkCount : undefined}
          versionNumber={document.version_number}
        />

        {status === 'FAILED' && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
            disabled={isRetrying}
            className="gap-1"
          >
            <RotateCwIcon className={cn('size-3.5', isRetrying && 'animate-spin')} />
            Retry
          </Button>
        )}

        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
          title="View details"
        >
          <InfoIcon className="size-4" />
        </Button>

        {/* Delete button - disabled when processing */}
        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground hover:text-destructive"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteDialog(true);
          }}
          disabled={status === 'PROCESSING'}
          title={status === 'PROCESSING' ? 'Cannot delete while processing' : 'Delete document'}
        >
          <TrashIcon className="size-4" />
        </Button>

        {isPolling && (
          <span className="text-xs text-muted-foreground animate-pulse">Checking...</span>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        documentName={document.name}
        documentId={document.id}
        kbId={kbId}
        onDeleted={() => {
          showDocumentStatusToast(document.name, 'delete-success');
          onDeleted?.(document.id);
        }}
        onError={(error) => {
          showDocumentStatusToast(document.name, 'delete-error', error);
        }}
      />
    </div>
  );
}

/**
 * Pagination controls component.
 */
function PaginationControls({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  return (
    <div className="flex items-center justify-center gap-2 py-3 border-t">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        <ChevronLeftIcon className="size-4" />
        Previous
      </Button>
      <span className="text-sm text-muted-foreground px-2">
        Page {page} of {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
        <ChevronRightIcon className="size-4" />
      </Button>
    </div>
  );
}

/**
 * Sort controls component.
 */
function SortControls({
  sortBy,
  sortOrder,
  onSortByChange,
  onSortOrderChange,
}: {
  sortBy: SortField;
  sortOrder: SortOrder;
  onSortByChange: (field: SortField) => void;
  onSortOrderChange: (order: SortOrder) => void;
}) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30">
      <ArrowUpDownIcon className="size-4 text-muted-foreground" />
      <span className="text-sm text-muted-foreground">Sort by:</span>
      <Select value={sortBy} onValueChange={onSortByChange}>
        <SelectTrigger className="w-[140px] h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created_at">Date uploaded</SelectItem>
          <SelectItem value="name">Name</SelectItem>
          <SelectItem value="file_size_bytes">File size</SelectItem>
          <SelectItem value="status">Status</SelectItem>
        </SelectContent>
      </Select>
      <Select value={sortOrder} onValueChange={onSortOrderChange}>
        <SelectTrigger className="w-[100px] h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="desc">Newest</SelectItem>
          <SelectItem value="asc">Oldest</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

interface DocumentListProps {
  /** Documents to display */
  documents: Document[];
  /** Knowledge base ID */
  kbId: string;
  /** Called when a document is retried */
  onRetry?: (documentId: string) => void;
  /** Called when a document is clicked */
  onDocumentClick?: (document: Document) => void;
  /** Called when a document is deleted */
  onDeleted?: (documentId: string) => void;
  /** Additional CSS classes */
  className?: string;
  /** Enable pagination UI */
  showPagination?: boolean;
  /** Current page number */
  page?: number;
  /** Total number of pages */
  totalPages?: number;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
  /** Enable sorting UI */
  showSort?: boolean;
  /** Current sort field */
  sortBy?: SortField;
  /** Current sort order */
  sortOrder?: SortOrder;
  /** Callback when sort field changes */
  onSortByChange?: (field: SortField) => void;
  /** Callback when sort order changes */
  onSortOrderChange?: (order: SortOrder) => void;
  /** Show loading skeleton */
  isLoading?: boolean;
  /** Total document count for display */
  total?: number;
}

/**
 * DocumentList displays a list of documents with their processing status.
 *
 * Features:
 * - Status badges for each document (PENDING, PROCESSING, READY, FAILED)
 * - Automatic status polling for PROCESSING documents
 * - Toast notifications when processing completes
 * - Retry button for FAILED documents
 * - Processing duration display for READY documents
 * - Chunk count display for indexed documents
 * - Pagination controls
 * - Sort controls (by name, date, size, status)
 * - Uploader info and relative dates
 * - Click to view details
 *
 * @example
 * <DocumentList
 *   documents={documents}
 *   kbId={kbId}
 *   onRetry={(docId) => console.log('Retrying:', docId)}
 *   showPagination
 *   page={1}
 *   totalPages={5}
 *   onPageChange={(p) => setPage(p)}
 * />
 */
export function DocumentList({
  documents,
  kbId,
  onRetry,
  onDocumentClick,
  onDeleted,
  className,
  showPagination = false,
  page = 1,
  totalPages = 1,
  onPageChange,
  showSort = false,
  sortBy = 'created_at',
  sortOrder = 'desc',
  onSortByChange,
  onSortOrderChange,
  isLoading = false,
  total,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className={cn('rounded-md border', className)}>
        {showSort && (
          <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30">
            <div className="h-4 w-32 bg-muted animate-pulse rounded" />
          </div>
        )}
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between border-b px-4 py-3">
            <div className="space-y-2">
              <div className="h-4 w-48 bg-muted animate-pulse rounded" />
              <div className="h-3 w-32 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-6 w-20 bg-muted animate-pulse rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className={cn('py-8 text-center text-muted-foreground', className)}>
        No documents uploaded yet
      </div>
    );
  }

  return (
    <div className={cn('rounded-md border', className)}>
      {showSort && onSortByChange && onSortOrderChange && (
        <SortControls
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortByChange={onSortByChange}
          onSortOrderChange={onSortOrderChange}
        />
      )}

      {total !== undefined && (
        <div className="px-4 py-2 text-xs text-muted-foreground border-b">
          {total} document{total !== 1 ? 's' : ''}
        </div>
      )}

      {documents.map((doc) => (
        <DocumentListItem
          key={doc.id}
          document={doc}
          kbId={kbId}
          onRetry={onRetry}
          onClick={() => onDocumentClick?.(doc)}
          onDeleted={onDeleted}
        />
      ))}

      {showPagination && totalPages > 1 && onPageChange && (
        <PaginationControls page={page} totalPages={totalPages} onPageChange={onPageChange} />
      )}
    </div>
  );
}
