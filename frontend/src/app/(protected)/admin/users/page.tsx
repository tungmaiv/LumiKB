/**
 * User management page for admins
 * Story 5.18: User Management UI (AC-5.18.1, AC-5.18.5)
 */

'use client';

import { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Users, Plus } from 'lucide-react';
import { toast } from 'sonner';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { UserTable } from '@/components/admin/user-table';
import { CreateUserModal } from '@/components/admin/create-user-modal';
import { EditUserModal } from '@/components/admin/edit-user-modal';
import { useUsers } from '@/hooks/useUsers';
import { useDebounce } from '@/hooks/useDebounce';
import { useAuthStore } from '@/lib/stores/auth-store';
import type { UserRead, UserCreate, AdminUserUpdate } from '@/types/user';

export default function UsersPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user: currentUser } = useAuthStore();

  // URL state
  const pageParam = searchParams.get('page');
  const pageSizeParam = searchParams.get('pageSize');
  const searchParam = searchParams.get('search') || '';

  const [page, setPage] = useState(pageParam ? parseInt(pageParam, 10) : 1);
  const [pageSize, setPageSize] = useState(pageSizeParam ? parseInt(pageSizeParam, 10) : 20);
  const [search, setSearch] = useState(searchParam);
  const debouncedSearch = useDebounce(search, 300);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserRead | null>(null);

  // Data fetching
  const { users, pagination, isLoading, error, createUser, updateUser, isCreating, isUpdating } =
    useUsers({ page, pageSize });

  // Update URL when page changes
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    const params = new URLSearchParams(searchParams.toString());
    params.set('page', newPage.toString());
    if (debouncedSearch) {
      params.set('search', debouncedSearch);
    } else {
      params.delete('search');
    }
    router.replace(`/admin/users?${params.toString()}`, { scroll: false });
  };

  // Update URL when page size changes
  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to page 1 when page size changes
    const params = new URLSearchParams(searchParams.toString());
    params.set('page', '1');
    params.set('pageSize', newPageSize.toString());
    router.replace(`/admin/users?${params.toString()}`, { scroll: false });
  };

  // Update URL when search changes
  const handleSearchChange = (value: string) => {
    setSearch(value);
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set('search', value);
    } else {
      params.delete('search');
    }
    params.set('page', '1');
    setPage(1);
    router.replace(`/admin/users?${params.toString()}`, { scroll: false });
  };

  const handleEditUser = (user: UserRead) => {
    setEditingUser(user);
    setEditModalOpen(true);
  };

  const handleCreateUser = async (data: UserCreate) => {
    await createUser(data);
    toast.success('User created successfully');
  };

  const handleUpdateUser = async (id: string, data: AdminUserUpdate) => {
    await updateUser(id, data);
    const action = data.is_active ? 'activated' : 'deactivated';
    toast.success(`User ${action} successfully`);
  };

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">User Management</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load users'}
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
              <Users className="h-8 w-8" />
              <h1 className="text-2xl font-bold">User Management</h1>
            </div>
            <p className="text-sm text-muted-foreground mt-1">View and manage user accounts</p>
          </div>
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add User
          </Button>
        </div>

        {/* User Table */}
        <UserTable
          users={users}
          pagination={pagination}
          isLoading={isLoading}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          pageSize={pageSize}
          onEditUser={handleEditUser}
          searchValue={search}
          onSearchChange={handleSearchChange}
        />

        {/* Create User Modal */}
        <CreateUserModal
          open={createModalOpen}
          onOpenChange={setCreateModalOpen}
          onCreateUser={handleCreateUser}
          isCreating={isCreating}
        />

        {/* Edit User Modal */}
        <EditUserModal
          user={editingUser}
          currentUserId={currentUser?.id ?? ''}
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          onUpdateUser={handleUpdateUser}
          isUpdating={isUpdating}
        />
      </div>
    </DashboardLayout>
  );
}
