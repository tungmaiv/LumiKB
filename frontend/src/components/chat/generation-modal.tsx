/**
 * GenerationModal Component - Epic 4, Story 4.4, AC1
 * Modal dialog for configuring and triggering document generation
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Button } from '@/components/ui/button';
import { useDraftStore } from '@/lib/stores/draft-store';
import { Bookmark } from 'lucide-react';
import { TemplateSelector } from '../generation/template-selector';
import { AdditionalPromptInput } from './additional-prompt-input';
import { GenerateButton } from './generate-button';

/**
 * Zod schema for generation form validation
 * Story 4.9: Updated to use new template IDs
 */
const generationFormSchema = z.object({
  mode: z.enum(['rfp_response', 'checklist', 'gap_analysis', 'custom']),
  additionalPrompt: z.string().max(500, 'Additional prompt must be 500 characters or less'),
});

export type GenerationFormData = z.infer<typeof generationFormSchema>;

export interface GenerationModalProps {
  /** Whether modal is open */
  open: boolean;
  /** Callback when modal open state changes */
  onOpenChange: (open: boolean) => void;
  /** KB ID for generation context */
  kbId: string;
  /** Callback when generation is submitted */
  onSubmit: (data: GenerationFormData) => Promise<void>;
}

/**
 * Modal for configuring document generation request.
 * Integrates selected sources from Story 3.8 (AC2).
 *
 * @example
 * <GenerationModal
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   kbId={currentKbId}
 *   onSubmit={handleGenerate}
 * />
 */
export function GenerationModal({ open, onOpenChange, kbId, onSubmit }: GenerationModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Access selected sources from Story 3.8 draft store (AC2)
  const { selectedResults } = useDraftStore();
  const hasSelectedSources = selectedResults.length > 0;

  const form = useForm<GenerationFormData>({
    resolver: zodResolver(generationFormSchema),
    defaultValues: {
      mode: 'rfp_response',
      additionalPrompt: '',
    },
  });

  const handleSubmit = async (data: GenerationFormData) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await onSubmit(data);
      form.reset();
      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to generate document';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && !isSubmitting) {
      form.reset();
      setSubmitError(null);
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Generate Document</DialogTitle>
          <DialogDescription>
            Create a professional document using AI-powered synthesis of your knowledge base
            sources.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {/* Selected Sources Indicator (AC2) */}
            {hasSelectedSources && (
              <div
                className="rounded-md bg-primary/5 border border-primary/20 p-3 flex items-center gap-2"
                data-testid="selected-sources-indicator"
              >
                <Bookmark className="h-4 w-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">
                  <strong className="font-medium text-foreground">
                    {selectedResults.length} source{selectedResults.length > 1 ? 's' : ''}
                  </strong>{' '}
                  selected from search results
                </span>
              </div>
            )}

            {/* Template Selector (Story 4.9) */}
            <FormField
              control={form.control}
              name="mode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Template</FormLabel>
                  <FormControl>
                    <TemplateSelector value={field.value} onChange={field.onChange} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Additional Prompt Input */}
            <FormField
              control={form.control}
              name="additionalPrompt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Additional Instructions (Optional)</FormLabel>
                  <FormControl>
                    <AdditionalPromptInput
                      value={field.value}
                      onChange={field.onChange}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Error Display */}
            {submitError && (
              <p className="text-sm text-destructive" role="alert">
                {submitError}
              </p>
            )}

            {/* Footer Actions */}
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || !hasSelectedSources}
                size="lg"
                data-testid="generate-button"
              >
                {isSubmitting ? (
                  <>
                    <span className="mr-2 h-4 w-4 animate-spin">⏳</span>
                    Generating...
                  </>
                ) : (
                  <>
                    <span className="mr-2">📄</span>
                    Generate Draft
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
