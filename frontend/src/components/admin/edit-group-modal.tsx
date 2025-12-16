/**
 * Edit group modal component with form validation and status toggle
 * Story 5.19: Group Management (AC-5.19.3)
 */

'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import type { Group, GroupUpdate } from '@/types/group';

const editGroupSchema = z.object({
  name: z
    .string()
    .min(1, 'Group name is required')
    .max(255, 'Group name must be at most 255 characters'),
  description: z
    .string()
    .max(2000, 'Description must be at most 2000 characters')
    .optional(),
  is_active: z.boolean(),
});

type EditGroupFormData = z.infer<typeof editGroupSchema>;

export interface EditGroupModalProps {
  group: Group | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdateGroup: (id: string, data: GroupUpdate) => Promise<void>;
  isUpdating?: boolean;
}

export function EditGroupModal({
  group,
  open,
  onOpenChange,
  onUpdateGroup,
  isUpdating = false,
}: EditGroupModalProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setError,
    setValue,
    watch,
  } = useForm<EditGroupFormData>({
    resolver: zodResolver(editGroupSchema),
    defaultValues: {
      name: '',
      description: '',
      is_active: true,
    },
  });

  const isActive = watch('is_active');

  // Reset form when group changes
  React.useEffect(() => {
    if (group) {
      reset({
        name: group.name,
        description: group.description ?? '',
        is_active: group.is_active,
      });
    }
  }, [group, reset]);

  const onSubmit = async (data: EditGroupFormData) => {
    if (!group) return;

    try {
      // Only send fields that changed
      const updates: GroupUpdate = {};
      if (data.name !== group.name) updates.name = data.name;
      // Convert empty string to null for comparison and API
      const newDescription = data.description || null;
      if (newDescription !== group.description) updates.description = newDescription;
      if (data.is_active !== group.is_active) updates.is_active = data.is_active;

      // If nothing changed, just close
      if (Object.keys(updates).length === 0) {
        onOpenChange(false);
        return;
      }

      await onUpdateGroup(group.id, updates);
      onOpenChange(false);
    } catch (error) {
      if (error instanceof Error) {
        if (error.message.includes('already exists')) {
          setError('name', { message: 'A group with this name already exists' });
        } else {
          setError('root', { message: error.message });
        }
      }
    }
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  if (!group) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Group</DialogTitle>
          <DialogDescription>
            Update group details and status. Changes take effect immediately.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {errors.root && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {errors.root.message}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="edit-name">Group Name</Label>
            <Input
              id="edit-name"
              type="text"
              {...register('name')}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? 'edit-name-error' : undefined}
            />
            {errors.name && (
              <p id="edit-name-error" className="text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-description">Description (optional)</Label>
            <Textarea
              id="edit-description"
              rows={3}
              {...register('description')}
              aria-invalid={!!errors.description}
              aria-describedby={errors.description ? 'edit-description-error' : undefined}
            />
            {errors.description && (
              <p id="edit-description-error" className="text-sm text-destructive">
                {errors.description.message}
              </p>
            )}
          </div>

          {/* Status Toggle */}
          <div className="space-y-2">
            <Label htmlFor="status-toggle">Group Status</Label>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <p className="text-sm font-medium">{isActive ? 'Active' : 'Inactive'}</p>
                <p className="text-xs text-muted-foreground">
                  {isActive
                    ? 'Group is active and visible'
                    : 'Group is deactivated (soft deleted)'}
                </p>
              </div>
              <Switch
                id="status-toggle"
                checked={isActive}
                onCheckedChange={(checked) => setValue('is_active', checked, { shouldDirty: true })}
                disabled={isUpdating}
                aria-label={`Set group status to ${isActive ? 'inactive' : 'active'}`}
              />
            </div>
          </div>

          <div className="text-xs text-muted-foreground">
            Members: {group.member_count} | Created:{' '}
            {new Date(group.created_at).toLocaleDateString()}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isUpdating}>
              Cancel
            </Button>
            <Button type="submit" disabled={isUpdating || !isDirty}>
              {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
