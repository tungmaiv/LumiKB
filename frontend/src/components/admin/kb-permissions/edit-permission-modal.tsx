/**
 * Modal for editing a KB permission level
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.3)
 */

'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Loader2, User, Users, AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import type { PermissionLevel, PermissionExtended, PermissionUpdate } from '@/types/permission';
import { PERMISSION_LEVELS } from '@/types/permission';

export interface EditPermissionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  permission: PermissionExtended | null;
  onUpdatePermission: (id: string, data: PermissionUpdate) => Promise<void>;
  onDeletePermission: (permission: PermissionExtended) => Promise<void>;
  isUpdating?: boolean;
  isDeleting?: boolean;
}

export function EditPermissionModal({
  open,
  onOpenChange,
  permission,
  onUpdatePermission,
  onDeletePermission,
  isUpdating = false,
  isDeleting = false,
}: EditPermissionModalProps) {
  const [permissionLevel, setPermissionLevel] = useState<PermissionLevel>('READ');
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const lastPermissionId = useRef<string | null>(null);

  // Update permission level when permission changes (avoiding effect)
  if (permission && permission.id !== lastPermissionId.current) {
    lastPermissionId.current = permission.id;
    if (permissionLevel !== permission.permission_level) {
      setPermissionLevel(permission.permission_level);
    }
  }

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      if (!permission) return;

      // Skip if no change
      if (permissionLevel === permission.permission_level) {
        onOpenChange(false);
        return;
      }

      try {
        await onUpdatePermission(permission.id, {
          permission_level: permissionLevel,
        });
        onOpenChange(false);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to update permission');
        }
      }
    },
    [permission, permissionLevel, onUpdatePermission, onOpenChange]
  );

  const handleDelete = useCallback(async () => {
    if (!permission) return;

    try {
      await onDeletePermission(permission);
      setShowDeleteConfirm(false);
      onOpenChange(false);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to revoke permission');
      }
      setShowDeleteConfirm(false);
    }
  }, [permission, onDeletePermission, onOpenChange]);

  const handleClose = useCallback(() => {
    setError(null);
    onOpenChange(false);
  }, [onOpenChange]);

  if (!permission) return null;

  const isUser = permission.entity_type === 'user';
  const EntityIcon = isUser ? User : Users;

  return (
    <>
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Edit Permission</DialogTitle>
            <DialogDescription>
              Update or revoke the permission for this {isUser ? 'user' : 'group'}.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {/* Entity Info */}
            <div className="flex items-center gap-3 rounded-lg border p-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                <EntityIcon className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate font-medium">{permission.entity_name}</p>
                <p className="text-sm text-muted-foreground capitalize">{permission.entity_type}</p>
              </div>
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
              {!isUser && (
                <p className="text-xs text-muted-foreground">
                  Note: Users with direct permissions will override group permissions.
                </p>
              )}
            </div>

            <DialogFooter className="flex-col gap-2 sm:flex-row">
              <Button
                type="button"
                variant="destructive"
                onClick={() => setShowDeleteConfirm(true)}
                disabled={isUpdating || isDeleting}
                className="w-full sm:w-auto"
              >
                {isDeleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Revoke Access
              </Button>
              <div className="flex flex-1 justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isUpdating || isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={
                    isUpdating || isDeleting || permissionLevel === permission.permission_level
                  }
                >
                  {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save Changes
                </Button>
              </div>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Revoke Permission
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to revoke access for{' '}
              <span className="font-medium">{permission.entity_name}</span>?
              {isUser
                ? ' This user will no longer have direct access to this Knowledge Base.'
                : ' All members of this group will lose their group-based access to this Knowledge Base.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Revoke Access
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
