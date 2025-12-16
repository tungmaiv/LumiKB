/**
 * Trace Filters Component
 *
 * Story 9-8: Trace Viewer UI Component
 * AC2: Filtering controls for operation type, status, and date range
 */
'use client';

import { Filter, Search, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export interface TraceFilters {
  operation_type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

interface TraceFiltersProps {
  filters: TraceFilters;
  onFilterChange: (filters: TraceFilters) => void;
}

const OPERATION_TYPES = [
  { value: 'all', label: 'All Operations' },
  { value: 'chat_completion', label: 'Chat Completion' },
  { value: 'document_processing', label: 'Document Processing' },
  { value: 'embedding', label: 'Embedding' },
  { value: 'search', label: 'Search' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Statuses' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'in_progress', label: 'In Progress' },
];

export function TraceFiltersComponent({ filters, onFilterChange }: TraceFiltersProps) {
  const handleOperationTypeChange = (value: string) => {
    onFilterChange({
      ...filters,
      operation_type: value === 'all' ? undefined : value,
    });
  };

  const handleStatusChange = (value: string) => {
    onFilterChange({
      ...filters,
      status: value === 'all' ? undefined : value,
    });
  };

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      start_date: e.target.value || undefined,
    });
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      end_date: e.target.value || undefined,
    });
  };

  const clearFilters = () => {
    onFilterChange({});
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      search: e.target.value || undefined,
    });
  };

  const hasActiveFilters =
    filters.operation_type ||
    filters.status ||
    filters.start_date ||
    filters.end_date ||
    filters.search;

  return (
    <div className="flex flex-col gap-3 p-4 border-b bg-muted/30">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search by trace ID, doc ID, or name..."
          value={filters.search || ''}
          onChange={handleSearchChange}
          className="pl-8 w-full max-w-md"
          data-testid="search-filter"
        />
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Filter className="h-4 w-4" />
          <span>Filters:</span>
        </div>

        <Select
          value={filters.operation_type || 'all'}
          onValueChange={handleOperationTypeChange}
        >
          <SelectTrigger className="w-[180px]" data-testid="operation-type-filter">
            <SelectValue placeholder="Operation Type" />
          </SelectTrigger>
          <SelectContent>
            {OPERATION_TYPES.map((op) => (
              <SelectItem key={op.value} value={op.value}>
                {op.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.status || 'all'}
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-[150px]" data-testid="status-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((status) => (
              <SelectItem key={status.value} value={status.value}>
                {status.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">From:</label>
          <Input
            type="datetime-local"
            value={filters.start_date || ''}
            onChange={handleStartDateChange}
            className="w-auto"
            data-testid="start-date-filter"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">To:</label>
          <Input
            type="datetime-local"
            value={filters.end_date || ''}
            onChange={handleEndDateChange}
            className="w-auto"
            data-testid="end-date-filter"
          />
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="gap-1"
            data-testid="clear-filters-btn"
          >
            <X className="h-4 w-4" />
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}
