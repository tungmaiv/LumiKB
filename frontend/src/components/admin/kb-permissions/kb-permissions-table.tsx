/**
 * KB Permissions table component with sorting, filtering, and pagination
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1)
 */

'use client';

import React, { useState, useMemo } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, Pencil, Search, User, Users, Trash2 } from 'lucide-react';
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
import type { PermissionExtended, PermissionLevel } from '@/types/permission';

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

type SortField = 'entity_name' | 'entity_type' | 'permission_level' | 'created_at';
type SortDirection = 'asc' | 'desc';

export interface KBPermissionsTableProps {
  permissions: PermissionExtended[];
  total: number;
  page: number;
  limit: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onLimitChange?: (limit: number) => void;
  onEditPermission: (permission: PermissionExtended) => void;
  onDeletePermission: (permission: PermissionExtended) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

function getPermissionBadgeClass(level: PermissionLevel): string {
  switch (level) {
    case 'ADMIN':
      return 'bg-red-500/20 text-red-600 border-red-500/30 hover:bg-red-500/30';
    case 'WRITE':
      return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30 hover:bg-yellow-500/30';
    case 'READ':
      return 'bg-green-500/20 text-green-600 border-green-500/30 hover:bg-green-500/30';
    default:
      return '';
  }
}

export function KBPermissionsTable({
  permissions,
  total,
  page,
  limit,
  isLoading = false,
  onPageChange,
  onLimitChange,
  onEditPermission,
  onDeletePermission,
  searchValue,
  onSearchChange,
}: KBPermissionsTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Filter by search (client-side)
  const filteredPermissions = useMemo(() => {
    if (!searchValue) return permissions;
    const searchLower = searchValue.toLowerCase();
    return permissions.filter(
      (p) =>
        p.entity_name.toLowerCase().includes(searchLower) ||
        p.entity_type.toLowerCase().includes(searchLower)
    );
  }, [permissions, searchValue]);

  // Client-side sorting
  const sortedPermissions = useMemo(() => {
    return [...filteredPermissions].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'entity_name':
          comparison = a.entity_name.localeCompare(b.entity_name);
          break;
        case 'entity_type':
          comparison = a.entity_type.localeCompare(b.entity_type);
          break;
        case 'permission_level': {
          const levels: Record<PermissionLevel, number> = { READ: 1, WRITE: 2, ADMIN: 3 };
          comparison = levels[a.permission_level] - levels[b.permission_level];
          break;
        }
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredPermissions, sortField, sortDirection]);

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

  const totalPages = Math.ceil(total / limit);
  const hasPrevious = page > 1;
  const hasNext = page < totalPages;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading permissions...</p>
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
          placeholder="Search by name or type..."
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
          aria-label="Search permissions"
        />
      </div>

      {/* Pagination Bar - Top */}
      <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
        <div className="flex items-center gap-4">
          {/* Page Size Selector */}
          {onLimitChange && (
            <div className="flex items-center gap-2">
              <label htmlFor="permission-page-size" className="text-sm text-muted-foreground">
                Show
              </label>
              <Select
                value={limit.toString()}
                onValueChange={(value) => onLimitChange(parseInt(value, 10))}
              >
                <SelectTrigger id="permission-page-size" className="w-[80px]">
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
          )}

          {/* Results Info */}
          <p className="text-sm text-muted-foreground">
            Showing <span className="font-medium">{sortedPermissions.length}</span> of{' '}
            <span className="font-medium">{total}</span> permissions
          </p>
        </div>

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
            <span className="font-medium">{totalPages || 1}</span>
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

      {sortedPermissions.length === 0 ? (
        <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
          <div className="text-center">
            <p className="text-lg font-medium">No permissions found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchValue
                ? 'Try adjusting your search term'
                : 'Add users or groups to grant access'}
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
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('entity_type')}
                  >
                    <div className="flex items-center">
                      Type
                      {renderSortIcon('entity_type')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('entity_name')}
                  >
                    <div className="flex items-center">
                      Name
                      {renderSortIcon('entity_name')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('permission_level')}
                  >
                    <div className="flex items-center">
                      Permission
                      {renderSortIcon('permission_level')}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('created_at')}
                  >
                    <div className="flex items-center">
                      Granted
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
                {sortedPermissions.map((permission) => (
                  <tr key={permission.id} className="hover:bg-muted/50">
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <span className="inline-flex items-center gap-1.5">
                        {permission.entity_type === 'user' ? (
                          <>
                            <User className="h-4 w-4 text-blue-500" />
                            <span className="text-blue-600 font-medium">User</span>
                          </>
                        ) : (
                          <>
                            <Users className="h-4 w-4 text-purple-500" />
                            <span className="text-purple-600 font-medium">Group</span>
                          </>
                        )}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium">
                      {permission.entity_name}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <Badge className={getPermissionBadgeClass(permission.permission_level)}>
                        {permission.permission_level}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(permission.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onEditPermission(permission)}
                          className="text-primary hover:text-primary/80"
                          aria-label={`Edit permission for ${permission.entity_name}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeletePermission(permission)}
                          className="text-destructive hover:text-destructive/80"
                          aria-label={`Remove permission for ${permission.entity_name}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
