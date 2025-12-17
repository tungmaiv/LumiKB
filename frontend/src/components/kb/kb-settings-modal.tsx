'use client';

/**
 * KB Settings Modal - Story 7-14: KB Settings UI - General Panel (AC-7.14.1-8)
 *
 * Tabbed modal for configuring Knowledge Base settings including:
 * - General: Chunking, Retrieval, Generation parameters
 * - Models: Embedding and Generation model selection (from Story 7-10)
 * - Advanced: Placeholder for future advanced settings
 * - Prompts: Placeholder for prompt configuration
 */

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  AlertTriangle,
  Loader2,
  Settings,
  Cpu,
  Sliders,
  MessageSquare,
  Lock,
  Bug,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useKBStore } from '@/lib/stores/kb-store';
import { useAvailableModels } from '@/hooks/useAvailableModels';
import { useKBSettings } from '@/hooks/useKBSettings';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';
import {
  GeneralPanel,
  generalPanelSchema,
  defaultGeneralPanelValues,
  type KBSettingsFormData,
} from './settings/general-panel';
import {
  PromptsPanel,
  promptsPanelSchema,
  defaultPromptsPanelValues,
} from './settings/prompts-panel';
import { PresetSelector } from './settings/preset-selector';
import {
  ChunkingStrategy,
  RetrievalMethod,
  CitationStyle,
  UncertaintyHandling,
  DocumentParserBackend,
} from '@/types/kb-settings';

// =============================================================================
// Schema Definitions (AC-7.14.7)
// =============================================================================

// Combined schema for the entire settings form
// Using merge() for proper type inference with react-hook-form
const modelSchema = z.object({
  embedding_model_id: z.string().optional(),
  generation_model_id: z.string().optional(),
});

const advancedSchema = z.object({
  // Story 9-15: Debug mode (AC-9.15.2)
  debug_mode: z.boolean().optional().default(false),
});

const kbSettingsSchema = modelSchema
  .merge(generalPanelSchema)
  .merge(promptsPanelSchema)
  .merge(advancedSchema);

type KbSettingsFormValues = z.infer<typeof kbSettingsSchema>;

// =============================================================================
// Props & Types
// =============================================================================

interface KbSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  kb: KnowledgeBase;
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * KB Settings Modal Component
 * Story 7-14: AC-7.14.1-8
 */
