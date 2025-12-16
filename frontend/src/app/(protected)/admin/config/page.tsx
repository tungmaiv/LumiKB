/**
 * System Configuration Management Page (Admin Only)
 */

"use client";

import { useState } from "react";
import { ConfigSettingsTable } from "@/components/admin/config-settings-table";
import { EditConfigModal } from "@/components/admin/edit-config-modal";
import { RestartWarningBanner } from "@/components/admin/restart-warning-banner";
import { useSystemConfig } from "@/hooks/useSystemConfig";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Settings } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function SystemConfigPage() {
  const { configs, isLoading, error, updateConfig, isUpdating, updateError } =
    useSystemConfig();

  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [restartRequired, setRestartRequired] = useState<string[]>([]);

  const handleEdit = (key: string) => {
    setEditingKey(key);
  };

  const handleSave = async (key: string, value: number | boolean | string) => {
    await updateConfig(key, value);

    // Check if this setting requires restart
    const setting = configs?.[key];
    if (setting?.requires_restart && !restartRequired.includes(key)) {
      setRestartRequired((prev) => [...prev, key]);
    }
  };

  const handleDismissWarning = () => {
    setRestartRequired([]);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center min-h-[400px]">
            <p className="text-muted-foreground">Loading configuration...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error Loading Configuration</AlertTitle>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Settings className="h-8 w-8" />
          <h1 className="text-2xl font-bold">System Configuration</h1>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Manage system-wide settings for security, processing, and rate limits
        </p>
      </div>

      <RestartWarningBanner
        changedKeys={restartRequired}
        onDismiss={handleDismissWarning}
      />

      {updateError && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Update Failed</AlertTitle>
          <AlertDescription>{updateError.message}</AlertDescription>
        </Alert>
      )}

      {configs && (
        <>
          <ConfigSettingsTable configs={configs} onEdit={handleEdit} />

          <EditConfigModal
            isOpen={editingKey !== null}
            onClose={() => setEditingKey(null)}
            setting={editingKey ? configs[editingKey] : null}
            onSave={handleSave}
            isSaving={isUpdating}
          />
        </>
      )}
      </div>
    </DashboardLayout>
  );
}
