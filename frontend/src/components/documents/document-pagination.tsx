'use client';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface DocumentPaginationProps {
  /** Current page number (1-indexed) */
  page: number;
  /** Total number of pages */
  totalPages: number;
  /** Total number of items */
  total: number;
  /** Items per page */
  limit: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
  /** Callback when limit changes */
  onLimitChange?: (limit: number) => void;
  /** Whether data is loading */
  isLoading?: boolean;
  className?: string;
}

const PAGE_SIZE_OPTIONS = [10, 20, 25, 50, 100];

/**
 * Pagination component for document lists.
 * Matches the audit log pagination style for UI consistency.
 *
 * Features:
 * - "Show X per page" selector
 * - "Showing X to Y of Z documents" display
 * - Previous/Next text buttons
 * - "Page X of Y" display
 */
export function DocumentPagination({
  page,
  totalPages,
  total,
  limit,
  onPageChange,
  onLimitChange,
  isLoading = false,
  className,
}: DocumentPaginationProps) {
  const startItem = total === 0 ? 0 : (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, total);

  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;
  const effectiveTotalPages = Math.max(1, totalPages);

  return (
    <div
      className={`flex items-center justify-between rounded-lg border bg-card px-4 py-3 ${className || ''}`}
      data-testid="document-pagination"
    >
      {/* Left side: Page size selector and results info */}
      <div className="flex items-center gap-4">
        {/* Page Size Selector */}
        {onLimitChange && (
          <div className="flex items-center gap-2">
            <label htmlFor="doc-page-size" className="text-sm text-muted-foreground">
              Show
            </label>
            <Select
              value={limit.toString()}
              onValueChange={(value) => onLimitChange(parseInt(value, 10))}
              disabled={isLoading}
            >
              <SelectTrigger id="doc-page-size" className="w-[80px]" data-testid="page-size-select">
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
        )}

        {/* Results Info */}
        <p className="text-sm text-muted-foreground" data-testid="pagination-info">
          {total === 0 ? (
            'No documents'
          ) : (
            <>
              Showing <span className="font-medium">{startItem}</span> to{' '}
              <span className="font-medium">{endItem}</span> of{' '}
              <span className="font-medium">{total}</span> documents
            </>
          )}
        </p>
      </div>

      {/* Right side: Pagination Controls */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={!canGoPrevious || isLoading}
          aria-label="Previous page"
          data-testid="previous-page-button"
        >
          Previous
        </Button>
        <span className="text-sm text-muted-foreground px-2" data-testid="page-indicator">
          Page <span className="font-medium">{page}</span> of{' '}
          <span className="font-medium">{effectiveTotalPages}</span>
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={!canGoNext || isLoading}
          aria-label="Next page"
          data-testid="next-page-button"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