export function KbSettingsModal({
  open,
  onOpenChange,
  kb,
}: KbSettingsModalProps): React.ReactElement {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('general');
  const updateKb = useKBStore((state) => state.updateKb);

  // Story 7-10: Fetch available models (AC-7.10.6)
  const {
    embeddingModels,
    generationModels,
    defaultEmbeddingModel,
    defaultGenerationModel,
    isLoading: isLoadingModels,
  } = useAvailableModels();

  // Story 7-14: Fetch KB settings (AC-7.14.8)
  const { settings, isLoading: isLoadingSettings, updateSettings, isSaving } = useKBSettings(kb.id);

  // Build default form values from KB and settings
  // Story 7-10: Extract model IDs from nested model objects
  const buildDefaultValues = (): KbSettingsFormValues => ({
    embedding_model_id: kb.embedding_model?.id ?? kb.embedding_model_id ?? undefined,
    generation_model_id: kb.generation_model?.id ?? kb.generation_model_id ?? undefined,
    chunking: {
      strategy: settings?.chunking?.strategy ?? defaultGeneralPanelValues.chunking.strategy,
      chunk_size: settings?.chunking?.chunk_size ?? defaultGeneralPanelValues.chunking.chunk_size,
      chunk_overlap:
        settings?.chunking?.chunk_overlap ?? defaultGeneralPanelValues.chunking.chunk_overlap,
    },
    retrieval: {
      top_k: settings?.retrieval?.top_k ?? defaultGeneralPanelValues.retrieval.top_k,
      similarity_threshold:
        settings?.retrieval?.similarity_threshold ??
        defaultGeneralPanelValues.retrieval.similarity_threshold,
      method: settings?.retrieval?.method ?? defaultGeneralPanelValues.retrieval.method,
      mmr_enabled:
        settings?.retrieval?.mmr_enabled ?? defaultGeneralPanelValues.retrieval.mmr_enabled,
      mmr_lambda: settings?.retrieval?.mmr_lambda ?? defaultGeneralPanelValues.retrieval.mmr_lambda,
    },
    generation: {
      temperature:
        settings?.generation?.temperature ?? defaultGeneralPanelValues.generation.temperature,
      top_p: settings?.generation?.top_p ?? defaultGeneralPanelValues.generation.top_p,
      max_tokens:
        settings?.generation?.max_tokens ?? defaultGeneralPanelValues.generation.max_tokens,
    },
    // Story 7-32: Document Processing settings (AC-7.32.3)
    processing: {
      parser_backend:
        settings?.processing?.parser_backend ?? defaultGeneralPanelValues.processing.parser_backend,
    },
    // Story 7-15: Prompts settings
    prompts: {
      system_prompt:
        settings?.prompts?.system_prompt ?? defaultPromptsPanelValues.prompts.system_prompt,
      context_template:
        settings?.prompts?.context_template ?? defaultPromptsPanelValues.prompts.context_template,
      citation_style:
        settings?.prompts?.citation_style ?? defaultPromptsPanelValues.prompts.citation_style,
      uncertainty_handling:
        settings?.prompts?.uncertainty_handling ??
        defaultPromptsPanelValues.prompts.uncertainty_handling,
      response_language:
        settings?.prompts?.response_language ?? defaultPromptsPanelValues.prompts.response_language,
    },
    // Story 9-15: Debug mode (AC-9.15.2)
    debug_mode: settings?.debug_mode ?? false,
  });

  // Cast zodResolver result to fix type inference with complex merged schemas
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<KbSettingsFormValues>({
    resolver: zodResolver(kbSettingsSchema) as any,
    defaultValues: buildDefaultValues(),
  });

  // Reset form when KB or settings change
  useEffect(() => {
    form.reset(buildDefaultValues());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kb, settings]);

  // Story 7-10: Check if embedding model is being changed (AC-7.10.7)
  const currentEmbeddingModelId = form.watch('embedding_model_id');
  const originalEmbeddingModelId = kb.embedding_model?.id ?? kb.embedding_model_id ?? undefined;
  const isEmbeddingModelChanging =
    currentEmbeddingModelId !== originalEmbeddingModelId && currentEmbeddingModelId !== undefined;

  // Story 7-14: Handle form submission (AC-7.14.6)
  const handleSubmit = async (data: KbSettingsFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      // Update model configuration (Story 7-10)
      await updateKb(kb.id, {
        embedding_model_id: data.embedding_model_id || null,
        generation_model_id: data.generation_model_id || null,
      });

      // Update general settings (Story 7-14, AC-7.14.6, AC-7.14.8)
      // Update prompts settings (Story 7-15)
      // Update processing settings (Story 7-32, AC-7.32.3)
      // Update debug mode (Story 9-15, AC-9.15.2)
      await updateSettings({
        chunking: data.chunking,
        retrieval: data.retrieval,
        generation: data.generation,
        processing: data.processing,
        prompts: data.prompts,
        debug_mode: data.debug_mode,
      });

      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update KB settings';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      form.reset(buildDefaultValues());
      setSubmitError(null);
      setActiveTab('general');
    }
    onOpenChange(newOpen);
  };

  // Check if any settings have changed
  // Story 7-10: Compare against nested model IDs
  const formValues = form.watch();
  const currentEmbeddingId = kb.embedding_model?.id ?? kb.embedding_model_id ?? undefined;
  const currentGenerationId = kb.generation_model?.id ?? kb.generation_model_id ?? undefined;
  const hasModelChanges =
    formValues.embedding_model_id !== currentEmbeddingId ||
    formValues.generation_model_id !== currentGenerationId;

  const hasGeneralChanges =
    formValues.chunking?.strategy !==
      (settings?.chunking?.strategy ?? defaultGeneralPanelValues.chunking.strategy) ||
    formValues.chunking?.chunk_size !==
      (settings?.chunking?.chunk_size ?? defaultGeneralPanelValues.chunking.chunk_size) ||
    formValues.chunking?.chunk_overlap !==
      (settings?.chunking?.chunk_overlap ?? defaultGeneralPanelValues.chunking.chunk_overlap) ||
    formValues.retrieval?.top_k !==
      (settings?.retrieval?.top_k ?? defaultGeneralPanelValues.retrieval.top_k) ||
    formValues.retrieval?.similarity_threshold !==
      (settings?.retrieval?.similarity_threshold ??
        defaultGeneralPanelValues.retrieval.similarity_threshold) ||
    formValues.retrieval?.method !==
      (settings?.retrieval?.method ?? defaultGeneralPanelValues.retrieval.method) ||
    formValues.retrieval?.mmr_enabled !==
      (settings?.retrieval?.mmr_enabled ?? defaultGeneralPanelValues.retrieval.mmr_enabled) ||
    formValues.retrieval?.mmr_lambda !==
      (settings?.retrieval?.mmr_lambda ?? defaultGeneralPanelValues.retrieval.mmr_lambda) ||
    formValues.generation?.temperature !==
      (settings?.generation?.temperature ?? defaultGeneralPanelValues.generation.temperature) ||
    formValues.generation?.top_p !==
      (settings?.generation?.top_p ?? defaultGeneralPanelValues.generation.top_p) ||
    formValues.generation?.max_tokens !==
      (settings?.generation?.max_tokens ?? defaultGeneralPanelValues.generation.max_tokens) ||
    // Story 7-32: Document Processing changes (AC-7.32.3)
    formValues.processing?.parser_backend !==
      (settings?.processing?.parser_backend ?? defaultGeneralPanelValues.processing.parser_backend);

  // Story 7-15: Check if prompts settings have changed
  const hasPromptsChanges =
    formValues.prompts?.system_prompt !==
      (settings?.prompts?.system_prompt ?? defaultPromptsPanelValues.prompts.system_prompt) ||
    formValues.prompts?.citation_style !==
      (settings?.prompts?.citation_style ?? defaultPromptsPanelValues.prompts.citation_style) ||
    formValues.prompts?.uncertainty_handling !==
      (settings?.prompts?.uncertainty_handling ??
        defaultPromptsPanelValues.prompts.uncertainty_handling) ||
    formValues.prompts?.response_language !==
      (settings?.prompts?.response_language ?? defaultPromptsPanelValues.prompts.response_language);

  // Story 9-15: Check if debug mode has changed (AC-9.15.2)
  const hasAdvancedChanges = formValues.debug_mode !== (settings?.debug_mode ?? false);

  const hasChanges =
    hasModelChanges || hasGeneralChanges || hasPromptsChanges || hasAdvancedChanges;
  // Story 7-16: Track if form has custom changes for preset confirmation (AC-7.16.7)
  const hasCustomChanges = hasGeneralChanges || hasPromptsChanges;
  const isDisabled = isSubmitting || isSaving;
  const isLoading = isLoadingModels || isLoadingSettings;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>KB Settings</DialogTitle>
          <DialogDescription>Configure settings for &quot;{kb.name}&quot;.</DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            {/* Story 7-16: Quick Preset Selector (AC-7.16.1, AC-7.16.7, AC-7.16.8) */}
            {!isLoading && (
              <PresetSelector
                form={form}
                currentSettings={settings}
                hasCustomChanges={hasCustomChanges}
                disabled={isDisabled}
              />
            )}

            {/* Story 7-14: Tab Structure (AC-7.14.1) */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="general" className="flex items-center gap-1.5">
                  <Settings className="h-4 w-4" />
                  <span className="hidden sm:inline">General</span>
                </TabsTrigger>
                <TabsTrigger value="models" className="flex items-center gap-1.5">
                  <Cpu className="h-4 w-4" />
                  <span className="hidden sm:inline">Models</span>
                </TabsTrigger>
                <TabsTrigger value="advanced" className="flex items-center gap-1.5">
                  <Sliders className="h-4 w-4" />
                  <span className="hidden sm:inline">Advanced</span>
                </TabsTrigger>
                <TabsTrigger value="prompts" className="flex items-center gap-1.5">
                  <MessageSquare className="h-4 w-4" />
                  <span className="hidden sm:inline">Prompts</span>
                </TabsTrigger>
              </TabsList>

              {/* General Tab (AC-7.14.2-5) */}
              <TabsContent value="general" className="mt-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <GeneralPanel
                    form={form as unknown as Parameters<typeof GeneralPanel>[0]['form']}
                    disabled={isDisabled}
                  />
                )}
              </TabsContent>

              {/* Models Tab (from Story 7-10) */}
              <TabsContent value="models" className="mt-4 space-y-4">
                {/* Story 7-10: Info about locked embedding model when KB has documents */}
                {kb.embedding_model_locked && (
                  <Alert>
                    <Lock className="h-4 w-4" />
                    <AlertTitle>Embedding Model Locked</AlertTitle>
                    <AlertDescription>
                      This KB has documents with embeddings. The embedding model cannot be changed
                      because existing documents use the current model&apos;s vector dimensions. The
                      generation model can still be changed.
                    </AlertDescription>
                  </Alert>
                )}

                {/* Story 7-10: Warning about embedding model change (AC-7.10.7) */}
                {!kb.embedding_model_locked && isEmbeddingModelChanging && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Warning: Embedding Model Change</AlertTitle>
                    <AlertDescription>
                      Changing the embedding model will only affect newly uploaded documents.
                      Existing documents will retain their current embeddings. For consistent search
                      results, consider re-processing existing documents.
                    </AlertDescription>
                  </Alert>
                )}

                {/* Story 7-10: Embedding Model Selection (AC-7.10.5) */}
                <FormField
                  control={form.control}
                  name="embedding_model_id"
                  render={({ field }) => {
                    // Find the currently selected model for display
                    const selectedModel = embeddingModels.find((m) => m.id === field.value);
                    return (
                      <FormItem>
                        <FormLabel className="flex items-center gap-2">
                          Embedding Model
                          {kb.embedding_model_locked && (
                            <Lock className="h-3 w-3 text-muted-foreground" />
                          )}
                        </FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value}
                          disabled={isDisabled || isLoadingModels || kb.embedding_model_locked}
                        >
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select embedding model" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {embeddingModels.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.name}
                                {model.is_default && ' (Default)'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormDescription>
                          {kb.embedding_model_locked ? (
                            'Locked: KB has existing documents with embeddings.'
                          ) : selectedModel ? (
                            <>
                              Using: <strong>{selectedModel.name}</strong> ({selectedModel.provider}
                              )
                            </>
                          ) : (
                            'No embedding model configured'
                          )}
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    );
                  }}
                />

                {/* Story 7-10: Generation Model Selection (AC-7.10.5) */}
                <FormField
                  control={form.control}
                  name="generation_model_id"
                  render={({ field }) => {
                    // Find the currently selected model for display
                    const selectedModel = generationModels.find((m) => m.id === field.value);
                    return (
                      <FormItem>
                        <FormLabel>Generation Model</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value}
                          disabled={isDisabled || isLoadingModels}
                        >
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select generation model" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {generationModels.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.name}
                                {model.is_default && ' (Default)'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormDescription>
                          {selectedModel ? (
                            <>
                              Using: <strong>{selectedModel.name}</strong> ({selectedModel.provider}
                              )
                            </>
                          ) : (
                            'No generation model configured'
                          )}
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    );
                  }}
                />
              </TabsContent>

              {/* Advanced Tab - Story 9-15: Debug Mode (AC-9.15.2) */}
              <TabsContent value="advanced" className="mt-4 space-y-6">
                {/* Debug Mode Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Bug className="h-4 w-4 text-muted-foreground" />
                    <h3 className="text-sm font-medium">Debug Settings</h3>
                  </div>

                  <FormField
                    control={form.control}
                    name="debug_mode"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                            disabled={isDisabled}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel className="flex items-center gap-2">
                            Enable Debug Mode
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Bug className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                              </TooltipTrigger>
                              <TooltipContent side="top" className="max-w-xs">
                                <p>
                                  When enabled, chat responses include detailed RAG pipeline
                                  telemetry: retrieved chunks with similarity scores, KB parameters,
                                  and timing metrics. Useful for debugging retrieval quality.
                                </p>
                              </TooltipContent>
                            </Tooltip>
                          </FormLabel>
                          <FormDescription>
                            Show detailed RAG pipeline information in chat responses for
                            troubleshooting.
                          </FormDescription>
                        </div>
                      </FormItem>
                    )}
                  />
                </div>

                {/* Placeholder for future advanced settings */}
                <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground border-t">
                  <Sliders className="h-8 w-8 mb-3 opacity-50" />
                  <p className="text-sm">More advanced settings coming soon.</p>
                  <p className="text-xs mt-1">
                    Configure reranking, NER, and document processing options.
                  </p>
                </div>
              </TabsContent>

              {/* Prompts Tab - Story 7-15 (AC-7.15.1-8) */}
              <TabsContent value="prompts" className="mt-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <PromptsPanel
                    form={form as unknown as Parameters<typeof PromptsPanel>[0]['form']}
                    kbName={kb.name}
                    disabled={isDisabled}
                  />
                )}
              </TabsContent>
            </Tabs>

            {submitError && <p className="text-sm text-destructive">{submitError}</p>}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isDisabled}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isDisabled || !hasChanges || !form.formState.isValid}>
                {isDisabled && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save Settings
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
