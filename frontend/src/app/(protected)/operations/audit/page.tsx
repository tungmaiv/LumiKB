/**
 * Audit Log Viewer page (Operations section)
 * Story 5.2: Audit Log Viewer
 * Story 5.3: Audit Log Export
 * Story 7.11: Navigation Restructure - moved to /operations/audit
 */

'use client';

import { useState } from 'react';
import { Download, FileSearch } from 'lucide-react';
import { AuditLogFilters } from '@/components/admin/audit-log-filters';
import { AuditLogTable } from '@/components/admin/audit-log-table';
import { AuditEventDetailsModal } from '@/components/admin/audit-event-details-modal';
import { ExportAuditLogsModal } from '@/components/admin/export-audit-logs-modal';
import { useAuditLogs } from '@/hooks/useAuditLogs';
import type { AuditEvent, AuditLogFilter, AuditLogFilters as AuditFilters } from '@/types/audit';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';

export default function OperationsAuditPage() {
  const [filters, setFilters] = useState<AuditLogFilter>({});
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // Fetch audit logs with filters
  const { data, isLoading, error } = useAuditLogs({
    filters,
    page,
    pageSize,
  });

  const handleFiltersChange = (newFilters: AuditLogFilter) => {
    setFilters(newFilters);
    setPage(1); // Reset to page 1 when filters change
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to page 1 when page size changes
  };

  const handleViewDetails = (event: AuditEvent) => {
    setSelectedEvent(event);
    setIsDetailsModalOpen(true);
  };

  const handleCloseDetails = () => {
    setIsDetailsModalOpen(false);
    setSelectedEvent(null);
  };

  const handleOpenExport = () => {
    setIsExportModalOpen(true);
  };

  const handleCloseExport = () => {
    setIsExportModalOpen(false);
  };

  // Convert filters to ExportAuditLogsModal format
  const exportFilters: AuditFilters = {
    startDate: filters.start_date,
    endDate: filters.end_date,
    userEmail: filters.user_email,
    eventType: filters.event_type,
    resourceType: filters.resource_type,
  };

  return (
    <DashboardLayout>
      <div className="container mx-auto space-y-6 p-6">
        {/* Page Header */}
        <div className="flex justify-between items-start">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <FileSearch className="h-8 w-8" />
              <h1 className="text-2xl font-bold">Audit Logs</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              View and filter system audit logs for security investigations,
              compliance reporting, and troubleshooting
            </p>
          </div>
          {/* Export Button */}
          <Button onClick={handleOpenExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>

        {/* Filters Section */}
        <AuditLogFilters filters={filters} onFiltersChange={handleFiltersChange} />

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-destructive"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-destructive">
                  Error loading audit logs
                </h3>
                <p className="mt-1 text-sm text-destructive/80">
                  {error instanceof Error ? error.message : 'Unknown error'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Audit Log Table */}
        <AuditLogTable
          events={data?.events || []}
          totalCount={data?.total || 0}
          page={page}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          onViewDetails={handleViewDetails}
          isLoading={isLoading}
        />

        {/* Event Details Modal */}
        <AuditEventDetailsModal
          event={selectedEvent}
          isOpen={isDetailsModalOpen}
          onClose={handleCloseDetails}
        />

        {/* Export Modal */}
        <ExportAuditLogsModal
          open={isExportModalOpen}
          onClose={handleCloseExport}
          filters={exportFilters}
          recordCount={data?.total || 0}
        />
      </div>
    </DashboardLayout>
  );
}
