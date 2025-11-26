'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { RotateCwIcon, FileTextIcon, AlertCircleIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DocumentStatusBadge, type DocumentStatus } from './document-status-badge';
import { showDocumentStatusToast } from '@/lib/utils/document-toast';
import { cn } from '@/lib/utils';

interface DocumentDetail {
  id: string;
  kb_id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_path: string | null;
  checksum: string;
  status: DocumentStatus;
  chunk_count: number;
  processing_started_at: string | null;
  processing_completed_at: string | null;
  last_error: string | null;
  retry_count: number;
  uploaded_by: string | null;
  uploader_email: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentDetailModalProps {
  document: DocumentDetail | null;
  kbId: string;
  isOpen: boolean;
  onClose: () => void;
  onRetrySuccess?: () => void;
}

/**
 * Format bytes to human-readable size.
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
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
 * Modal component showing full document metadata.
 *
 * Features:
 * - All document metadata fields
 * - Processing duration for READY documents
 * - Full error message for FAILED documents
 * - Retry button for FAILED documents
 * - Relative and absolute timestamps
 */
export function DocumentDetailModal({
  document,
  kbId,
  isOpen,
  onClose,
  onRetrySuccess,
}: DocumentDetailModalProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  if (!document) return null;

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      const response = await fetch(
        `/api/v1/knowledge-bases/${kbId}/documents/${document.id}/retry`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (response.ok) {
        showDocumentStatusToast(document.name, 'retry');
        onRetrySuccess?.();
        onClose();
      }
    } catch (err) {
      console.error('Failed to retry document processing:', err);
    } finally {
      setIsRetrying(false);
    }
  };

  const duration = calculateDuration(
    document.processing_started_at,
    document.processing_completed_at
  );

  const uploadDate = new Date(document.created_at);
  const relativeDate = formatDistanceToNow(uploadDate, { addSuffix: true });

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileTextIcon className="size-5" />
            {document.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status Section */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Status</span>
            <DocumentStatusBadge
              status={document.status}
              errorMessage={document.last_error}
              chunkCount={document.status === 'READY' ? document.chunk_count : undefined}
            />
          </div>

          {/* Error Message for FAILED */}
          {document.status === 'FAILED' && document.last_error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3">
              <div className="flex items-start gap-2">
                <AlertCircleIcon className="mt-0.5 size-4 text-destructive" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">Processing Failed</p>
                  <p className="mt-1 text-sm text-muted-foreground">{document.last_error}</p>
                </div>
              </div>
              {document.retry_count > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Retry attempts: {document.retry_count}
                </p>
              )}
            </div>
          )}

          {/* Retry Button */}
          {document.status === 'FAILED' && (
            <Button onClick={handleRetry} disabled={isRetrying} className="w-full gap-2">
              <RotateCwIcon className={cn('size-4', isRetrying && 'animate-spin')} />
              Retry Processing
            </Button>
          )}

          {/* Metadata Grid */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Document Details</h4>

            <MetadataRow label="Original Filename">{document.original_filename}</MetadataRow>

            <MetadataRow label="MIME Type">{document.mime_type}</MetadataRow>

            <MetadataRow label="File Size">
              {formatBytes(document.file_size_bytes)} ({document.file_size_bytes.toLocaleString()}{' '}
              bytes)
            </MetadataRow>

            <MetadataRow label="Uploaded">
              {relativeDate}
              <span className="ml-1 text-xs text-muted-foreground">
                ({uploadDate.toLocaleString()})
              </span>
            </MetadataRow>

            <MetadataRow label="Uploaded By">{document.uploader_email || 'Unknown'}</MetadataRow>

            {document.status === 'READY' && (
              <>
                <MetadataRow label="Chunk Count">{document.chunk_count} chunks</MetadataRow>

                {duration !== null && (
                  <MetadataRow label="Processing Time">{duration}s</MetadataRow>
                )}
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function MetadataRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="shrink-0 text-sm text-muted-foreground">{label}</span>
      <span className="text-sm text-right">{children}</span>
    </div>
  );
}
