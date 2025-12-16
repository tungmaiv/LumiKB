/**
 * Modal for adding group permission to a Knowledge Base
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.2)
 */

"use client";

import React, { useState, useCallback, useMemo } from "react";
import { Loader2, Search, Users } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PermissionLevel, PermissionCreate } from "@/types/permission";
import { PERMISSION_LEVELS } from "@/types/permission";
import type { Group } from "@/types/group";

export interface AddGroupPermissionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGrantPermission: (data: PermissionCreate) => Promise<void>;
  isGranting?: boolean;
  groups: Group[];
  groupsLoading?: boolean;
  /** Group IDs that already have permissions (to exclude from selection) */
  existingGroupIds?: string[];
}

export function AddGroupPermissionModal({
  open,
  onOpenChange,
  onGrantPermission,
  isGranting = false,
  groups,
  groupsLoading = false,
  existingGroupIds = [],
}: AddGroupPermissionModalProps) {
  const [selectedGroupId, setSelectedGroupId] = useState<string>("");
  const [permissionLevel, setPermissionLevel] = useState<PermissionLevel>("READ");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Filter groups: exclude already-permitted groups and apply search
  const filteredGroups = useMemo(() => {
    const availableGroups = groups.filter(
      (group) => !existingGroupIds.includes(group.id) && group.is_active
    );

    if (!searchQuery.trim()) {
      return availableGroups;
    }

    const query = searchQuery.toLowerCase();
    return availableGroups.filter(
      (group) =>
        group.name.toLowerCase().includes(query) ||
        group.description?.toLowerCase().includes(query)
    );
  }, [groups, existingGroupIds, searchQuery]);

  const selectedGroup = useMemo(
    () => groups.find((g) => g.id === selectedGroupId),
    [groups, selectedGroupId]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      if (!selectedGroupId) {
        setError("Please select a group");
        return;
      }

      try {
        await onGrantPermission({
          group_id: selectedGroupId,
          permission_level: permissionLevel,
        });
        // Reset form on success
        setSelectedGroupId("");
        setPermissionLevel("READ");
        setSearchQuery("");
        onOpenChange(false);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to grant permission");
        }
      }
    },
    [selectedGroupId, permissionLevel, onGrantPermission, onOpenChange]
  );

  const handleClose = useCallback(() => {
    setSelectedGroupId("");
    setPermissionLevel("READ");
    setSearchQuery("");
    setError(null);
    onOpenChange(false);
  }, [onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Add Group Permission</DialogTitle>
          <DialogDescription>
            Grant a group access to this Knowledge Base. All members of the group
            will inherit this permission level.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Group Search & Selection */}
          <div className="space-y-2">
            <Label htmlFor="group-search">Select Group</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="group-search"
                type="text"
                placeholder="Search by name or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Group list */}
            <div className="max-h-48 overflow-y-auto rounded-md border">
              {groupsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">
                    Loading groups...
                  </span>
                </div>
              ) : filteredGroups.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {searchQuery
                    ? "No groups found matching your search"
                    : "No available groups to add"}
                </div>
              ) : (
                <div className="divide-y">
                  {filteredGroups.map((group) => (
                    <button
                      key={group.id}
                      type="button"
                      onClick={() => setSelectedGroupId(group.id)}
                      className={`flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-accent ${
                        selectedGroupId === group.id ? "bg-accent" : ""
                      }`}
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                        <Users className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="truncate text-sm font-medium">
                          {group.name}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {group.member_count} member
                          {group.member_count !== 1 ? "s" : ""}
                          {group.description && ` • ${group.description}`}
                        </p>
                      </div>
                      {selectedGroupId === group.id && (
                        <div className="h-2 w-2 rounded-full bg-primary" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedGroup && (
              <p className="text-sm text-muted-foreground">
                Selected: <span className="font-medium">{selectedGroup.name}</span>
                {" "}({selectedGroup.member_count} member
                {selectedGroup.member_count !== 1 ? "s" : ""})
              </p>
            )}
          </div>

          {/* Permission Level Selection */}
          <div className="space-y-2">
            <Label htmlFor="permission-level">Permission Level</Label>
            <Select
              value={permissionLevel}
              onValueChange={(value) =>
                setPermissionLevel(value as PermissionLevel)
              }
            >
              <SelectTrigger id="permission-level" className="w-full">
                <SelectValue placeholder="Select permission level" />
              </SelectTrigger>
              <SelectContent>
                {PERMISSION_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    <div className="flex flex-col">
                      <span>{level.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {level.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Note: Users with direct permissions will override group permissions.
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isGranting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isGranting || !selectedGroupId}
            >
              {isGranting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Grant Permission
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
