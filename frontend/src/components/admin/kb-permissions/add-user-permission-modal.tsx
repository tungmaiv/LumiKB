/**
 * Modal for adding user permission to a Knowledge Base
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.2)
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Loader2, Search, User } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { PermissionLevel, PermissionCreate } from '@/types/permission';
import { PERMISSION_LEVELS } from '@/types/permission';
import type { UserRead } from '@/types/user';

export interface AddUserPermissionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGrantPermission: (data: PermissionCreate) => Promise<void>;
  isGranting?: boolean;
  users: UserRead[];
  usersLoading?: boolean;
  /** User IDs that already have permissions (to exclude from selection) */
  existingUserIds?: string[];
}

export function AddUserPermissionModal({
  open,
  onOpenChange,
  onGrantPermission,
  isGranting = false,
  users,
  usersLoading = false,
  existingUserIds = [],
}: AddUserPermissionModalProps) {
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [permissionLevel, setPermissionLevel] = useState<PermissionLevel>('READ');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Filter users: exclude already-permitted users and apply search
  // Note: users prop is already filtered to active users only via API (is_active=true)
  const filteredUsers = useMemo(() => {
    const availableUsers = users.filter((user) => !existingUserIds.includes(user.id));

    if (!searchQuery.trim()) {
      return availableUsers;
    }

    const query = searchQuery.toLowerCase();
    return availableUsers.filter((user) => user.email.toLowerCase().includes(query));
  }, [users, existingUserIds, searchQuery]);

  const selectedUser = useMemo(
    () => users.find((u) => u.id === selectedUserId),
    [users, selectedUserId]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      if (!selectedUserId) {
        setError('Please select a user');
        return;
      }

      try {
        await onGrantPermission({
          user_id: selectedUserId,
          permission_level: permissionLevel,
        });
        // Reset form on success
        setSelectedUserId('');
        setPermissionLevel('READ');
        setSearchQuery('');
        onOpenChange(false);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to grant permission');
        }
      }
    },
    [selectedUserId, permissionLevel, onGrantPermission, onOpenChange]
  );

  const handleClose = useCallback(() => {
    setSelectedUserId('');
    setPermissionLevel('READ');
    setSearchQuery('');
    setError(null);
    onOpenChange(false);
  }, [onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Add User Permission</DialogTitle>
          <DialogDescription>
            Grant a user access to this Knowledge Base. Select a user and choose their permission
            level.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">{error}</div>
          )}

          {/* User Search & Selection */}
          <div className="space-y-2">
            <Label htmlFor="user-search">Select User</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="user-search"
                type="text"
                placeholder="Search by email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* User list */}
            <div className="max-h-48 overflow-y-auto rounded-md border">
              {usersLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Loading users...</span>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {searchQuery
                    ? 'No users found matching your search'
                    : 'No available users to add'}
                </div>
              ) : (
                <div className="divide-y">
                  {filteredUsers.map((user) => (
                    <button
                      key={user.id}
                      type="button"
                      onClick={() => setSelectedUserId(user.id)}
                      className={`flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-accent ${
                        selectedUserId === user.id ? 'bg-accent' : ''
                      }`}
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="truncate text-sm font-medium">{user.email}</p>
                        <p className="text-xs text-muted-foreground">
                          {user.is_superuser ? 'Admin' : 'User'}
                        </p>
                      </div>
                      {selectedUserId === user.id && (
                        <div className="h-2 w-2 rounded-full bg-primary" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedUser && (
              <p className="text-sm text-muted-foreground">
                Selected: <span className="font-medium">{selectedUser.email}</span>
              </p>
            )}
          </div>

          {/* Permission Level Selection */}
          <div className="space-y-2">
            <Label htmlFor="permission-level">Permission Level</Label>
            <Select
              value={permissionLevel}
              onValueChange={(value) => setPermissionLevel(value as PermissionLevel)}
            >
              <SelectTrigger id="permission-level" className="w-full">
                <SelectValue placeholder="Select permission level" />
              </SelectTrigger>
              <SelectContent>
                {PERMISSION_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    <div className="flex flex-col">
                      <span>{level.label}</span>
                      <span className="text-xs text-muted-foreground">{level.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isGranting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isGranting || !selectedUserId}>
              {isGranting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Grant Permission
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
