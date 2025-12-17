'use client';

import { useCallback, useState } from 'react';
import { Search, X, Filter, Calendar, FileType, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DocumentFilterActions, DocumentFilterState } from '@/lib/hooks/use-document-filters';
import { DocumentStatus } from '@/lib/hooks/use-documents';

interface DocumentFilterBarProps {
  filters: DocumentFilterState;
  actions: DocumentFilterActions;
  hasActiveFilters: boolean;
  activeFilterCount: number;
  /** Available tags for filtering (from all documents in KB) */
  availableTags?: string[];
  className?: string;
}

const STATUS_OPTIONS: { value: DocumentStatus; label: string }[] = [
  { value: 'READY', label: 'Ready' },
  { value: 'PROCESSING', label: 'Processing' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'ARCHIVED', label: 'Archived' },
];

const MIME_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'application/pdf', label: 'PDF' },
  {
    value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    label: 'DOCX',
  },
  { value: 'text/markdown', label: 'Markdown' },
];

/**
 * Filter bar component for document list filtering.
 *
 * Provides search input, status/type dropdowns, tag selection, and date range filters.
 */
export function DocumentFilterBar({
  filters,
  actions,
  hasActiveFilters,
  activeFilterCount,
  availableTags = [],
  className,
}: DocumentFilterBarProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Debounced search handler
  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchInput(value);
      // Debounce search by 300ms
      const timeoutId = setTimeout(() => {
        actions.setSearch(value);
      }, 300);
      return () => clearTimeout(timeoutId);
    },
    [actions]
  );

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      actions.setStatus(undefined);
    } else {
      actions.setStatus(value as DocumentStatus);
    }
  };

  const handleMimeTypeChange = (value: string) => {
    if (value === 'all') {
      actions.setMimeType(undefined);
    } else {
      actions.setMimeType(value);
    }
  };

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || [];
    if (currentTags.includes(tag)) {
      actions.setTags(currentTags.filter((t) => t !== tag));
    } else {
      actions.setTags([...currentTags, tag]);
    }
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    actions.setDateRange(e.target.value || undefined, filters.dateTo);
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    actions.setDateRange(filters.dateFrom, e.target.value || undefined);
  };

  const handleClearFilters = () => {
    setSearchInput('');
    actions.resetFilters();
  };

  return (
    <div className={className} data-testid="document-filter-bar">
      {/* Main filter row */}
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
            data-testid="document-search-input"
          />
          {searchInput && (
            <button
              onClick={() => {
                setSearchInput('');
                actions.setSearch('');
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Status filter */}
        <Select value={filters.status || 'all'} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-[140px]" data-testid="status-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            {STATUS_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* MIME type filter */}
        <Select value={filters.mimeType || 'all'} onValueChange={handleMimeTypeChange}>
          <SelectTrigger className="w-[130px]" data-testid="type-filter">
            <FileType className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {MIME_TYPE_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
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
            onClick={handleClearFilters}
            className="text-muted-foreground hover:text-foreground"
            data-testid="clear-filters-button"
          >
            <X className="mr-1 h-4 w-4" />
            Clear filters
          </Button>
        )}
      </div>

      {/* Advanced filters panel */}
      {showAdvanced && (
        <div
          className="mt-4 rounded-lg border bg-muted/30 p-4 space-y-4"
          data-testid="advanced-filters-panel"
        >
          {/* Date range filters */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Date Range:</span>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={filters.dateFrom || ''}
                onChange={handleDateFromChange}
                className="w-[160px]"
                data-testid="date-from-input"
              />
              <span className="text-muted-foreground">to</span>
              <Input
                type="date"
                value={filters.dateTo || ''}
                onChange={handleDateToChange}
                className="w-[160px]"
                data-testid="date-to-input"
              />
            </div>
          </div>

          {/* Tags filter */}
          {availableTags.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Filter by Tags:</span>
              </div>
              <div className="flex flex-wrap gap-2" data-testid="tag-filters">
                {availableTags.map((tag) => {
                  const isSelected = filters.tags?.includes(tag);
                  return (
                    <Badge
                      key={tag}
                      variant={isSelected ? 'default' : 'outline'}
                      className="cursor-pointer transition-colors"
                      onClick={() => handleTagToggle(tag)}
                      data-testid={`tag-filter-${tag}`}
                    >
                      {tag}
                      {isSelected && <X className="ml-1 h-3 w-3" />}
                    </Badge>
                  );
                })}
              </div>
            </div>
          )}

          {/* Active filters summary */}
          {hasActiveFilters && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {filters.search && (
                <Badge variant="secondary" className="gap-1">
                  Search: &quot;{filters.search}&quot;
                  <button
                    onClick={() => {
                      setSearchInput('');
                      actions.setSearch('');
                    }}
                    className="hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary" className="gap-1">
                  Status: {filters.status}
                  <button
                    onClick={() => actions.setStatus(undefined)}
                    className="hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {filters.mimeType && (
                <Badge variant="secondary" className="gap-1">
                  Type:{' '}
                  {MIME_TYPE_OPTIONS.find((o) => o.value === filters.mimeType)?.label ||
                    filters.mimeType}
                  <button
                    onClick={() => actions.setMimeType(undefined)}
                    className="hover:text-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {filters.tags?.map((tag) => (
                <Badge key={tag} variant="secondary" className="gap-1">
                  Tag: {tag}
                  <button onClick={() => handleTagToggle(tag)} className="hover:text-foreground">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {(filters.dateFrom || filters.dateTo) && (
                <Badge variant="secondary" className="gap-1">
                  Date: {filters.dateFrom || '...'} - {filters.dateTo || '...'}
                  <button
                    onClick={() => actions.setDateRange(undefined, undefined)}
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
    </div>
  );
}
