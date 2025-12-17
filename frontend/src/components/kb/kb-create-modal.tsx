'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, X } from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useKBStore } from '@/lib/stores/kb-store';
import { useAvailableModels } from '@/hooks/useAvailableModels';
import { useState, KeyboardEvent } from 'react';

/**
 * Story 7-10: KB Model Configuration (AC-7.10.1-3, 7.10.6)
 * Updated schema to include embedding and generation model selection.
 */
const createKbSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  description: z.string().max(2000, 'Description must be less than 2000 characters').optional(),
  tags: z
    .array(z.string().max(50, 'Tag must be less than 50 characters'))
    .max(10, 'Maximum 10 tags allowed')
    .optional(),
  /** Story 7-10: Optional embedding model from registry (AC-7.10.1) */
  embedding_model_id: z.string().optional(),
  /** Story 7-10: Optional generation model from registry (AC-7.10.1) */
  generation_model_id: z.string().optional(),
});

type CreateKbFormData = z.infer<typeof createKbSchema>;

interface KbCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Story 7-10: KB Model Configuration (AC-7.10.1-3, 7.10.6)
 * KB owners can select embedding and generation models during creation.
 */
export function KbCreateModal({ open, onOpenChange }: KbCreateModalProps): React.ReactElement {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState('');
  const createKb = useKBStore((state) => state.createKb);

  // Story 7-10: Fetch available models for KB configuration (AC-7.10.1, 7.10.6)
  const { embeddingModels, generationModels, isLoading: isLoadingModels } = useAvailableModels();

  const form = useForm<CreateKbFormData>({
    resolver: zodResolver(createKbSchema),
    defaultValues: {
      name: '',
      description: '',
      tags: [],
      embedding_model_id: undefined,
      generation_model_id: undefined,
    },
  });

  const tags = form.watch('tags') || [];

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim().toLowerCase();
    if (trimmedTag && !tags.includes(trimmedTag) && tags.length < 10) {
      form.setValue('tags', [...tags, trimmedTag]);
    }
    setTagInput('');
  };

  const removeTag = (tagToRemove: string) => {
    form.setValue(
      'tags',
      tags.filter((tag) => tag !== tagToRemove)
    );
  };

  const handleTagInputKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(tagInput);
    } else if (e.key === 'Backspace' && !tagInput && tags.length > 0) {
      removeTag(tags[tags.length - 1]);
    }
  };

  const handleSubmit = async (data: CreateKbFormData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      // Story 7-10: Pass model IDs to createKb (AC-7.10.1-3)
      await createKb({
        name: data.name,
        description: data.description || undefined,
        tags: data.tags && data.tags.length > 0 ? data.tags : undefined,
        embedding_model_id: data.embedding_model_id || undefined,
        generation_model_id: data.generation_model_id || undefined,
      });
      form.reset();
      setTagInput('');
      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create knowledge base';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      form.reset();
      setTagInput('');
      setSubmitError(null);
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Knowledge Base</DialogTitle>
          <DialogDescription>
            Create a new knowledge base to organize your documents.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter knowledge base name"
                      {...field}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter a description for this knowledge base"
                      className="resize-none"
                      rows={3}
                      {...field}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="tags"
              render={() => (
                <FormItem>
                  <FormLabel>Tags (optional)</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      {tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                            >
                              {tag}
                              <button
                                type="button"
                                onClick={() => removeTag(tag)}
                                className="rounded-full p-0.5 hover:bg-primary/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                aria-label={`Remove ${tag} tag`}
                                disabled={isSubmitting}
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                      <Input
                        placeholder="Type a tag and press Enter"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={handleTagInputKeyDown}
                        onBlur={() => tagInput && addTag(tagInput)}
                        disabled={isSubmitting || tags.length >= 10}
                        aria-label="Add tags"
                      />
                    </div>
                  </FormControl>
                  <FormDescription>
                    Press Enter or comma to add a tag. Maximum 10 tags.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Story 7-10: Model Configuration Section (AC-7.10.1-3, 7.10.6) */}
            <div className="space-y-4 border-t pt-4">
              <p className="text-sm font-medium text-muted-foreground">
                Model Configuration (optional)
              </p>

              {/* Embedding Model Selection (AC-7.10.1, 7.10.2) */}
              <FormField
                control={form.control}
                name="embedding_model_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Embedding Model</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isSubmitting || isLoadingModels}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Use system default" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {embeddingModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Model used for document embedding. Leave empty to use system default.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Generation Model Selection (AC-7.10.1, 7.10.3) */}
              <FormField
                control={form.control}
                name="generation_model_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Generation Model</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isSubmitting || isLoadingModels}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Use system default" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {generationModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Model used for document generation. Leave empty to use system default.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {submitError && <p className="text-sm text-destructive">{submitError}</p>}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
