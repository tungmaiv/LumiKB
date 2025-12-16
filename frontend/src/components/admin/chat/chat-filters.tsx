/**
 * Chat History Filter Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC6: Search within chat history by content
 * AC7: Filter by user, KB, and date range
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import { Calendar, Search, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDebounce } from '@/hooks/useDebounce';
import type { ChatHistoryFilters } from '@/hooks/useChatHistory';

interface ChatFiltersProps {
  filters: ChatHistoryFilters;
  onFiltersChange: (
    filtersOrUpdater: ChatHistoryFilters | ((prev: ChatHistoryFilters) => ChatHistoryFilters)
  ) => void;
  users?: Array<{ id: string; name: string }>;
  knowledgeBases?: Array<{ id: string; name: string }>;
}

export function ChatFilters({
  filters,
  onFiltersChange,
  users = [],
  knowledgeBases = [],
}: ChatFiltersProps) {
  const [searchQuery, setSearchQuery] = useState(filters.searchQuery || '');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'custom'>('7d');

  // Debounce search query (300ms as per spec)
  const debouncedSearch = useDebounce(searchQuery, 300);

  // Update filters when debounced search changes
  // Use functional update pattern to avoid depending on `filters` object reference
  useEffect(() => {
    if (debouncedSearch !== filters.searchQuery) {
      onFiltersChange((prev) => ({ ...prev, searchQuery: debouncedSearch || undefined }));
    }
    // Only re-run when debouncedSearch changes, not when filters object reference changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, onFiltersChange]);

  const handleUserChange = useCallback(
    (userId: string) => {
      onFiltersChange((prev) => ({
        ...prev,
        userId: userId === 'all' ? undefined : userId,
      }));
    },
    [onFiltersChange]
  );

  const handleKBChange = useCallback(
    (kbId: string) => {
      onFiltersChange((prev) => ({
        ...prev,
        kbId: kbId === 'all' ? undefined : kbId,
      }));
    },
    [onFiltersChange]
  );

  const handleDateRangeChange = useCallback(
    (range: '24h' | '7d' | '30d' | 'custom') => {
      setDateRange(range);
      const now = new Date();
      let startDate: string | undefined;

      switch (range) {
        case '24h':
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
          break;
        case '7d':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
          break;
        case '30d':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
          break;
        case 'custom':
          startDate = undefined;
          break;
      }

      onFiltersChange((prev) => ({
        ...prev,
        startDate,
        endDate: range !== 'custom' ? now.toISOString() : undefined,
      }));
    },
    [onFiltersChange]
  );

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setDateRange('7d');
    onFiltersChange({});
  }, [onFiltersChange]);

  const hasActiveFilters =
    !!filters.searchQuery ||
    !!filters.userId ||
    !!filters.kbId ||
    !!filters.startDate;

  return (
    <div className="space-y-4">
      {/* Search Input - Full width on top */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search messages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
          data-testid="chat-search-input"
        />
      </div>

      {/* Filters Row - Below search */}
      <div className="flex flex-wrap items-center gap-3">
        {/* User Filter */}
        <Select
          value={filters.userId || 'all'}
          onValueChange={handleUserChange}
        >
          <SelectTrigger className="w-[160px]" data-testid="user-filter">
            <SelectValue placeholder="All Users" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Users</SelectItem>
            {users.map((user) => (
              <SelectItem key={user.id} value={user.id}>
                {user.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* KB Filter */}
        <Select value={filters.kbId || 'all'} onValueChange={handleKBChange}>
          <SelectTrigger className="w-[180px]" data-testid="kb-filter">
            <SelectValue placeholder="All Knowledge Bases" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Knowledge Bases</SelectItem>
            {knowledgeBases.map((kb) => (
              <SelectItem key={kb.id} value={kb.id}>
                {kb.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Date Range */}
        <Select value={dateRange} onValueChange={handleDateRangeChange}>
          <SelectTrigger className="w-[140px]" data-testid="date-range-filter">
            <Calendar className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Date Range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="24h">Last 24 hours</SelectItem>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="custom">Custom</SelectItem>
          </SelectContent>
        </Select>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-10"
            data-testid="clear-filters"
          >
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}
