/**
 * Trace Pagination Component
 *
 * Story 9-8: Trace Viewer UI Component
 * Matches the document pagination style for UI consistency
 */
'use client';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface TracePaginationProps {
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

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

/**
 * Pagination component for trace lists.
 * Matches the document pagination style for UI consistency.
 *
 * Features:
 * - "Show X per page" selector
 * - "Showing X to Y of Z traces" display
 * - Previous/Next text buttons
 * - "Page X of Y" display
 */
export function TracePagination({
  page,
  totalPages,
  total,
  limit,
  onPageChange,
  onLimitChange,
  isLoading = false,
  className,
}: TracePaginationProps) {
  const startItem = total === 0 ? 0 : (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, total);

  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;
  const effectiveTotalPages = Math.max(1, totalPages);

  return (
    <div
      className={`flex items-center justify-between rounded-lg border bg-card px-4 py-3 ${className || ''}`}
      data-testid="trace-pagination"
    >
      {/* Left side: Page size selector and results info */}
      <div className="flex items-center gap-4">
        {/* Page Size Selector */}
        {onLimitChange && (
          <div className="flex items-center gap-2">
            <label htmlFor="trace-page-size" className="text-sm text-muted-foreground">
              Show
            </label>
            <Select
              value={limit.toString()}
              onValueChange={(value) => onLimitChange(parseInt(value, 10))}
              disabled={isLoading}
            >
              <SelectTrigger id="trace-page-size" className="w-[80px]" data-testid="trace-page-size-select">
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
        <p className="text-sm text-muted-foreground" data-testid="trace-pagination-info">
          {total === 0 ? (
            'No traces'
          ) : (
            <>
              Showing <span className="font-medium">{startItem}</span> to{' '}
              <span className="font-medium">{endItem}</span> of{' '}
              <span className="font-medium">{total}</span> traces
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
          data-testid="trace-previous-page-button"
        >
          Previous
        </Button>
        <span className="text-sm text-muted-foreground px-2" data-testid="trace-page-indicator">
          Page <span className="font-medium">{page}</span> of{' '}
          <span className="font-medium">{effectiveTotalPages}</span>
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={!canGoNext || isLoading}
          aria-label="Next page"
          data-testid="trace-next-page-button"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
