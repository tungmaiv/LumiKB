/**
 * Audit log filters component
 * Story 5.2: Audit Log Viewer
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import type { AuditLogFilter } from '@/types/audit';
import { EVENT_TYPES, RESOURCE_TYPES } from '@/types/audit';

export interface AuditLogFiltersProps {
  filters: AuditLogFilter;
  onFiltersChange: (filters: AuditLogFilter) => void;
  eventTypes?: readonly string[];
  resourceTypes?: readonly string[];
}

export function AuditLogFilters({
  filters,
  onFiltersChange,
  eventTypes = EVENT_TYPES,
  resourceTypes = RESOURCE_TYPES,
}: AuditLogFiltersProps) {
  const [localFilters, setLocalFilters] = useState<AuditLogFilter>(filters);
  const [isOpen, setIsOpen] = useState(false);

  // Count active filters
  const activeFilterCount = [
    localFilters.event_type,
    localFilters.resource_type,
    localFilters.user_email,
    localFilters.start_date,
    localFilters.end_date,
  ].filter(Boolean).length;

  const handleApplyFilters = () => {
    // Trim whitespace from email before applying
    const filtersToApply: AuditLogFilter = {
      ...localFilters,
      user_email: localFilters.user_email?.trim() || undefined,
    };
    onFiltersChange(filtersToApply);
  };

  const handleResetFilters = () => {
    const emptyFilters: AuditLogFilter = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="rounded-lg border bg-card">
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center justify-between p-4 text-left hover:bg-muted/50 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              <h3 className="text-lg font-semibold">Filters</h3>
              {activeFilterCount > 0 && (
                <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
                  {activeFilterCount} active
                </span>
              )}
            </div>
            {isOpen ? (
              <ChevronUp className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            )}
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="space-y-4 border-t p-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {/* Event Type Filter */}
              <div className="space-y-2">
                <label htmlFor="event-type" className="text-sm font-medium">
                  Event Type
                </label>
                <Select
                  value={localFilters.event_type || '__all__'}
                  onValueChange={(value) =>
                    setLocalFilters({
                      ...localFilters,
                      event_type: value === '__all__' ? undefined : value,
                    })
                  }
                >
                  <SelectTrigger id="event-type">
                    <SelectValue placeholder="All event types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All event types</SelectItem>
                    {eventTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Resource Type Filter */}
              <div className="space-y-2">
                <label htmlFor="resource-type" className="text-sm font-medium">
                  Resource Type
                </label>
                <Select
                  value={localFilters.resource_type || '__all__'}
                  onValueChange={(value) =>
                    setLocalFilters({
                      ...localFilters,
                      resource_type: value === '__all__' ? undefined : value,
                    })
                  }
                >
                  <SelectTrigger id="resource-type">
                    <SelectValue placeholder="All resource types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All resource types</SelectItem>
                    {resourceTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* User Email Filter */}
              <div className="space-y-2">
                <label htmlFor="user-email" className="text-sm font-medium">
                  User Email
                </label>
                <Input
                  id="user-email"
                  type="text"
                  placeholder="Search by email..."
                  value={localFilters.user_email || ''}
                  onChange={(e) =>
                    setLocalFilters({
                      ...localFilters,
                      user_email: e.target.value || undefined,
                    })
                  }
                />
              </div>

              {/* Start Date Filter */}
              <div className="space-y-2">
                <label htmlFor="start-date" className="text-sm font-medium">
                  Start Date
                </label>
                <Input
                  id="start-date"
                  type="datetime-local"
                  value={
                    localFilters.start_date
                      ? localFilters.start_date.slice(0, 16)
                      : ''
                  }
                  onChange={(e) =>
                    setLocalFilters({
                      ...localFilters,
                      start_date: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    })
                  }
                />
              </div>

              {/* End Date Filter */}
              <div className="space-y-2">
                <label htmlFor="end-date" className="text-sm font-medium">
                  End Date
                </label>
                <Input
                  id="end-date"
                  type="datetime-local"
                  value={
                    localFilters.end_date
                      ? localFilters.end_date.slice(0, 16)
                      : ''
                  }
                  onChange={(e) =>
                    setLocalFilters({
                      ...localFilters,
                      end_date: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    })
                  }
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button onClick={handleApplyFilters} className="px-6">
                Apply Filters
              </Button>
              <Button onClick={handleResetFilters} variant="outline" className="px-6">
                Reset
              </Button>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
