/**
 * Processing filter bar component
 * Story 5-23 (AC-5.23.2): Filter by file type, status, or processing step
 */

"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Filter, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type {
  ProcessingFilters,
  DocumentStatus,
  ProcessingStep,
} from "@/types/processing";
import {
  DOC_STATUS_LABELS,
  STEP_LABELS,
  PROCESSING_STEPS_ORDER,
} from "@/types/processing";

const DOCUMENT_STATUSES: DocumentStatus[] = [
  "pending",
  "processing",
  "ready",
  "failed",
];

const FILE_TYPES = ["pdf", "docx", "doc", "txt", "xlsx", "pptx", "md"];

export interface ProcessingFilterBarProps {
  filters: ProcessingFilters;
  onFiltersChange: (filters: ProcessingFilters) => void;
}

export function ProcessingFilterBar({
  filters,
  onFiltersChange,
}: ProcessingFilterBarProps) {
  const [localFilters, setLocalFilters] = useState<ProcessingFilters>(filters);
  const [isOpen, setIsOpen] = useState(false);

  // Count active filters
  const activeFilterCount = [
    localFilters.name,
    localFilters.file_type,
    localFilters.status,
    localFilters.current_step,
  ].filter(Boolean).length;

  const handleApplyFilters = () => {
    const filtersToApply: ProcessingFilters = {
      ...localFilters,
      name: localFilters.name?.trim() || undefined,
    };
    onFiltersChange(filtersToApply);
  };

  const handleResetFilters = () => {
    const emptyFilters: ProcessingFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const handleQuickSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleApplyFilters();
    }
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="rounded-lg border bg-card">
        <div className="flex items-center gap-4 p-4">
          {/* Quick search always visible */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={localFilters.name || ""}
              onChange={(e) =>
                setLocalFilters({ ...localFilters, name: e.target.value })
              }
              onKeyDown={handleQuickSearch}
              className="pl-9"
            />
          </div>

          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-muted/50 transition-colors"
            >
              <Filter className="h-4 w-4" />
              <span className="text-sm font-medium">Filters</span>
              {activeFilterCount > 0 && (
                <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
                  {activeFilterCount}
                </span>
              )}
              {isOpen ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent>
          <div className="space-y-4 border-t p-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {/* File Type Filter */}
              <div className="space-y-2">
                <label htmlFor="file-type" className="text-sm font-medium">
                  File Type
                </label>
                <Select
                  value={localFilters.file_type || "__all__"}
                  onValueChange={(value) =>
                    setLocalFilters({
                      ...localFilters,
                      file_type: value === "__all__" ? undefined : value,
                    })
                  }
                >
                  <SelectTrigger id="file-type">
                    <SelectValue placeholder="All file types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All file types</SelectItem>
                    {FILE_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type.toUpperCase()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Status Filter */}
              <div className="space-y-2">
                <label htmlFor="status" className="text-sm font-medium">
                  Status
                </label>
                <Select
                  value={localFilters.status || "__all__"}
                  onValueChange={(value) =>
                    setLocalFilters({
                      ...localFilters,
                      status:
                        value === "__all__"
                          ? undefined
                          : (value as DocumentStatus),
                    })
                  }
                >
                  <SelectTrigger id="status">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All statuses</SelectItem>
                    {DOCUMENT_STATUSES.map((status) => (
                      <SelectItem key={status} value={status}>
                        {DOC_STATUS_LABELS[status]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Current Step Filter */}
              <div className="space-y-2">
                <label htmlFor="current-step" className="text-sm font-medium">
                  Processing Step
                </label>
                <Select
                  value={localFilters.current_step || "__all__"}
                  onValueChange={(value) =>
                    setLocalFilters({
                      ...localFilters,
                      current_step:
                        value === "__all__"
                          ? undefined
                          : (value as ProcessingStep),
                    })
                  }
                >
                  <SelectTrigger id="current-step">
                    <SelectValue placeholder="All steps" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All steps</SelectItem>
                    {PROCESSING_STEPS_ORDER.map((step) => (
                      <SelectItem key={step} value={step}>
                        {STEP_LABELS[step]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Sort Order */}
              <div className="space-y-2">
                <label htmlFor="sort-order" className="text-sm font-medium">
                  Sort By
                </label>
                <Select
                  value={`${localFilters.sort_by || "created_at"}_${
                    localFilters.sort_order || "desc"
                  }`}
                  onValueChange={(value) => {
                    const [sortBy, sortOrder] = value.split("_") as [
                      ProcessingFilters["sort_by"],
                      ProcessingFilters["sort_order"]
                    ];
                    setLocalFilters({
                      ...localFilters,
                      sort_by: sortBy,
                      sort_order: sortOrder,
                    });
                  }}
                >
                  <SelectTrigger id="sort-order">
                    <SelectValue placeholder="Sort by..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at_desc">
                      Newest First
                    </SelectItem>
                    <SelectItem value="created_at_asc">Oldest First</SelectItem>
                    <SelectItem value="original_filename_asc">
                      Name (A-Z)
                    </SelectItem>
                    <SelectItem value="original_filename_desc">
                      Name (Z-A)
                    </SelectItem>
                    <SelectItem value="status_asc">Status (A-Z)</SelectItem>
                    <SelectItem value="status_desc">Status (Z-A)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button onClick={handleApplyFilters} className="px-6">
                Apply Filters
              </Button>
              <Button
                onClick={handleResetFilters}
                variant="outline"
                className="px-6"
              >
                Reset
              </Button>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
