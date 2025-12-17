/**
 * Edit user modal component with status toggle
 * Story 5.18: User Management UI (AC-5.18.3, AC-5.18.4)
 */

'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';
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
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { UserRead, AdminUserUpdate } from '@/types/user';

export interface EditUserModalProps {
  user: UserRead | null;
  currentUserId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateUser: (id: string, data: AdminUserUpdate) => Promise<void>;
  isUpdating?: boolean;
}

export function EditUserModal({
  user,
  currentUserId,
  open,
  onOpenChange,
  onUpdateUser,
  isUpdating = false,
}: EditUserModalProps) {
  const [isActive, setIsActive] = React.useState(user?.is_active ?? true);
  const [error, setError] = React.useState<string | null>(null);

  // Reset state when user changes
  React.useEffect(() => {
    if (user) {
      setIsActive(user.is_active);
      setError(null);
    }
  }, [user]);

  const isSelf = user?.id === currentUserId;

  const handleSave = async () => {
    if (!user) return;

    try {
      setError(null);
      await onUpdateUser(user.id, { is_active: isActive });
      onOpenChange(false);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to update user');
      }
    }
  };

  const handleClose = () => {
    setError(null);
    onOpenChange(false);
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Update user status. Role changes require backend configuration.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">{error}</div>
          )}

          {/* Email (read-only) */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">Email</Label>
            <p className="text-sm font-medium">{user.email}</p>
          </div>

          {/* Role (read-only) */}
          <div className="space-y-2">
            <Label className="text-muted-foreground">Role</Label>
            <div>
              {user.is_superuser ? (
                <Badge className="bg-purple-500/20 text-purple-600 border-purple-500/30">
                  Admin
                </Badge>
              ) : (
                <Badge variant="secondary">User</Badge>
              )}
              <p className="mt-1 text-xs text-muted-foreground">
                Role changes are not supported via this interface
              </p>
            </div>
          </div>

          {/* Status Toggle */}
          <div className="space-y-2">
            <Label htmlFor="status-toggle">Account Status</Label>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <p className="text-sm font-medium">{isActive ? 'Active' : 'Inactive'}</p>
                <p className="text-xs text-muted-foreground">
                  {isActive
                    ? 'User can log in and access the system'
                    : 'User is blocked from logging in'}
                </p>
              </div>

              {isSelf ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div>
                      <Switch
                        id="status-toggle"
                        checked={isActive}
                        disabled
                        aria-label="Cannot deactivate your own account"
                      />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>You cannot deactivate your own account</p>
                  </TooltipContent>
                </Tooltip>
              ) : (
                <Switch
                  id="status-toggle"
                  checked={isActive}
                  onCheckedChange={setIsActive}
                  disabled={isUpdating}
                  aria-label={`Set user status to ${isActive ? 'inactive' : 'active'}`}
                />
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose} disabled={isUpdating}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isUpdating || user.is_active === isActive}>
            {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
