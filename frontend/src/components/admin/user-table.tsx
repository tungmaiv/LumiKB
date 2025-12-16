/**
 * User management table component with sorting, filtering, and pagination
 * Story 5.18: User Management UI (AC-5.18.1)
 */

'use client';

import React, { useState, useMemo } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, Pencil, Search } from 'lucide-react';
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
import type { UserRead, PaginationMeta } from '@/types/user';

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

type SortField = 'email' | 'is_active' | 'is_superuser' | 'created_at' | 'last_active';
type SortDirection = 'asc' | 'desc';

export interface UserTableProps {
  users: UserRead[];
  pagination: PaginationMeta | null;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSize?: number;
  onEditUser: (user: UserRead) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
}

export function UserTable({
  users,
  pagination,
  isLoading = false,
  onPageChange,
  onPageSizeChange,
  pageSize = 20,
  onEditUser,
  searchValue,
  onSearchChange,
}: UserTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Client-side filtering by email
  const filteredUsers = useMemo(() => {
    if (!searchValue.trim()) return users;
    const search = searchValue.toLowerCase();
    return users.filter((user) => user.email.toLowerCase().includes(search));
  }, [users, searchValue]);

  // Client-side sorting
  const sortedUsers = useMemo(() => {
    return [...filteredUsers].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'email':
          comparison = a.email.localeCompare(b.email);
          break;
        case 'is_active':
          comparison = Number(a.is_active) - Number(b.is_active);
          break;
        case 'is_superuser':
          comparison = Number(a.is_superuser) - Number(b.is_superuser);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'last_active':
          const aTime = a.last_active ? new Date(a.last_active).getTime() : 0;
          const bTime = b.last_active ? new Date(b.last_active).getTime() : 0;
          comparison = aTime - bTime;
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredUsers, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
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

  const totalPages = pagination?.total_pages ?? 1;
  const currentPage = pagination?.page ?? 1;
  const total = pagination?.total ?? sortedUsers.length;
  const hasPrevious = currentPage > 1;
  const hasNext = currentPage < totalPages;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading users...</p>
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
          placeholder="Search by email..."
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
          aria-label="Search users by email"
        />
      </div>

      {/* Pagination Bar - Top */}
      <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
        <div className="flex items-center gap-4">
          {/* Page Size Selector */}
          {onPageSizeChange && (
            <div className="flex items-center gap-2">
              <label htmlFor="user-page-size" className="text-sm text-muted-foreground">
                Show
              </label>
              <Select
                value={pageSize.toString()}
                onValueChange={(value) => onPageSizeChange(parseInt(value, 10))}
              >
                <SelectTrigger id="user-page-size" className="w-[80px]">
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
            Showing <span className="font-medium">{sortedUsers.length}</span> of{' '}
            <span className="font-medium">{total}</span> users
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!hasPrevious}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground px-2">
            Page <span className="font-medium">{currentPage}</span> of{' '}
            <span className="font-medium">{totalPages}</span>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!hasNext}
          >
            Next
          </Button>
        </div>
      </div>

      {sortedUsers.length === 0 ? (
        <div className="flex h-64 items-center justify-center rounded-lg border bg-card">
          <div className="text-center">
            <p className="text-lg font-medium">No users found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchValue ? 'Try adjusting your search term' : 'No users in the system yet'}
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
                    onClick={() => handleSort('email')}
                  >
                    <div className="flex items-center">
                      Email
                      {renderSortIcon('email')}
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
                    onClick={() => handleSort('is_superuser')}
                  >
                    <div className="flex items-center">
                      Role
                      {renderSortIcon('is_superuser')}
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
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground cursor-pointer hover:bg-muted/80"
                    onClick={() => handleSort('last_active')}
                  >
                    <div className="flex items-center">
                      Last Active
                      {renderSortIcon('last_active')}
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
                {sortedUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-muted/50">
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium">
                      {user.email}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      {user.is_active ? (
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
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      {user.is_superuser ? (
                        <Badge
                          data-testid="role-badge-admin"
                          className="bg-purple-500/20 text-purple-600 border-purple-500/30 hover:bg-purple-500/30"
                        >
                          Admin
                        </Badge>
                      ) : (
                        <Badge data-testid="role-badge-user" variant="secondary">
                          User
                        </Badge>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(user.last_active)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditUser(user)}
                        className="text-primary hover:text-primary/80"
                        aria-label={`Edit ${user.email}`}
                      >
                        <Pencil className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
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
