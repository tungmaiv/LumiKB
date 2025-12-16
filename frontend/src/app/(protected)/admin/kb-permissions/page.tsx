/**
 * KB Permissions management page for admins
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1, AC-5.20.2, AC-5.20.3, AC-5.20.6)
 */

"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Shield, UserPlus, Users } from "lucide-react";
import { toast } from "sonner";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  KBPermissionsTable,
  AddUserPermissionModal,
  AddGroupPermissionModal,
  EditPermissionModal,
} from "@/components/admin/kb-permissions";
import { useKBPermissions } from "@/hooks/useKBPermissions";
import { useUsers } from "@/hooks/useUsers";
import { useGroups } from "@/hooks/useGroups";
import { useKBStore } from "@/lib/stores/kb-store";
import type { PermissionExtended, PermissionCreate, PermissionUpdate } from "@/types/permission";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  status: string;
}

export default function KBPermissionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // KB store for sidebar sync
  const { kbs: storeKbs, activeKb, setActiveKb, fetchKbs } = useKBStore();

  // KB selection state
  const [kbId, setKbId] = useState<string | null>(searchParams.get("kb_id"));
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loadingKBs, setLoadingKBs] = useState(true);

  // Pagination state
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [search, setSearch] = useState("");

  // Modal states
  const [addUserModalOpen, setAddUserModalOpen] = useState(false);
  const [addGroupModalOpen, setAddGroupModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedPermission, setSelectedPermission] = useState<PermissionExtended | null>(null);

  // Data fetching
  const {
    permissions,
    total,
    isLoading,
    error,
    grantPermission,
    updatePermission,
    revokeUserPermission,
    revokeGroupPermission,
    isGranting,
    isUpdating,
    isRevoking,
  } = useKBPermissions({
    kbId: kbId || "",
    page,
    limit,
    enabled: !!kbId,
  });

  // Fetch ACTIVE users and groups for add modals (is_active=true filters out inactive users)
  // Note: Backend limits pageSize to max 100
  const { users, isLoading: usersLoading } = useUsers({ page: 1, pageSize: 100, isActive: true });
  const { groups, isLoading: groupsLoading } = useGroups({ page: 1, pageSize: 100 });

  // Compute existing IDs to exclude from add modals
  const existingUserIds = useMemo(
    () =>
      permissions
        .filter((p) => p.entity_type === "user")
        .map((p) => p.entity_id),
    [permissions]
  );

  const existingGroupIds = useMemo(
    () =>
      permissions
        .filter((p) => p.entity_type === "group")
        .map((p) => p.entity_id),
    [permissions]
  );

  // Fetch knowledge bases for selector
  useEffect(() => {
    const fetchKnowledgeBases = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/`, {
          credentials: "include",
        });

        if (res.ok) {
          const response = await res.json();
          setKnowledgeBases(Array.isArray(response) ? response : response.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch knowledge bases:", err);
      } finally {
        setLoadingKBs(false);
      }
    };

    fetchKnowledgeBases();
    // Also fetch KBs into the store if not already loaded
    if (storeKbs.length === 0) {
      fetchKbs();
    }
  }, [storeKbs.length, fetchKbs]);

  // Sync KB selection with sidebar: when kbId changes, update sidebar's active KB
  useEffect(() => {
    if (kbId && storeKbs.length > 0) {
      const kbToSelect = storeKbs.find((kb) => kb.id === kbId);
      if (kbToSelect && activeKb?.id !== kbId) {
        setActiveKb(kbToSelect);
      }
    }
  }, [kbId, storeKbs, activeKb?.id, setActiveKb]);

  // Initialize from sidebar's active KB if no URL param provided
  useEffect(() => {
    if (!kbId && activeKb && !searchParams.get("kb_id")) {
      setKbId(activeKb.id);
      router.replace(`/admin/kb-permissions?kb_id=${activeKb.id}`);
    }
  }, [activeKb, kbId, searchParams, router]);

  // Get selected KB name
  const selectedKB = useMemo(
    () => knowledgeBases.find((kb) => kb.id === kbId),
    [knowledgeBases, kbId]
  );

  // Handlers
  const handleKBChange = useCallback(
    (newKbId: string) => {
      setKbId(newKbId);
      setPage(1);
      setSearch("");
      router.push(`/admin/kb-permissions?kb_id=${newKbId}`);

      // Sync with sidebar
      const kbToSelect = storeKbs.find((kb) => kb.id === newKbId);
      if (kbToSelect) {
        setActiveKb(kbToSelect);
      }
    },
    [router, storeKbs, setActiveKb]
  );

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    setPage(1);
  }, []);

  const handleLimitChange = useCallback((newLimit: number) => {
    setLimit(newLimit);
    setPage(1); // Reset to page 1 when limit changes
  }, []);

  const handleEditPermission = useCallback((permission: PermissionExtended) => {
    setSelectedPermission(permission);
    setEditModalOpen(true);
  }, []);

  const handleDeletePermission = useCallback(
    async (permission: PermissionExtended) => {
      try {
        if (permission.entity_type === "user") {
          await revokeUserPermission(permission.entity_id);
        } else {
          await revokeGroupPermission(permission.entity_id);
        }
        toast.success("Permission revoked successfully");
      } catch (err) {
        if (err instanceof Error) {
          toast.error(err.message);
        } else {
          toast.error("Failed to revoke permission");
        }
        throw err;
      }
    },
    [revokeUserPermission, revokeGroupPermission]
  );

  const handleGrantPermission = useCallback(
    async (data: PermissionCreate) => {
      try {
        await grantPermission(data);
        toast.success("Permission granted successfully");
      } catch (err) {
        if (err instanceof Error) {
          toast.error(err.message);
        } else {
          toast.error("Failed to grant permission");
        }
        throw err;
      }
    },
    [grantPermission]
  );

  const handleUpdatePermission = useCallback(
    async (id: string, data: PermissionUpdate) => {
      try {
        await updatePermission(id, data);
        toast.success("Permission updated successfully");
      } catch (err) {
        if (err instanceof Error) {
          toast.error(err.message);
        } else {
          toast.error("Failed to update permission");
        }
        throw err;
      }
    },
    [updatePermission]
  );

  // KB selection screen
  if (!kbId) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Shield className="h-8 w-8" />
                <h1 className="text-2xl font-bold">KB Permissions</h1>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Manage user and group access to Knowledge Bases
              </p>
            </div>
            <Button variant="outline" onClick={() => router.push("/admin")}>
              Back to Dashboard
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Select Knowledge Base</CardTitle>
              <CardDescription>
                Choose a knowledge base to manage permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingKBs ? (
                <Skeleton className="h-10 w-full" />
              ) : knowledgeBases.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No knowledge bases available. Create a knowledge base first.
                </p>
              ) : (
                <Select onValueChange={handleKBChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a knowledge base" />
                  </SelectTrigger>
                  <SelectContent>
                    {knowledgeBases.map((kb) => (
                      <SelectItem key={kb.id} value={kb.id}>
                        {kb.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">KB Permissions</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-6">
            <p className="text-sm text-destructive mb-4">
              {error instanceof Error ? error.message : "Failed to load permissions"}
            </p>
            <Button onClick={() => router.push("/admin")}>
              Return to Admin Dashboard
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Shield className="h-8 w-8" />
              <h1 className="text-2xl font-bold">
                {selectedKB?.name || "KB Permissions"}
              </h1>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Manage user and group access permissions
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {/* KB Selector */}
            {loadingKBs ? (
              <Skeleton className="h-10 w-48" />
            ) : (
              <Select value={kbId || undefined} onValueChange={handleKBChange}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Switch KB" />
                </SelectTrigger>
                <SelectContent>
                  {knowledgeBases.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id}>
                      {kb.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {/* Add Permission Buttons */}
            <Button
              variant="outline"
              onClick={() => setAddGroupModalOpen(true)}
              disabled={isLoading}
            >
              <Users className="h-4 w-4 mr-2" />
              Add Group
            </Button>
            <Button onClick={() => setAddUserModalOpen(true)} disabled={isLoading}>
              <UserPlus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </div>
        </div>

        {/* Permissions Table */}
        <KBPermissionsTable
          permissions={permissions}
          total={total}
          page={page}
          limit={limit}
          isLoading={isLoading}
          onPageChange={handlePageChange}
          onLimitChange={handleLimitChange}
          onEditPermission={handleEditPermission}
          onDeletePermission={handleDeletePermission}
          searchValue={search}
          onSearchChange={handleSearchChange}
        />

        {/* Add User Permission Modal */}
        <AddUserPermissionModal
          open={addUserModalOpen}
          onOpenChange={setAddUserModalOpen}
          onGrantPermission={handleGrantPermission}
          isGranting={isGranting}
          users={users}
          usersLoading={usersLoading}
          existingUserIds={existingUserIds}
        />

        {/* Add Group Permission Modal */}
        <AddGroupPermissionModal
          open={addGroupModalOpen}
          onOpenChange={setAddGroupModalOpen}
          onGrantPermission={handleGrantPermission}
          isGranting={isGranting}
          groups={groups}
          groupsLoading={groupsLoading}
          existingGroupIds={existingGroupIds}
        />

        {/* Edit Permission Modal */}
        <EditPermissionModal
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          permission={selectedPermission}
          onUpdatePermission={handleUpdatePermission}
          onDeletePermission={handleDeletePermission}
          isUpdating={isUpdating}
          isDeleting={isRevoking}
        />
      </div>
    </DashboardLayout>
  );
}
