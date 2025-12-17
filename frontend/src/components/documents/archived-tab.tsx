'use client';

/**
 * ArchivedTab - Displays archived documents for a KB with restore/purge actions
 * Follows the same UI pattern as DocumentsPanel with search and pagination
 */

import { useState, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Archive, RotateCcw, Trash2, Search, FileText, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  useKBArchivedDocuments,
  useRestoreArchivedDocument,
  usePurgeArchivedDocument,
  type ArchivedDocumentItem,
} from '@/hooks/useKBArchivedDocuments';
import { useDebounce } from '@/hooks/useDebounce';

interface ArchivedTabProps {
  kbId: string;
}

const PAGE_SIZE_OPTIONS = [10, 20, 25, 50, 100];

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ArchivedTab({ kbId }: ArchivedTabProps) {
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'restore' | 'purge';
    document: ArchivedDocumentItem;
  } | null>(null);

  const debouncedSearch = useDebounce(searchInput, 300);

  const { data, isLoading, error } = useKBArchivedDocuments({
    kbId,
    search: debouncedSearch || undefined,
    page,
    pageSize,
  });

  const restoreMutation = useRestoreArchivedDocument(kbId);
  const purgeMutation = usePurgeArchivedDocument(kbId);

  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value);
    setPage(1); // Reset to first page on search
  }, []);

  const handleClearSearch = useCallback(() => {
    setSearchInput('');
    setPage(1);
  }, []);

  const handlePageSizeChange = useCallback((value: string) => {
    setPageSize(parseInt(value, 10));
    setPage(1); // Reset to first page on page size change
  }, []);

  const handleRestore = async () => {
    if (!confirmAction || confirmAction.type !== 'restore') return;
    await restoreMutation.mutateAsync(confirmAction.document.id);
    setConfirmAction(null);
  };

  const handlePurge = async () => {
    if (!confirmAction || confirmAction.type !== 'purge') return;
    await purgeMutation.mutateAsync(confirmAction.document.id);
    setConfirmAction(null);
  };

  // Pagination calculations
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize) || 1;
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);
  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Archive className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <p className="text-muted-foreground">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar - Matches DocumentFilterBar pattern */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search input */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search archived documents..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 pr-9"
            data-testid="archived-search-input"
          />
          {searchInput && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Pagination Bar - Matches DocumentPagination pattern */}
      {(total > 0 || isLoading) && (
        <div
          className="flex items-center justify-between rounded-lg border bg-card px-4 py-3"
          data-testid="archived-pagination"
        >
          {/* Left side: Page size selector and results info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="archived-page-size" className="text-sm text-muted-foreground">
                Show
              </label>
              <Select
                value={pageSize.toString()}
                onValueChange={handlePageSizeChange}
                disabled={isLoading}
              >
                <SelectTrigger
                  id="archived-page-size"
                  className="w-[80px]"
                  data-testid="page-size-select"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <SelectItem key={size} value={size.toString()}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-sm text-muted-foreground">per page</span>
            </div>

            {/* Results Info */}
            <p className="text-sm text-muted-foreground" data-testid="pagination-info">
              {total === 0 ? (
                'No archived documents'
              ) : (
                <>
                  Showing <span className="font-medium">{startItem}</span> to{' '}
                  <span className="font-medium">{endItem}</span> of{' '}
                  <span className="font-medium">{total}</span> archived documents
                </>
              )}
            </p>
          </div>

          {/* Right side: Pagination Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!canGoPrevious || isLoading}
              aria-label="Previous page"
              data-testid="previous-page-button"
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground px-2" data-testid="page-indicator">
              Page <span className="font-medium">{page}</span> of{' '}
              <span className="font-medium">{totalPages}</span>
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!canGoNext || isLoading}
              aria-label="Next page"
              data-testid="next-page-button"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !data?.data.length ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Archive className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-1">No archived documents</h3>
          <p className="text-sm text-muted-foreground">
            {searchInput
              ? 'No documents match your search.'
              : 'Archived documents will appear here.'}
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Document</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Archived</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.data.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium truncate max-w-[300px]">{doc.name}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[300px]">
                          {doc.original_filename}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatFileSize(doc.file_size_bytes)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(doc.archived_at), { addSuffix: true })}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setConfirmAction({ type: 'restore', document: doc })}
                        disabled={restoreMutation.isPending || purgeMutation.isPending}
                      >
                        <RotateCcw className="h-4 w-4 mr-1" />
                        Restore
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setConfirmAction({ type: 'purge', document: doc })}
                        disabled={restoreMutation.isPending || purgeMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Restore Confirmation Dialog */}
      <AlertDialog
        open={confirmAction?.type === 'restore'}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Restore Document</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to restore &quot;{confirmAction?.document.name}&quot;? The
              document will be moved back to the active documents list.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRestore} disabled={restoreMutation.isPending}>
              {restoreMutation.isPending ? 'Restoring...' : 'Restore'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Purge Confirmation Dialog */}
      <AlertDialog
        open={confirmAction?.type === 'purge'}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Permanently Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently delete &quot;{confirmAction?.document.name}
              &quot;? This action cannot be undone. All document data and vectors will be removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handlePurge}
              disabled={purgeMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {purgeMutation.isPending ? 'Deleting...' : 'Delete Permanently'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
