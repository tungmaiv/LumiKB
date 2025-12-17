'use client';

/**
 * General Panel Component - Story 7-14: KB Settings UI - General Panel (AC-7.14.2-5,7)
 *
 * Integrates ChunkingSection, RetrievalSection, and GenerationSection
 * with form state management and Reset to Defaults functionality.
 */

import { z } from 'zod';
import { UseFormReturn } from 'react-hook-form';
import { RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { ChunkingSection } from './chunking-section';
import { RetrievalSection } from './retrieval-section';
import { GenerationSection } from './generation-section';
import { ProcessingSection } from './processing-section';
import {
  ChunkingStrategy,
  RetrievalMethod,
  DocumentParserBackend,
  KB_SETTINGS_CONSTRAINTS,
  DEFAULT_CHUNKING_CONFIG,
  DEFAULT_RETRIEVAL_CONFIG,
  DEFAULT_GENERATION_CONFIG,
  DEFAULT_PROCESSING_CONFIG,
} from '@/types/kb-settings';

// =============================================================================
// Zod Schema for General Panel Form Validation (AC-7.14.7)
// =============================================================================

const { chunking, retrieval, generation } = KB_SETTINGS_CONSTRAINTS;

export const generalPanelSchema = z.object({
  chunking: z.object({
    strategy: z.nativeEnum(ChunkingStrategy),
    chunk_size: z
      .number()
      .min(chunking.chunk_size.min, `Chunk size must be at least ${chunking.chunk_size.min}`)
      .max(chunking.chunk_size.max, `Chunk size must be at most ${chunking.chunk_size.max}`),
    chunk_overlap: z
      .number()
      .min(chunking.chunk_overlap.min, `Overlap must be at least ${chunking.chunk_overlap.min}`)
      .max(chunking.chunk_overlap.max, `Overlap must be at most ${chunking.chunk_overlap.max}`),
  }),
  retrieval: z.object({
    top_k: z
      .number()
      .min(retrieval.top_k.min, `Top K must be at least ${retrieval.top_k.min}`)
      .max(retrieval.top_k.max, `Top K must be at most ${retrieval.top_k.max}`),
    similarity_threshold: z
      .number()
      .min(retrieval.similarity_threshold.min, 'Threshold must be at least 0')
      .max(retrieval.similarity_threshold.max, 'Threshold must be at most 1'),
    method: z.nativeEnum(RetrievalMethod),
    mmr_enabled: z.boolean(),
    mmr_lambda: z
      .number()
      .min(retrieval.mmr_lambda.min, 'Lambda must be at least 0')
      .max(retrieval.mmr_lambda.max, 'Lambda must be at most 1'),
  }),
  generation: z.object({
    temperature: z
      .number()
      .min(generation.temperature.min, `Temperature must be at least ${generation.temperature.min}`)
      .max(generation.temperature.max, `Temperature must be at most ${generation.temperature.max}`),
    top_p: z
      .number()
      .min(generation.top_p.min, 'Top P must be at least 0')
      .max(generation.top_p.max, 'Top P must be at most 1'),
    max_tokens: z
      .number()
      .min(generation.max_tokens.min, `Max tokens must be at least ${generation.max_tokens.min}`)
      .max(generation.max_tokens.max, `Max tokens must be at most ${generation.max_tokens.max}`),
  }),
  // Story 7-32: Document Processing settings (AC-7.32.3)
  processing: z.object({
    parser_backend: z.nativeEnum(DocumentParserBackend),
  }),
});

export type KBSettingsFormData = z.infer<typeof generalPanelSchema>;

// =============================================================================
// Default Form Values
// =============================================================================

export const defaultGeneralPanelValues: KBSettingsFormData = {
  chunking: {
    strategy: DEFAULT_CHUNKING_CONFIG.strategy,
    chunk_size: DEFAULT_CHUNKING_CONFIG.chunk_size,
    chunk_overlap: DEFAULT_CHUNKING_CONFIG.chunk_overlap,
  },
  retrieval: {
    top_k: DEFAULT_RETRIEVAL_CONFIG.top_k,
    similarity_threshold: DEFAULT_RETRIEVAL_CONFIG.similarity_threshold,
    method: DEFAULT_RETRIEVAL_CONFIG.method,
    mmr_enabled: DEFAULT_RETRIEVAL_CONFIG.mmr_enabled,
    mmr_lambda: DEFAULT_RETRIEVAL_CONFIG.mmr_lambda,
  },
  generation: {
    temperature: DEFAULT_GENERATION_CONFIG.temperature,
    top_p: DEFAULT_GENERATION_CONFIG.top_p,
    max_tokens: DEFAULT_GENERATION_CONFIG.max_tokens,
  },
  // Story 7-32: Document Processing defaults (AC-7.32.3)
  processing: {
    parser_backend: DEFAULT_PROCESSING_CONFIG.parser_backend,
  },
};

// =============================================================================
// General Panel Component
// =============================================================================

interface GeneralPanelProps {
  form: UseFormReturn<KBSettingsFormData>;
  disabled?: boolean;
  onResetToDefaults?: () => void;
}

export function GeneralPanel({
  form,
  disabled = false,
  onResetToDefaults,
}: GeneralPanelProps): React.ReactElement {
  const handleResetToDefaults = () => {
    form.reset(defaultGeneralPanelValues);
    onResetToDefaults?.();
  };

  return (
    <div className="space-y-6">
      {/* Document Processing Section - Story 7-32 (AC-7.32.3) */}
      <ProcessingSection form={form} disabled={disabled} />

      <Separator />

      {/* Chunking Section (AC-7.14.2) */}
      <ChunkingSection form={form} disabled={disabled} />

      <Separator />

      {/* Retrieval Section (AC-7.14.3) */}
      <RetrievalSection form={form} disabled={disabled} />

      <Separator />

      {/* Generation Section (AC-7.14.4) */}
      <GenerationSection form={form} disabled={disabled} />

      <Separator />

      {/* Reset to Defaults Button (AC-7.14.5) */}
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset General Settings?</AlertDialogTitle>
            <AlertDialogDescription>
              This will reset all document processing, chunking, retrieval, and generation settings
              to their default values. This action cannot be undone until you save.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleResetToDefaults}>Reset to Defaults</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
