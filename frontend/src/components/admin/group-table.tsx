/**
 * Group management table component with sorting, filtering, expandable rows, and pagination
 * Story 5.19: Group Management (AC-5.19.2)
 * Story 7.11: Navigation Restructure with RBAC Default Groups
 *
 * AC-7.11.8: System groups display "System" badge
 * AC-7.11.9: Groups display permission level badge
 * AC-7.11.10: System groups are non-editable and non-deletable
 */

'use client';

import React, { useState, useMemo } from 'react';
import { format } from 'date-fns';
import {
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Lock,
  Pencil,
  Search,
  Shield,
  Users,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import type { Group, GroupMember } from '@/types/group';
import { PermissionLevel } from '@/types/user';

/** Map permission levels to display names */
const PERMISSION_LEVEL_LABELS: Record<PermissionLevel, string> = {
  [PermissionLevel.USER]: 'User',
  [PermissionLevel.OPERATOR]: 'Operator',
  [PermissionLevel.ADMINISTRATOR]: 'Admin',
};

/** Map permission levels to badge colors */
const PERMISSION_LEVEL_COLORS: Record<PermissionLevel, string> = {
  [PermissionLevel.USER]: 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border-gray-500/30',
  [PermissionLevel.OPERATOR]: 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30',
  [PermissionLevel.ADMINISTRATOR]: 'bg-purple-500/20 text-purple-600 dark:text-purple-400 border-purple-500/30',
};

type SortField = 'name' | 'member_count' | 'is_active' | 'created_at' | 'permission_level';
type SortDirection = 'asc' | 'desc';

export interface GroupTableProps {
  groups: Group[];
  total: number;
  page: number;
  totalPages: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onEditGroup: (group: Group) => void;
  onDeleteGroup: (group: Group) => void;
  onManageMembers: (group: Group) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  expandedGroup: string | null;
  onExpandGroup: (groupId: string | null) => void;
  expandedMembers: GroupMember[];
  isLoadingMembers?: boolean;
}

export function GroupTable({
  groups,
  total,
  page,
  totalPages,
  isLoading = false,
  onPageChange,
  onEditGroup,
  onDeleteGroup,
  onManageMembers,
  searchValue,
  onSearchChange,
  expandedGroup,
  onExpandGroup,
  expandedMembers,
  isLoadingMembers = false,
}: GroupTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Client-side sorting
  const sortedGroups = useMemo(() => {
    return [...groups].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'member_count':
          comparison = a.member_count - b.member_count;
          break;
        case 'is_active':
          comparison = Number(a.is_active) - Number(b.is_active);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'permission_level':
          comparison = a.permission_level - b.permission_level;
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [groups, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy');
    } catch {
      return 'Invalid date';
    }
  };

  const truncateDescription = (description: string | null, maxLength = 50): string => {
    if (!description) return '-';
    if (description.length <= maxLength) return description;
    return `${description.substring(0, maxLength)}...`;
  };

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <span className="ml-1 text-muted-foreground/50 w-4" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="ml-1 h-4 w-4" />
    ) : (
      <ChevronDown className="ml-1 h-4 w-4" />
    );
  };

  const hasPrevious = page > 1;
  const hasNext = page < totalPages;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading groups...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search by name..."
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
          aria-label="Search groups by name"
        />
      </div>

      {sortedGroups.length === 0 ? (
        <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
          <div className="text-center">
            <p className="text-lg font-medium">No groups found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchValue ? 'Try adjusting your search term' : 'Create your first group'}
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="overflow-x-auto rounded-lg border bg-card">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-muted">
                <tr>
                  <th scope="col" className="w-8 px-2 py-3" />
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('name')}
                  >
                    <div className="flex items-center">
                      Name
                      {renderSortIcon('name')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                  >
                    Description
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('member_count')}
                  >
                    <div className="flex items-center">
                      Members
                      {renderSortIcon('member_count')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('permission_level')}
                  >
                    <div className="flex items-center">
                      Level
                      {renderSortIcon('permission_level')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('is_active')}
                  >
                    <div className="flex items-center">
                      Status
                      {renderSortIcon('is_active')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('created_at')}
                  >
                    <div className="flex items-center">
                      Created
                      {renderSortIcon('created_at')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground"
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sortedGroups.map((group) => (
                  <React.Fragment key={group.id}>
                    <tr className="hover:bg-muted/50">
                      <td className="px-2 py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={() =>
                            onExpandGroup(expandedGroup === group.id ? null : group.id)
                          }
                          aria-label={
                            expandedGroup === group.id ? 'Collapse members' : 'Expand members'
                          }
                        >
                          <ChevronRight
                            className={`h-4 w-4 transition-transform ${
                              expandedGroup === group.id ? 'rotate-90' : ''
                            }`}
                          />
                        </Button>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm font-medium">
                        <div className="flex items-center gap-2">
                          {group.name}
                          {group.is_system && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Badge
                                    variant="outline"
                                    className="bg-slate-500/20 text-slate-600 dark:text-slate-400 border-slate-500/30"
                                    data-testid="system-badge"
                                  >
                                    <Lock className="h-3 w-3 mr-1" />
                                    System
                                  </Badge>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>System group - cannot be modified or deleted</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground max-w-xs">
                        {truncateDescription(group.description)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm">
                        <span className="inline-flex items-center gap-1">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          {group.member_count}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm">
                        <Badge
                          variant="outline"
                          className={PERMISSION_LEVEL_COLORS[group.permission_level]}
                          data-testid="permission-level-badge"
                        >
                          <Shield className="h-3 w-3 mr-1" />
                          {PERMISSION_LEVEL_LABELS[group.permission_level]}
                        </Badge>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm">
                        {group.is_active ? (
                          <Badge
                            data-testid="status-badge-active"
                            className="bg-green-500/20 text-green-600 border-green-500/30 hover:bg-green-500/30"
                          >
                            Active
                          </Badge>
                        ) : (
                          <Badge
                            data-testid="status-badge-inactive"
                            variant="destructive"
                            className="bg-red-500/20 text-red-600 border-red-500/30 hover:bg-red-500/30"
                          >
                            Inactive
                          </Badge>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                        {formatDate(group.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onManageMembers(group)}
                            className="text-primary hover:text-primary/80"
                            aria-label={`Manage members of ${group.name}`}
                          >
                            <Users className="h-4 w-4" />
                          </Button>
                          {group.is_system ? (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      disabled
                                      className="text-muted-foreground cursor-not-allowed"
                                      aria-label={`Cannot edit system group ${group.name}`}
                                    >
                                      <Pencil className="h-4 w-4" />
                                    </Button>
                                  </span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>System groups cannot be edited</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onEditGroup(group)}
                              className="text-primary hover:text-primary/80"
                              aria-label={`Edit ${group.name}`}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          )}
                          {group.is_system ? (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      disabled
                                      className="text-muted-foreground cursor-not-allowed"
                                      aria-label={`Cannot delete system group ${group.name}`}
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>System groups cannot be deleted</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onDeleteGroup(group)}
                              className="text-destructive hover:text-destructive/80"
                              aria-label={`Delete ${group.name}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {/* Expandable row for members */}
                    {expandedGroup === group.id && (
                      <tr>
                        <td colSpan={8} className="bg-muted/30 px-8 py-4">
                          {isLoadingMembers ? (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
                              Loading members...
                            </div>
                          ) : expandedMembers.length === 0 ? (
                            <p className="text-sm text-muted-foreground">No members in this group</p>
                          ) : (
                            <div className="space-y-2">
                              <p className="text-xs font-medium text-muted-foreground uppercase">
                                Group Members ({expandedMembers.length})
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {expandedMembers.slice(0, 5).map((member) => (
                                  <Badge
                                    key={member.id}
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {member.email}
                                    {!member.is_active && (
                                      <span className="ml-1 text-destructive">(inactive)</span>
                                    )}
                                  </Badge>
                                ))}
                                {expandedMembers.length > 5 && (
                                  <Badge
                                    variant="outline"
                                    className="text-xs text-muted-foreground"
                                  >
                                    +{expandedMembers.length - 5} more...
                                  </Badge>
                                )}
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
            <p className="text-sm text-muted-foreground">
              Showing <span className="font-medium">{sortedGroups.length}</span> of{' '}
              <span className="font-medium">{total}</span> groups
            </p>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page - 1)}
                disabled={!hasPrevious}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground px-2">
                Page <span className="font-medium">{page}</span> of{' '}
                <span className="font-medium">{totalPages}</span>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page + 1)}
                disabled={!hasNext}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
