/**
 * LLM Model Registry admin page
 * Story 7-9: LLM Model Registry (AC-7.9.4, AC-7.9.5, AC-7.9.6, AC-7.9.7)
 */

'use client';

import { useState, useCallback } from 'react';
import { Bot, Plus, Filter } from 'lucide-react';
import { toast } from 'sonner';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ModelTable,
  ModelFormModal,
  TestResultDialog,
  DeleteModelDialog,
} from '@/components/admin/models';
import { DocumentPagination } from '@/components/documents/document-pagination';
import { useModelRegistry, useModel } from '@/hooks/useModelRegistry';
import type {
  LLMModelSummary,
  LLMModelCreate,
  LLMModelUpdate,
  ConnectionTestResult,
  ModelType,
  ModelProvider,
  ModelStatus,
} from '@/types/llm-model';
import { PROVIDER_INFO, MODEL_TYPE_INFO, MODEL_STATUS_INFO } from '@/types/llm-model';

const DEFAULT_PAGE_SIZE = 10;

const MODEL_TYPES: ModelType[] = ['embedding', 'generation'];
const MODEL_PROVIDERS: ModelProvider[] = [
  'ollama',
  'openai',
  'azure',
  'gemini',
  'anthropic',
  'cohere',
];
const MODEL_STATUSES: ModelStatus[] = ['active', 'inactive', 'deprecated'];

export default function ModelsPage() {
  // Filters
  const [typeFilter, setTypeFilter] = useState<ModelType | undefined>();
  const [providerFilter, setProviderFilter] = useState<ModelProvider | undefined>();
  const [statusFilter, setStatusFilter] = useState<ModelStatus | undefined>();

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  // Modals
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [deletingModel, setDeletingModel] = useState<LLMModelSummary | null>(null);

  // Test state
  const [testingModelId, setTestingModelId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [testedModelName, setTestedModelName] = useState('');

  // Data fetching with pagination
  const {
    models,
    total,
    isLoading,
    error,
    createModel,
    updateModel,
    deleteModel,
    setDefault,
    testConnection,
    isCreating,
    isUpdating,
    isDeleting,
  } = useModelRegistry({
    type: typeFilter,
    provider: providerFilter,
    status: statusFilter,
    skip: (page - 1) * pageSize,
    limit: pageSize,
  });

  // Pagination handlers
  const totalPages = Math.ceil(total / pageSize);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when page size changes
  }, []);

  // Fetch selected model for editing
  const { data: selectedModel } = useModel(selectedModelId);

  const handleAddModel = () => {
    setSelectedModelId(null);
    setFormModalOpen(true);
  };

  const handleEditModel = (model: LLMModelSummary) => {
    setSelectedModelId(model.id);
    setFormModalOpen(true);
  };

  const handleDeleteModel = (model: LLMModelSummary) => {
    setDeletingModel(model);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deletingModel) return;
    try {
      await deleteModel(deletingModel.id);
      toast.success(`Model "${deletingModel.name}" deleted successfully`);
      setDeleteDialogOpen(false);
      setDeletingModel(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete model');
    }
  };

  const handleSetDefault = async (model: LLMModelSummary) => {
    try {
      await setDefault(model.id);
      toast.success(`"${model.name}" is now the default ${model.type} model`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to set default model');
    }
  };

  const handleTestConnection = async (model: LLMModelSummary) => {
    setTestingModelId(model.id);
    setTestedModelName(model.name);
    try {
      const result = await testConnection(model.id);
      setTestResult(result);
      setTestDialogOpen(true);
      if (result.success) {
        toast.success(`Connection test passed for "${model.name}"`);
      } else {
        toast.error(`Connection test failed: ${result.message}`);
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Connection test failed',
        latency_ms: null,
        details: null,
      });
      setTestDialogOpen(true);
      toast.error(err instanceof Error ? err.message : 'Connection test failed');
    } finally {
      setTestingModelId(null);
    }
  };

  const handleFormSubmit = async (data: LLMModelCreate | LLMModelUpdate) => {
    try {
      if (selectedModelId) {
        await updateModel(selectedModelId, data as LLMModelUpdate);
        toast.success('Model updated successfully');
      } else {
        await createModel(data as LLMModelCreate);
        toast.success('Model created successfully');
      }
      setFormModalOpen(false);
      setSelectedModelId(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save model');
      throw err; // Re-throw to keep modal open
    }
  };

  const clearFilters = () => {
    setTypeFilter(undefined);
    setProviderFilter(undefined);
    setStatusFilter(undefined);
    setPage(1); // Reset to first page when filters are cleared
  };

  const hasFilters = typeFilter || providerFilter || statusFilter;

  if (error) {
    return (
      <DashboardLayout>
        <div className="container mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">LLM Model Registry</h1>
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load models'}
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
              <Bot className="h-8 w-8" />
              <h1 className="text-2xl font-bold">LLM Model Registry</h1>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Manage embedding and generation models from multiple providers
            </p>
          </div>
          <Button onClick={handleAddModel}>
            <Plus className="h-4 w-4 mr-2" />
            Add Model
          </Button>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filters:</span>
          </div>

          <Select
            value={typeFilter || 'all'}
            onValueChange={(value) => {
              setTypeFilter(value === 'all' ? undefined : (value as ModelType));
              setPage(1); // Reset to first page when filter changes
            }}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {MODEL_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {MODEL_TYPE_INFO[type].name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={providerFilter || 'all'}
            onValueChange={(value) => {
              setProviderFilter(value === 'all' ? undefined : (value as ModelProvider));
              setPage(1); // Reset to first page when filter changes
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Providers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Providers</SelectItem>
              {MODEL_PROVIDERS.map((provider) => (
                <SelectItem key={provider} value={provider}>
                  {PROVIDER_INFO[provider].icon} {PROVIDER_INFO[provider].name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={statusFilter || 'all'}
            onValueChange={(value) => {
              setStatusFilter(value === 'all' ? undefined : (value as ModelStatus));
              setPage(1); // Reset to first page when filter changes
            }}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {MODEL_STATUSES.map((status) => (
                <SelectItem key={status} value={status}>
                  {MODEL_STATUS_INFO[status].name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </div>

        {/* Pagination - Above Table */}
        {total > 0 && (
          <div className="mb-4">
            <DocumentPagination
              page={page}
              totalPages={totalPages}
              total={total}
              limit={pageSize}
              onPageChange={handlePageChange}
              onLimitChange={handlePageSizeChange}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Model Table */}
        <ModelTable
          models={models}
          isLoading={isLoading}
          onEdit={handleEditModel}
          onDelete={handleDeleteModel}
          onSetDefault={handleSetDefault}
          onTest={handleTestConnection}
          testingModelId={testingModelId}
        />

        {/* Create/Edit Modal */}
        <ModelFormModal
          open={formModalOpen}
          onOpenChange={(open) => {
            setFormModalOpen(open);
            if (!open) setSelectedModelId(null);
          }}
          model={selectedModel}
          onSubmit={handleFormSubmit}
          isSubmitting={isCreating || isUpdating}
        />

        {/* Delete Confirmation Dialog */}
        <DeleteModelDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          model={deletingModel}
          onConfirm={handleConfirmDelete}
          isDeleting={isDeleting}
        />

        {/* Test Result Dialog */}
        <TestResultDialog
          open={testDialogOpen}
          onOpenChange={setTestDialogOpen}
          result={testResult}
          modelName={testedModelName}
        />
      </div>
    </DashboardLayout>
  );
}
