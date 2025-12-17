/**
 * Processing tab component
 * Story 5-23: Main container for document processing progress view
 *
 * Follows the same UI pattern as DocumentsPanel with search and pagination bar.
 */

'use client';

import { useState, useCallback } from 'react';
import { RefreshCw, Loader2, Search, X, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { DocumentProcessingTable } from './document-processing-table';
import { ProcessingDetailsModal } from './processing-details-modal';
import { useDocumentProcessing } from '@/hooks/useDocumentProcessing';
import type { ProcessingFilters, DocumentStatus, ProcessingStep } from '@/types/processing';
import { DOC_STATUS_LABELS, STEP_LABELS, PROCESSING_STEPS_ORDER } from '@/types/processing';
import { useDebounce } from '@/hooks/useDebounce';

const PAGE_SIZE_OPTIONS = [10, 20, 25, 50, 100];
const DOCUMENT_STATUSES: DocumentStatus[] = ['pending', 'processing', 'ready', 'failed'];

export interface ProcessingTabProps {
  /** Knowledge Base ID */
  kbId: string;
}

export function ProcessingTab({ kbId }: ProcessingTabProps) {
  // Filter state
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [status, setStatus] = useState<DocumentStatus | undefined>(undefined);
  const [currentStep, setCurrentStep] = useState<ProcessingStep | undefined>(undefined);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Selected document for details modal
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const debouncedSearch = useDebounce(searchInput, 300);

  // Build filters object
  const filters: ProcessingFilters = {
    name: debouncedSearch || undefined,
    status,
    current_step: currentStep,
    page,
    page_size: pageSize,
  };

  // Fetch documents with processing status
  const { data, isLoading, isFetching, refetch } = useDocumentProcessing({
    kbId,
    filters,
    autoRefresh: true, // AC-5.23.5: 10-second auto-refresh
  });

  // Count active filters (excluding search)
  const activeFilterCount = [status, currentStep].filter(Boolean).length;

  // Handle search change
  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value);
    setPage(1);
  }, []);

  const handleClearSearch = useCallback(() => {
    setSearchInput('');
    setPage(1);
  }, []);

  // Handle page size change
  const handlePageSizeChange = useCallback((value: string) => {
    setPageSize(parseInt(value, 10));
    setPage(1);
  }, []);

  // Handle status change
  const handleStatusChange = useCallback((value: string) => {
    setStatus(value === 'all' ? undefined : (value as DocumentStatus));
    setPage(1);
  }, []);

  // Handle step change
  const handleStepChange = useCallback((value: string) => {
    setCurrentStep(value === 'all' ? undefined : (value as ProcessingStep));
    setPage(1);
  }, []);

  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    setSearchInput('');
    setStatus(undefined);
    setCurrentStep(undefined);
    setPage(1);
  }, []);

  // Handle document click - open details modal
  const handleDocumentClick = useCallback((docId: string) => {
    setSelectedDocId(docId);
    setIsModalOpen(true);
  }, []);

  // Handle modal close
  const handleModalClose = useCallback(() => {
    setIsModalOpen(false);
    // Clear selected doc after animation
    setTimeout(() => setSelectedDocId(null), 200);
  }, []);

  // Manual refresh
  const handleManualRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Pagination calculations
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize) || 1;
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);
  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;

  const hasActiveFilters = !!searchInput || !!status || !!currentStep;

  return (
    <div className="space-y-4">
      {/* Filter Bar - Matches DocumentFilterBar pattern */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search input */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search documents..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 pr-9"
            data-testid="processing-search-input"
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

        {/* Status filter */}
        <Select value={status || 'all'} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-[140px]" data-testid="status-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            {DOCUMENT_STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {DOC_STATUS_LABELS[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Advanced filters toggle */}
        <Button
          variant={showAdvanced ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="gap-2"
          data-testid="advanced-filters-toggle"
        >
          <Filter className="h-4 w-4" />
          Advanced
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1 h-5 w-5 rounded-full p-0 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>

        {/* Clear filters button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetFilters}
            className="text-muted-foreground hover:text-foreground"
            data-testid="clear-filters-button"
          >
            <X className="mr-1 h-4 w-4" />
            Clear filters
          </Button>
        )}

        {/* Manual Refresh Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleManualRefresh}
          disabled={isFetching}
          className="ml-auto"
        >
          {isFetching ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {/* Advanced filters panel */}
      {showAdvanced && (
        <div
          className="rounded-lg border bg-muted/30 p-4 space-y-4"
          data-testid="advanced-filters-panel"
        >
          <div className="flex flex-wrap items-center gap-4">
            {/* Processing Step Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Processing Step:</span>
              <Select value={currentStep || 'all'} onValueChange={handleStepChange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All steps" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All steps</SelectItem>
                  {PROCESSING_STEPS_ORDER.map((step) => (
                    <SelectItem key={step} value={step}>
                      {STEP_LABELS[step]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Active filters summary */}
          {hasActiveFilters && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {searchInput && (
                <Badge variant="secondary" className="gap-1">
                  Search: &quot;{searchInput}&quot;
                  <button onClick={handleClearSearch} className="hover:text-foreground">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {status && (
                <Badge variant="secondary" className="gap-1">
                  Status: {DOC_STATUS_LABELS[status]}
                  <button onClick={() => setStatus(undefined)} className="hover:text-foreground">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {currentStep && (
                <Badge variant="secondary" className="gap-1">
                  Step: {STEP_LABELS[currentStep]}
                  <button
                    onClick={() => setCurrentStep(undefined)}
                    className="hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
            </div>
          )}
        </div>
      )}

      {/* Pagination Bar - Matches DocumentPagination pattern */}
      {(total > 0 || isLoading) && (
        <div
          className="flex items-center justify-between rounded-lg border bg-card px-4 py-3"
          data-testid="processing-pagination"
        >
          {/* Left side: Page size selector and results info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="processing-page-size" className="text-sm text-muted-foreground">
                Show
              </label>
              <Select
                value={pageSize.toString()}
                onValueChange={handlePageSizeChange}
                disabled={isLoading}
              >
                <SelectTrigger
                  id="processing-page-size"
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

      {/* Document Table - AC-5.23.1 */}
      <DocumentProcessingTable
        documents={data?.documents || []}
        total={total}
        page={page}
        pageSize={pageSize}
        isLoading={isLoading}
        onPageChange={setPage}
        onDocumentClick={handleDocumentClick}
        hidePagination // We handle pagination above
      />

      {/* Auto-refresh indicator */}
      {isFetching && !isLoading && (
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Updating...</span>
        </div>
      )}

      {/* Details Modal - AC-5.23.3 */}
      <ProcessingDetailsModal
        kbId={kbId}
        docId={selectedDocId}
        isOpen={isModalOpen}
        onClose={handleModalClose}
      />
    </div>
  );
}
