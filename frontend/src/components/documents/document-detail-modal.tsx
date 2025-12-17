'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  RotateCwIcon,
  FileTextIcon,
  AlertCircleIcon,
  TagIcon,
  PencilIcon,
  LayersIcon,
  ActivityIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentStatusBadge, type DocumentStatus } from './document-status-badge';
import { DocumentTagsDisplay } from './document-tag-input';
import { DocumentEditTagsModal } from './document-edit-tags-modal';
import { SimpleChunkList } from './chunk-viewer/simple-chunk-list';
import { showDocumentStatusToast } from '@/lib/utils/document-toast';
import { cn } from '@/lib/utils';
import { ProcessingTimeline } from '@/components/admin/documents/processing-timeline';

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
  tags?: string[];
}

interface DocumentDetailModalProps {
  document: DocumentDetail | null;
  kbId: string;
  isOpen: boolean;
  onClose: () => void;
  onRetrySuccess?: () => void;
  onTagsUpdated?: (documentId: string, newTags: string[]) => void;
  /** Whether the user can edit tags (requires WRITE or ADMIN permission) */
  canEditTags?: boolean;
  /** Whether the user is an admin (shows processing timeline tab) */
  isAdmin?: boolean;
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
  onTagsUpdated,
  canEditTags = false,
  isAdmin = false,
}: DocumentDetailModalProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [showEditTagsModal, setShowEditTagsModal] = useState(false);
  const [localTags, setLocalTags] = useState<string[]>(document?.tags || []);

  // Sync local tags when document changes
  if (document && document.tags && localTags !== document.tags) {
    setLocalTags(document.tags);
  }

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

  // Determine if chunk viewer should be available (only for READY documents)
  const canViewChunks = document.status === 'READY' && document.chunk_count > 0;

  // Determine if we need tabs (chunks available or admin can view processing timeline)
  const showTabs = canViewChunks || isAdmin;

  // Calculate number of tab columns
  const tabCount = 1 + (canViewChunks ? 1 : 0) + (isAdmin ? 1 : 0);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={cn('max-w-lg transition-all duration-200', showTabs && 'max-w-2xl max-h-[85vh]')}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileTextIcon className="size-5" />
            {document.name}
          </DialogTitle>
        </DialogHeader>

        {showTabs ? (
          <Tabs defaultValue="details" className="flex-1 flex flex-col min-h-0">
            <TabsList className={`grid w-full grid-cols-${tabCount}`}>
              <TabsTrigger value="details" className="gap-2">
                <FileTextIcon className="size-4" />
                Details
              </TabsTrigger>
              {canViewChunks && (
                <TabsTrigger value="chunks" className="gap-2">
                  <LayersIcon className="size-4" />
                  Chunks ({document.chunk_count})
                </TabsTrigger>
              )}
              {isAdmin && (
                <TabsTrigger value="processing" className="gap-2" data-testid="processing-tab">
                  <ActivityIcon className="size-4" />
                  Processing
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="details" className="flex-1 overflow-auto">
              <DocumentDetailsContent
                document={document}
                duration={duration}
                relativeDate={relativeDate}
                uploadDate={uploadDate}
                localTags={localTags}
                canEditTags={canEditTags}
                isRetrying={isRetrying}
                onRetry={handleRetry}
                onEditTags={() => setShowEditTagsModal(true)}
              />
            </TabsContent>

            {canViewChunks && (
              <TabsContent value="chunks" className="flex-1 min-h-0 overflow-hidden">
                <SimpleChunkList kbId={kbId} documentId={document.id} />
              </TabsContent>
            )}

            {isAdmin && (
              <TabsContent value="processing" className="flex-1 overflow-auto">
                <ProcessingTimeline documentId={document.id} />
              </TabsContent>
            )}
          </Tabs>
        ) : (
          <DocumentDetailsContent
            document={document}
            duration={duration}
            relativeDate={relativeDate}
            uploadDate={uploadDate}
            localTags={localTags}
            canEditTags={canEditTags}
            isRetrying={isRetrying}
            onRetry={handleRetry}
            onEditTags={() => setShowEditTagsModal(true)}
          />
        )}
      </DialogContent>

      {/* Edit Tags Modal */}
      <DocumentEditTagsModal
        open={showEditTagsModal}
        onOpenChange={setShowEditTagsModal}
        kbId={kbId}
        documentId={document.id}
        documentName={document.name}
        currentTags={localTags}
        onTagsUpdated={(newTags) => {
          setLocalTags(newTags);
          onTagsUpdated?.(document.id, newTags);
        }}
      />
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

/**
 * Document details content extracted for reuse in both tabbed and non-tabbed views.
 */
interface DocumentDetailsContentProps {
  document: DocumentDetail;
  duration: number | null;
  relativeDate: string;
  uploadDate: Date;
  localTags: string[];
  canEditTags: boolean;
  isRetrying: boolean;
  onRetry: () => void;
  onEditTags: () => void;
}

function DocumentDetailsContent({
  document,
  duration,
  relativeDate,
  uploadDate,
  localTags,
  canEditTags,
  isRetrying,
  onRetry,
  onEditTags,
}: DocumentDetailsContentProps) {
  return (
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
        <Button onClick={onRetry} disabled={isRetrying} className="w-full gap-2">
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

            {duration !== null && <MetadataRow label="Processing Time">{duration}s</MetadataRow>}
          </>
        )}
      </div>

      {/* Tags Section */}
      <div className="space-y-2 pt-2 border-t">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium flex items-center gap-1.5">
            <TagIcon className="size-4" />
            Tags
          </h4>
          {canEditTags && (
            <Button variant="ghost" size="sm" className="h-7 gap-1" onClick={onEditTags}>
              <PencilIcon className="size-3" />
              Edit
            </Button>
          )}
        </div>
        {localTags.length > 0 ? (
          <DocumentTagsDisplay tags={localTags} maxVisible={10} />
        ) : (
          <p className="text-sm text-muted-foreground">No tags</p>
        )}
      </div>
    </div>
  );
}
