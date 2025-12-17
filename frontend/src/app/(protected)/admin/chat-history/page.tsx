/**
 * Chat History Page
 *
 * Story 9-9: Chat History Viewer UI
 * AC1: Session list displays user, KB name, message count, and last active timestamp
 * AC9: Pagination for long histories with page controls
 */
'use client';

import { useCallback, useState } from 'react';
import { MessageCircle } from 'lucide-react';

import { ChatSessionList, ChatFilters, SessionDetailPanel } from '@/components/admin/chat';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { useChatSessions, type ChatHistoryFilters } from '@/hooks/useChatHistory';

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;
const DEFAULT_PAGE_SIZE = 20;

export default function ChatHistoryPage() {
  const [filters, setFilters] = useState<ChatHistoryFilters>({});
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const { data, isLoading, error } = useChatSessions({
    ...filters,
  });

  const handleFiltersChange = useCallback(
    (filtersOrUpdater: ChatHistoryFilters | ((prev: ChatHistoryFilters) => ChatHistoryFilters)) => {
      setFilters((prev) => {
        const newFilters =
          typeof filtersOrUpdater === 'function' ? filtersOrUpdater(prev) : filtersOrUpdater;
        return newFilters;
      });
      setCurrentPage(1); // Reset to first page on filter change
    },
    []
  );

  const handleSelectSession = useCallback((sessionId: string) => {
    setSelectedSessionId(sessionId);
  }, []);

  const handleClosePanel = useCallback(() => {
    setSelectedSessionId(null);
  }, []);

  const sessions = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  // Pagination calculations
  const startIndex = total > 0 ? (currentPage - 1) * pageSize + 1 : 0;
  const endIndex = Math.min(currentPage * pageSize, total);
  const hasPrevious = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const handlePageChange = useCallback((newPage: number) => {
    setCurrentPage(newPage);
  }, []);

  const handlePageSizeChange = useCallback((newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1); // Reset to page 1 when page size changes
  }, []);

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <MessageCircle className="h-8 w-8" />
            <h1 className="text-2xl font-bold">Chat History</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Browse and analyze user conversations across knowledge bases
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <ChatFilters filters={filters} onFiltersChange={handleFiltersChange} />
          </CardContent>
        </Card>

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4 mb-6">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load chat history'}
            </p>
          </div>
        )}

        {/* Session List with Pagination Bar */}
        <div className="space-y-4">
          {/* Pagination Bar - Top (similar to audit logs) */}
          <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
            <div className="flex items-center gap-4">
              {/* Page Size Selector */}
              <div className="flex items-center gap-2">
                <label htmlFor="page-size" className="text-sm text-muted-foreground">
                  Show
                </label>
                <Select
                  value={pageSize.toString()}
                  onValueChange={(value) => handlePageSizeChange(parseInt(value, 10))}
                >
                  <SelectTrigger id="page-size" className="w-[80px]">
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
              <p className="text-sm text-muted-foreground">
                Showing <span className="font-medium">{startIndex}</span> to{' '}
                <span className="font-medium">{endIndex}</span> of{' '}
                <span className="font-medium">{total}</span> sessions
              </p>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!hasPrevious}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground px-2">
                Page <span className="font-medium">{currentPage}</span> of{' '}
                <span className="font-medium">{totalPages || 1}</span>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!hasNext}
              >
                Next
              </Button>
            </div>
          </div>

          {/* Conversations Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Conversations</CardTitle>
            </CardHeader>
            <CardContent>
              <ChatSessionList
                sessions={sessions}
                selectedSessionId={selectedSessionId}
                onSelectSession={handleSelectSession}
                isLoading={isLoading}
              />
            </CardContent>
          </Card>
        </div>

        {/* Session Detail Panel */}
        <SessionDetailPanel sessionId={selectedSessionId} onClose={handleClosePanel} />
      </div>
    </DashboardLayout>
  );
}
