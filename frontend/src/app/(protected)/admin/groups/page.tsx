/**
 * Group management page for admins
 * Story 5.19: Group Management (AC-5.19.2, AC-5.19.4, AC-5.19.5)
 */

'use client';

import { useState, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Users2, Plus } from 'lucide-react';
import { toast } from 'sonner';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { GroupTable } from '@/components/admin/group-table';
import { CreateGroupModal } from '@/components/admin/create-group-modal';
import { EditGroupModal } from '@/components/admin/edit-group-modal';
import { GroupMembershipModal } from '@/components/admin/group-membership-modal';
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
import { useGroups, useGroup } from '@/hooks/useGroups';
import { useUsers } from '@/hooks/useUsers';
import { useDebounce } from '@/hooks/useDebounce';
import type { Group, GroupCreate, GroupUpdate } from '@/types/group';

export default function GroupsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL state
  const pageParam = searchParams.get('page');
  const searchParam = searchParams.get('search') || '';

  const [page, setPage] = useState(pageParam ? parseInt(pageParam, 10) : 1);
  const [search, setSearch] = useState(searchParam);
  const debouncedSearch = useDebounce(search, 300);

  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [membershipModalOpen, setMembershipModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Selected group for modals
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null);

  // Data fetching
  const {
    groups,
    total,
    totalPages,
    isLoading,
    error,
    createGroup,
    updateGroup,
    deleteGroup,
    isCreating,
    isUpdating,
    isDeleting,
  } = useGroups({ page, pageSize: 20, search: debouncedSearch });

  // Fetch single group for membership modal OR expanded row
  // We need to fetch when either the modal is open OR a row is expanded
  const groupIdToFetch = membershipModalOpen
    ? selectedGroup?.id ?? null
    : expandedGroupId;

  const {
    group: membershipGroup,
    isLoading: isLoadingGroup,
    addMembers,
    removeMember,
    isAddingMembers,
    isRemovingMember,
    refetch: refetchGroup,
  } = useGroup(groupIdToFetch);

  // Fetch all ACTIVE users for membership modal (is_active=true filters out inactive users)
  // Note: Backend limits pageSize to max 100
  const { users: allUsers } = useUsers({ page: 1, pageSize: 100, isActive: true });

  // Update URL when page changes
  const handlePageChange = useCallback(
    (newPage: number) => {
      setPage(newPage);
      const params = new URLSearchParams(searchParams.toString());
      params.set('page', newPage.toString());
      if (debouncedSearch) {
        params.set('search', debouncedSearch);
      } else {
        params.delete('search');
      }
      router.replace(`/admin/groups?${params.toString()}`, { scroll: false });
    },
    [searchParams, debouncedSearch, router]
  );

  // Update URL when search changes
  const handleSearchChange = useCallback(
    (value: string) => {
      setSearch(value);
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set('search', value);
      } else {
        params.delete('search');
      }
      params.set('page', '1');
      setPage(1);
      router.replace(`/admin/groups?${params.toString()}`, { scroll: false });
    },
    [searchParams, router]
  );

  // Modal handlers
  const handleEditGroup = (group: Group) => {
    setSelectedGroup(group);
    setEditModalOpen(true);
  };

  const handleDeleteGroup = (group: Group) => {
    setSelectedGroup(group);
    setDeleteDialogOpen(true);
  };

  const handleManageMembers = (group: Group) => {
    setSelectedGroup(group);
    setMembershipModalOpen(true);
  };

  const handleExpandGroup = (groupId: string | null) => {
    setExpandedGroupId(groupId);
  };

  // CRUD operations
  const handleCreateGroup = async (data: GroupCreate) => {
    await createGroup(data);
    toast.success('Group created successfully');
  };

  const handleUpdateGroup = async (id: string, data: GroupUpdate) => {
    await updateGroup(id, data);
    toast.success('Group updated successfully');
  };

  const handleConfirmDelete = async () => {
    if (!selectedGroup) return;

    try {
      await deleteGroup(selectedGroup.id);
      toast.success('Group deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedGroup(null);
    } catch (err) {
      if (err instanceof Error) {
        toast.error(err.message);
      } else {
        toast.error('Failed to delete group');
      }
    }
  };

  const handleAddMembers = async (userIds: string[]) => {
    await addMembers(userIds);
    refetchGroup();
    toast.success(`${userIds.length} member(s) added successfully`);
  };

  const handleRemoveMember = async (userId: string) => {
    await removeMember(userId);
    refetchGroup();
    toast.success('Member removed successfully');
  };

  // Get members for expanded row
  const expandedMembers =
    expandedGroupId && membershipGroup?.id === expandedGroupId ? membershipGroup.members : [];

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Group Management</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load groups'}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Users2 className="h-8 w-8" />
              <h1 className="text-2xl font-bold">Group Management</h1>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Create and manage user groups for organizing permissions
            </p>
          </div>
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Group
          </Button>
        </div>

        {/* Group Table */}
        <GroupTable
          groups={groups}
          total={total}
          page={page}
          totalPages={totalPages}
          isLoading={isLoading}
          onPageChange={handlePageChange}
          onEditGroup={handleEditGroup}
          onDeleteGroup={handleDeleteGroup}
          onManageMembers={handleManageMembers}
          searchValue={search}
          onSearchChange={handleSearchChange}
          expandedGroup={expandedGroupId}
          onExpandGroup={handleExpandGroup}
          expandedMembers={expandedMembers}
          isLoadingMembers={isLoadingGroup && expandedGroupId !== null}
        />

        {/* Create Group Modal */}
        <CreateGroupModal
          open={createModalOpen}
          onOpenChange={setCreateModalOpen}
          onCreateGroup={handleCreateGroup}
          isCreating={isCreating}
        />

        {/* Edit Group Modal */}
        <EditGroupModal
          group={selectedGroup}
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          onUpdateGroup={handleUpdateGroup}
          isUpdating={isUpdating}
        />

        {/* Group Membership Modal */}
        <GroupMembershipModal
          group={selectedGroup}
          members={membershipGroup?.members ?? []}
          allUsers={allUsers}
          open={membershipModalOpen}
          onOpenChange={setMembershipModalOpen}
          onAddMembers={handleAddMembers}
          onRemoveMember={handleRemoveMember}
          isLoadingMembers={isLoadingGroup}
          isAddingMembers={isAddingMembers}
          isRemovingMember={isRemovingMember}
        />

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Group</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete &quot;{selectedGroup?.name}&quot;? This will
                deactivate the group and remove all member associations. This action can be undone
                by reactivating the group.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete Group'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </DashboardLayout>
  );
}
