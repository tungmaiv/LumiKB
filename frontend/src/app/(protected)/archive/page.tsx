'use client';

import { useState, useMemo, useCallback } from 'react';
import {
  Archive,
  RotateCcw,
  Trash2,
  Search,
  CheckSquare,
  Square,
  AlertTriangle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  useArchivedDocuments,
  useRestoreDocument,
  usePurgeDocument,
  useBulkPurge,
} from '@/hooks/useArchive';
import { useKBStore } from '@/lib/stores/kb-store';
import { useDebounce } from '@/hooks/useDebounce';
import type { ArchivedDocument } from '@/types/archive';

const PAGE_SIZE = 20;

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatRelativeDate(dateString: string): string {
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
}

interface RestoreConfirmModalProps {
  document: ArchivedDocument | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
  error?: string | null;
}

function RestoreConfirmModal({
  document,
  isOpen,
  onClose,
  onConfirm,
  isLoading,
  error,
}: RestoreConfirmModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Restore Document</DialogTitle>
          <DialogDescription>
            Are you sure you want to restore &quot;{document?.name}&quot;?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            This document will be restored to the knowledge base &quot;{document?.kb_name}&quot; and
            will be searchable again.
          </p>

          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={isLoading}>
            {isLoading ? 'Restoring...' : 'Restore'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface PurgeConfirmModalProps {
  document: ArchivedDocument | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
  step: 'initial' | 'confirm';
  onStepChange: (step: 'initial' | 'confirm') => void;
}

function PurgeConfirmModal({
  document,
  isOpen,
  onClose,
  onConfirm,
  isLoading,
  step,
  onStepChange,
}: PurgeConfirmModalProps) {
  const handleClose = () => {
    onStepChange('initial');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">Permanently Delete Document</DialogTitle>
          <DialogDescription>
            {step === 'initial' ? 'This action cannot be undone.' : 'Are you absolutely sure?'}
          </DialogDescription>
        </DialogHeader>

        {step === 'initial' ? (
          <>
            <div className="space-y-3">
              <p className="text-sm">
                You are about to permanently delete &quot;{document?.name}&quot;.
              </p>
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  This will remove all associated data including chunks and embeddings. This action
                  cannot be undone.
                </AlertDescription>
              </Alert>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => onStepChange('confirm')}>
                Continue
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <div className="space-y-3">
              <p className="text-sm font-medium">Type the document name to confirm:</p>
              <p className="text-sm text-muted-foreground font-mono bg-muted p-2 rounded">
                {document?.name}
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={isLoading}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={onConfirm} disabled={isLoading}>
                {isLoading ? 'Deleting...' : 'Delete Permanently'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

interface BulkPurgeModalProps {
  selectedCount: number;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
  step: 'initial' | 'confirm';
  onStepChange: (step: 'initial' | 'confirm') => void;
}

function BulkPurgeModal({
  selectedCount,
  isOpen,
  onClose,
  onConfirm,
  isLoading,
  step,
  onStepChange,
}: BulkPurgeModalProps) {
  const handleClose = () => {
    onStepChange('initial');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">
            Permanently Delete {selectedCount} Documents
          </DialogTitle>
          <DialogDescription>
            {step === 'initial' ? 'This action cannot be undone.' : 'Are you absolutely sure?'}
          </DialogDescription>
        </DialogHeader>

        {step === 'initial' ? (
          <>
            <div className="space-y-3">
              <p className="text-sm">
                You are about to permanently delete {selectedCount} archived documents.
              </p>
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  This will remove all associated data including chunks and embeddings. This action
                  cannot be undone.
                </AlertDescription>
              </Alert>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => onStepChange('confirm')}>
                Continue
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <div className="space-y-3">
              <p className="text-sm font-medium">
                This will permanently delete {selectedCount} documents.
              </p>
              <p className="text-sm text-muted-foreground">
                Click &quot;Delete All&quot; to confirm.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={isLoading}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={onConfirm} disabled={isLoading}>
                {isLoading ? 'Deleting...' : 'Delete All'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function TableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-10" />
          <TableHead>Document Name</TableHead>
          <TableHead>Knowledge Base</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Archived</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {[1, 2, 3, 4, 5].map((i) => (
          <TableRow key={i}>
            <TableCell>
              <Skeleton className="h-4 w-4" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-48" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-32" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-16" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-4 w-24" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-8 w-24 ml-auto" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function ArchivePage() {
  // Filters
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 300);
  const [selectedKbId, setSelectedKbId] = useState<string>('all');
  const [page, setPage] = useState(1);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Modal states
  const [restoreDoc, setRestoreDoc] = useState<ArchivedDocument | null>(null);
  const [purgeDoc, setPurgeDoc] = useState<ArchivedDocument | null>(null);
  const [purgeStep, setPurgeStep] = useState<'initial' | 'confirm'>('initial');
  const [showBulkPurge, setShowBulkPurge] = useState(false);
  const [bulkPurgeStep, setBulkPurgeStep] = useState<'initial' | 'confirm'>('initial');
  const [restoreError, setRestoreError] = useState<string | null>(null);

  // Data fetching
  const kbs = useKBStore((state) => state.kbs);
  const { data, isLoading, error } = useArchivedDocuments({
    filters: {
      kb_id: selectedKbId === 'all' ? undefined : selectedKbId,
      search: debouncedSearch || undefined,
      page,
      page_size: PAGE_SIZE,
    },
  });

  // Mutations
  const restoreMutation = useRestoreDocument();
  const purgeMutation = usePurgeDocument();
  const bulkPurgeMutation = useBulkPurge();

  // Computed values
  const documents = data?.data ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const hasMore = data?.has_more ?? false;

  // Selection helpers
  const allSelected = documents.length > 0 && documents.every((d) => selectedIds.has(d.id));
  const someSelected = documents.some((d) => selectedIds.has(d.id));

  const toggleSelectAll = useCallback(() => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(documents.map((d) => d.id)));
    }
  }, [allSelected, documents]);

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // Group selected documents by KB for bulk operations
  const selectedByKb = useMemo(() => {
    const map = new Map<string, string[]>();
    documents
      .filter((d) => selectedIds.has(d.id))
      .forEach((d) => {
        const list = map.get(d.kb_id) ?? [];
        list.push(d.id);
        map.set(d.kb_id, list);
      });
    return map;
  }, [documents, selectedIds]);

  // Handlers
  const handleRestore = (doc: ArchivedDocument) => {
    setRestoreError(null);
    setRestoreDoc(doc);
  };

  const handleConfirmRestore = async () => {
    if (!restoreDoc) return;

    try {
      await restoreMutation.mutateAsync({
        kbId: restoreDoc.kb_id,
        documentId: restoreDoc.id,
      });
      setRestoreDoc(null);
    } catch (error) {
      const err = error as Error & { status?: number; conflictingDocumentId?: string };
      if (err.status === 409) {
        setRestoreError(
          'A document with this name already exists in the knowledge base. Please archive or delete the existing document first.'
        );
      } else {
        setRestoreError(err.message);
      }
    }
  };

  const handlePurge = (doc: ArchivedDocument) => {
    setPurgeStep('initial');
    setPurgeDoc(doc);
  };

  const handleConfirmPurge = async () => {
    if (!purgeDoc) return;

    await purgeMutation.mutateAsync({
      kbId: purgeDoc.kb_id,
      documentId: purgeDoc.id,
    });
    setPurgeDoc(null);
    setPurgeStep('initial');
  };

  const handleBulkPurge = () => {
    setBulkPurgeStep('initial');
    setShowBulkPurge(true);
  };

  const handleConfirmBulkPurge = async () => {
    // Execute bulk purge for each KB
    for (const [kbId, docIds] of selectedByKb) {
      await bulkPurgeMutation.mutateAsync({
        kbId,
        documentIds: docIds,
      });
    }
    setShowBulkPurge(false);
    setBulkPurgeStep('initial');
    setSelectedIds(new Set());
  };

  // Reset page when filters change
  const handleKbChange = (value: string) => {
    setSelectedKbId(value);
    setPage(1);
    setSelectedIds(new Set());
  };

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    setPage(1);
    setSelectedIds(new Set());
  };

  return (
    <div className="container py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Archive className="h-6 w-6 text-muted-foreground" />
          <div>
            <h1 className="text-2xl font-bold">Archive</h1>
            <p className="text-sm text-muted-foreground">
              Manage archived documents across all knowledge bases
            </p>
          </div>
        </div>

        {selectedIds.size > 0 && (
          <Button variant="destructive" onClick={handleBulkPurge} className="gap-2">
            <Trash2 className="h-4 w-4" />
            Delete {selectedIds.size} Selected
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by document name..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={selectedKbId} onValueChange={handleKbChange}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Knowledge Bases" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Knowledge Bases</SelectItem>
            {kbs.map((kb) => (
              <SelectItem key={kb.id} value={kb.id}>
                {kb.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        {isLoading ? (
          <TableSkeleton />
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-destructive">{error.message}</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center">
            <Archive className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium mb-2">No archived documents</h3>
            <p className="text-sm text-muted-foreground">
              {debouncedSearch || selectedKbId !== 'all'
                ? 'Try adjusting your filters'
                : 'Archived documents will appear here'}
            </p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={toggleSelectAll}
                      aria-label="Select all"
                      className={someSelected && !allSelected ? 'opacity-50' : ''}
                    />
                  </TableHead>
                  <TableHead>Document Name</TableHead>
                  <TableHead>Knowledge Base</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Archived</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(doc.id)}
                        onCheckedChange={() => toggleSelect(doc.id)}
                        aria-label={`Select ${doc.name}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <span className="font-medium">{doc.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {doc.original_filename}
                          </span>
                          {doc.tags.length > 0 && (
                            <div className="flex gap-1">
                              {doc.tags.slice(0, 2).map((tag) => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                              {doc.tags.length > 2 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{doc.tags.length - 2}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{doc.kb_name}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {formatBytes(doc.file_size_bytes)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {formatRelativeDate(doc.archived_at)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRestore(doc)}
                          className="gap-1"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Restore
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePurge(doc)}
                          className="gap-1 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * PAGE_SIZE + 1} to {Math.min(page * PAGE_SIZE, total)} of{' '}
                  {total} documents
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasMore}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Restore Confirmation Modal */}
      <RestoreConfirmModal
        document={restoreDoc}
        isOpen={!!restoreDoc}
        onClose={() => {
          setRestoreDoc(null);
          setRestoreError(null);
        }}
        onConfirm={handleConfirmRestore}
        isLoading={restoreMutation.isPending}
        error={restoreError}
      />

      {/* Purge Confirmation Modal (Two-step) */}
      <PurgeConfirmModal
        document={purgeDoc}
        isOpen={!!purgeDoc}
        onClose={() => {
          setPurgeDoc(null);
          setPurgeStep('initial');
        }}
        onConfirm={handleConfirmPurge}
        isLoading={purgeMutation.isPending}
        step={purgeStep}
        onStepChange={setPurgeStep}
      />

      {/* Bulk Purge Modal (Two-step) */}
      <BulkPurgeModal
        selectedCount={selectedIds.size}
        isOpen={showBulkPurge}
        onClose={() => {
          setShowBulkPurge(false);
          setBulkPurgeStep('initial');
        }}
        onConfirm={handleConfirmBulkPurge}
        isLoading={bulkPurgeMutation.isPending}
        step={bulkPurgeStep}
        onStepChange={setBulkPurgeStep}
      />
    </div>
  );
}
