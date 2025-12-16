/**
 * Group membership modal for managing group members
 * Story 5.19: Group Management (AC-5.19.4)
 */

'use client';

import React, { useState, useMemo } from 'react';
import { Loader2, Search, UserMinus, UserPlus, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import type { Group, GroupMember } from '@/types/group';
import type { UserRead } from '@/types/user';

export interface GroupMembershipModalProps {
  group: Group | null;
  members: GroupMember[];
  allUsers: UserRead[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddMembers: (userIds: string[]) => Promise<void>;
  onRemoveMember: (userId: string) => Promise<void>;
  isLoadingMembers?: boolean;
  isAddingMembers?: boolean;
  isRemovingMember?: boolean;
}

export function GroupMembershipModal({
  group,
  members,
  allUsers,
  open,
  onOpenChange,
  onAddMembers,
  onRemoveMember,
  isLoadingMembers = false,
  isAddingMembers = false,
  isRemovingMember = false,
}: GroupMembershipModalProps) {
  const [memberSearch, setMemberSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (!open) {
      setMemberSearch('');
      setUserSearch('');
      setSelectedUsers([]);
      setError(null);
      setRemovingUserId(null);
    }
  }, [open]);

  // Get member IDs for filtering
  const memberIds = useMemo(() => new Set(members.map((m) => m.id)), [members]);

  // Filter current members by search
  const filteredMembers = useMemo(() => {
    if (!memberSearch.trim()) return members;
    const search = memberSearch.toLowerCase();
    return members.filter((m) => m.email.toLowerCase().includes(search));
  }, [members, memberSearch]);

  // Filter available users (not already members)
  // Note: allUsers is already filtered to active users only via API (is_active=true)
  const availableUsers = useMemo(() => {
    const filtered = allUsers.filter((u) => !memberIds.has(u.id));
    if (!userSearch.trim()) return filtered;
    const search = userSearch.toLowerCase();
    return filtered.filter((u) => u.email.toLowerCase().includes(search));
  }, [allUsers, memberIds, userSearch]);

  const handleToggleUser = (userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleAddMembers = async () => {
    if (selectedUsers.length === 0) return;

    try {
      setError(null);
      await onAddMembers(selectedUsers);
      setSelectedUsers([]);
      setUserSearch('');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to add members');
      }
    }
  };

  const handleRemoveMember = async (userId: string) => {
    try {
      setError(null);
      setRemovingUserId(userId);
      await onRemoveMember(userId);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to remove member');
      }
    } finally {
      setRemovingUserId(null);
    }
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  if (!group) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Manage Members: {group.name}</DialogTitle>
          <DialogDescription>Add or remove users from this group.</DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
            <Button
              variant="ghost"
              size="sm"
              className="ml-2 h-auto p-0"
              onClick={() => setError(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Current Members Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Current Members ({members.length})</h4>
            </div>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search members..."
                value={memberSearch}
                onChange={(e) => setMemberSearch(e.target.value)}
                className="pl-10"
                aria-label="Search current members"
              />
            </div>

            <ScrollArea className="h-[250px] rounded-md border p-2">
              {isLoadingMembers ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading members...
                </div>
              ) : filteredMembers.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {memberSearch ? 'No members match your search' : 'No members in this group'}
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredMembers.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between rounded-md p-2 hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="truncate text-sm">{member.email}</span>
                        {!member.is_active && (
                          <Badge variant="secondary" className="text-xs">
                            inactive
                          </Badge>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-destructive hover:text-destructive/80"
                        onClick={() => handleRemoveMember(member.id)}
                        disabled={isRemovingMember && removingUserId === member.id}
                        aria-label={`Remove ${member.email} from group`}
                      >
                        {isRemovingMember && removingUserId === member.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <UserMinus className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Add Members Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Add Members</h4>
              {selectedUsers.length > 0 && (
                <Badge variant="secondary">{selectedUsers.length} selected</Badge>
              )}
            </div>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search available users..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="pl-10"
                aria-label="Search available users"
              />
            </div>

            <ScrollArea className="h-[200px] rounded-md border p-2">
              {availableUsers.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {userSearch
                    ? 'No users match your search'
                    : 'All active users are already members'}
                </div>
              ) : (
                <div className="space-y-1">
                  {availableUsers.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center gap-2 rounded-md p-2 hover:bg-muted/50"
                    >
                      <Checkbox
                        id={`user-${user.id}`}
                        checked={selectedUsers.includes(user.id)}
                        onCheckedChange={() => handleToggleUser(user.id)}
                        aria-label={`Select ${user.email}`}
                      />
                      <Label
                        htmlFor={`user-${user.id}`}
                        className="flex-1 cursor-pointer truncate text-sm"
                      >
                        {user.email}
                      </Label>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>

            <Button
              onClick={handleAddMembers}
              disabled={selectedUsers.length === 0 || isAddingMembers}
              className="w-full"
            >
              {isAddingMembers ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <UserPlus className="mr-2 h-4 w-4" />
              )}
              Add {selectedUsers.length > 0 ? `${selectedUsers.length} ` : ''}Member
              {selectedUsers.length !== 1 ? 's' : ''}
            </Button>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={handleClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
