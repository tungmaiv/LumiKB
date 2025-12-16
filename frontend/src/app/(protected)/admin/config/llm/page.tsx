/**
 * LLM Configuration Page
 * Story 7-2: Centralized LLM Configuration (AC-7.2.1 through AC-7.2.4)
 *
 * Admin page for managing LLM model settings:
 * - View/edit embedding and generation model selection
 * - Configure generation parameters (temperature, max_tokens, top_p)
 * - Monitor model health status
 * - Handle hot-reload with dimension mismatch warnings
 */

'use client';

import { useState } from 'react';
import { Bot, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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
import { LLMConfigForm } from '@/components/admin/llm-config-form';
import { ModelHealthIndicator } from '@/components/admin/model-health-indicator';
import { useLLMConfig } from '@/hooks/useLLMConfig';
import type { LLMConfigUpdateRequest, DimensionMismatchWarning } from '@/types/llm-config';

export default function LLMConfigPage() {
  const {
    config,
    isLoading,
    error,
    updateConfig,
    isUpdating,
    updateError,
    health,
    isTestingHealth,
    testHealth,
    refetch,
    lastFetched,
  } = useLLMConfig();

  // Dimension mismatch warning dialog state
  const [dimensionWarning, setDimensionWarning] = useState<DimensionMismatchWarning | null>(null);
  const [pendingUpdate, setPendingUpdate] = useState<LLMConfigUpdateRequest | null>(null);

  // Hot-reload success indicator state
  const [showHotReloadSuccess, setShowHotReloadSuccess] = useState(false);

  const handleSubmit = async (request: LLMConfigUpdateRequest) => {
    try {
      const response = await updateConfig(request);

      // Check for dimension mismatch warning
      if (response.dimension_warning?.has_mismatch) {
        setDimensionWarning(response.dimension_warning);
        setPendingUpdate(request);
        return;
      }

      // Success without warning - show hot-reload feedback
      if (response.hot_reload_applied) {
        toast.success('LLM configuration updated successfully. Changes applied without restart.', {
          duration: 5000,
          icon: <RefreshCw className="h-4 w-4 text-green-500" />,
        });
        // Show visual hot-reload indicator
        setShowHotReloadSuccess(true);
        setTimeout(() => setShowHotReloadSuccess(false), 5000);
      } else {
        toast.success('LLM configuration updated successfully.');
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update configuration');
    }
  };

  const handleConfirmDimensionChange = async () => {
    // User acknowledged dimension mismatch, close the dialog
    setDimensionWarning(null);
    setPendingUpdate(null);
    toast.success('LLM configuration updated successfully.');
  };

  const handleHealthRefresh = async () => {
    try {
      await testHealth();
      toast.success('Health check completed');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Health check failed');
    }
  };

  if (isLoading && !config) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center min-h-[400px]">
            <p className="text-muted-foreground">Loading LLM configuration...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Bot className="h-8 w-8" />
              <h1 className="text-2xl font-bold">LLM Configuration</h1>
            </div>
          </div>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error Loading Configuration</AlertTitle>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <Bot className="h-8 w-8" />
            <h1 className="text-2xl font-bold">LLM Configuration</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Configure embedding and generation models with hot-reload capability
          </p>
        </div>

        {/* Hot-Reload Success Banner */}
        {showHotReloadSuccess && (
          <Alert className="mb-6 border-green-500 bg-green-50 dark:bg-green-950">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <AlertTitle className="text-green-700 dark:text-green-300">Hot-Reload Applied</AlertTitle>
            <AlertDescription className="text-green-600 dark:text-green-400">
              Configuration changes have been applied immediately without requiring a service restart.
            </AlertDescription>
          </Alert>
        )}

        {/* Update Error Alert */}
        {updateError && (
          <Alert variant="destructive" className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Update Failed</AlertTitle>
            <AlertDescription>{updateError.message}</AlertDescription>
          </Alert>
        )}

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Config Form - 2 columns */}
          <div className="lg:col-span-2">
            <LLMConfigForm
              config={config}
              onSubmit={handleSubmit}
              isSubmitting={isUpdating}
              onRefetch={refetch}
              lastFetched={lastFetched}
            />
          </div>

          {/* Health Indicator - 1 column */}
          <div>
            <ModelHealthIndicator
              health={health}
              isLoading={isLoading}
              onRefresh={handleHealthRefresh}
              isRefreshing={isTestingHealth}
            />
          </div>
        </div>

        {/* Dimension Mismatch Warning Dialog */}
        <AlertDialog
          open={dimensionWarning !== null}
          onOpenChange={(open) => {
            if (!open) {
              setDimensionWarning(null);
              setPendingUpdate(null);
            }
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Embedding Dimension Mismatch
              </AlertDialogTitle>
              <AlertDialogDescription className="space-y-3">
                <p>{dimensionWarning?.warning_message}</p>
                {dimensionWarning?.affected_kbs && dimensionWarning.affected_kbs.length > 0 && (
                  <div>
                    <p className="font-medium">Affected Knowledge Bases:</p>
                    <ul className="mt-1 list-disc list-inside text-sm">
                      {dimensionWarning.affected_kbs.map((kb) => (
                        <li key={kb}>{kb}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-sm">
                  <strong>Current dimensions:</strong> {dimensionWarning?.current_dimensions ?? 'N/A'}
                  <br />
                  <strong>New dimensions:</strong> {dimensionWarning?.new_dimensions ?? 'N/A'}
                </p>
                <p className="text-sm text-muted-foreground">
                  Changing the embedding model may require re-indexing affected knowledge bases.
                </p>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirmDimensionChange}>
                I Understand, Continue
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </DashboardLayout>
  );
}
