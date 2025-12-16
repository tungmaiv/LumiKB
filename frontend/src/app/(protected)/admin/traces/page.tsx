/**
 * Trace Viewer Page
 *
 * Story 9-8: Trace Viewer UI Component
 * AC8: Responsive design for admin dashboard integration
 */
'use client';

import { useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { useTraces } from '@/hooks/useTraces';

import {
  TraceList,
  TraceFiltersComponent,
  TraceDetailPanel,
  TracePagination,
  type TraceFilters,
} from '@/components/admin/traces';

const DEFAULT_PAGE_SIZE = 20;

export default function TracesPage() {
  const [filters, setFilters] = useState<TraceFilters>({});
  const [currentPage, setCurrentPage] = useState(1); // 1-indexed to match DocumentPagination
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  const { data, isLoading, error, refetch, isRefetching } = useTraces({
    ...filters,
    skip: (currentPage - 1) * pageSize, // Convert to 0-indexed skip
    limit: pageSize,
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  // Reset page when filters change
  const handleFilterChange = (newFilters: TraceFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  // Reset page when page size changes
  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1);
  };

  // Handle trace selection
  const handleSelectTrace = (traceId: string) => {
    setSelectedTraceId(traceId);
  };

  // Handle panel close
  const handleCloseDetail = () => {
    setSelectedTraceId(null);
  };

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-8 w-8" />
            <div>
              <h1 className="text-2xl font-bold">Traces</h1>
              <p className="text-sm text-muted-foreground">
                View and analyze distributed traces across the system
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Main content card */}
        <Card>
          <CardHeader className="pb-0">
            <CardTitle>Trace List</CardTitle>
            <CardDescription>
              {isLoading ? (
                <Skeleton className="h-4 w-32" />
              ) : (
                `${data?.total || 0} traces found`
              )}
            </CardDescription>
          </CardHeader>

          {/* Filters */}
          <TraceFiltersComponent
            filters={filters}
            onFilterChange={handleFilterChange}
          />

          <CardContent className="pt-4 space-y-4">
            {/* Error state */}
            {error && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
                <p className="text-sm text-destructive">
                  {error instanceof Error ? error.message : 'Failed to load traces'}
                </p>
              </div>
            )}

            {/* Pagination - at top of trace list */}
            {(data?.total ?? 0) > 0 && (
              <TracePagination
                page={currentPage}
                totalPages={totalPages}
                total={data?.total ?? 0}
                limit={pageSize}
                onPageChange={setCurrentPage}
                onLimitChange={handlePageSizeChange}
                isLoading={isLoading}
              />
            )}

            {/* Trace list */}
            <TraceList
              traces={data?.items || []}
              selectedTraceId={selectedTraceId}
              onSelectTrace={handleSelectTrace}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>

        {/* Trace Detail Panel (slide-out) */}
        <TraceDetailPanel
          traceId={selectedTraceId}
          onClose={handleCloseDetail}
        />
      </div>
    </DashboardLayout>
  );
}
