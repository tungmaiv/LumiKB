'use client';

/**
 * Prompts Panel Component - Story 7-15: KB Settings UI - Prompts Panel (AC-7.15.1-8)
 *
 * Configures KB-specific prompts including:
 * - System prompt with character count and preview
 * - Citation style selection
 * - Uncertainty handling configuration
 * - Response language setting
 * - Prompt templates for quick setup
 */

import { useState, useEffect, useRef } from 'react';
import { z } from 'zod';
import { UseFormReturn } from 'react-hook-form';
import { Info, Eye, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  CitationStyle,
  UncertaintyHandling,
  DEFAULT_PROMPT_CONFIG,
  CITATION_STYLE_LABELS,
  UNCERTAINTY_HANDLING_LABELS,
} from '@/types/kb-settings';
import {
  SUPPORTED_LANGUAGES,
  getTemplateOptions,
  getTemplateById,
  detectTemplateFromPrompt,
  type SupportedLanguageCode,
} from '@/lib/prompt-templates';

// =============================================================================
// Constants
// =============================================================================

const MAX_SYSTEM_PROMPT_LENGTH = 4000;

// Citation style descriptions for users
const CITATION_STYLE_DESCRIPTIONS: Record<CitationStyle, string> = {
  [CitationStyle.INLINE]: 'References appear as [1], [2] within the text',
  [CitationStyle.FOOTNOTE]: 'References appear as footnotes at the end',
  [CitationStyle.NONE]: 'No automatic citation formatting',
};

// Uncertainty handling descriptions for users
const UNCERTAINTY_HANDLING_DESCRIPTIONS: Record<UncertaintyHandling, string> = {
  [UncertaintyHandling.ACKNOWLEDGE]: 'AI states when it is uncertain about an answer',
  [UncertaintyHandling.REFUSE]: 'AI refuses to answer if not confident',
  [UncertaintyHandling.BEST_EFFORT]: 'AI gives best available answer without disclaimer',
};

// Sample values for preview (AC-7.15.7)
const PREVIEW_SAMPLE_VALUES = {
  context: 'Sample document chunk content from your knowledge base...\n\nThis is relevant information that was retrieved based on the user\'s query.',
  query: 'What is the meaning of X?',
};

// =============================================================================
// Zod Schema for Prompts Panel Form Validation (AC-7.15.2)
// =============================================================================

export const promptsPanelSchema = z.object({
  prompts: z.object({
    system_prompt: z
      .string()
      .max(MAX_SYSTEM_PROMPT_LENGTH, `System prompt must be at most ${MAX_SYSTEM_PROMPT_LENGTH} characters`),
    context_template: z.string().optional(),
    citation_style: z.nativeEnum(CitationStyle),
    uncertainty_handling: z.nativeEnum(UncertaintyHandling),
    response_language: z.string().max(10, 'Language code too long'),
  }),
});

export type PromptsPanelFormData = z.infer<typeof promptsPanelSchema>;

// =============================================================================
// Default Form Values
// =============================================================================

export const defaultPromptsPanelValues: PromptsPanelFormData = {
  prompts: {
    system_prompt: DEFAULT_PROMPT_CONFIG.system_prompt,
    context_template: DEFAULT_PROMPT_CONFIG.context_template,
    citation_style: DEFAULT_PROMPT_CONFIG.citation_style,
    uncertainty_handling: DEFAULT_PROMPT_CONFIG.uncertainty_handling,
    response_language: '', // Empty for auto-detect (AC-7.15.6)
  },
};

// =============================================================================
// Props & Types
// =============================================================================

interface PromptsPanelProps {
  form: UseFormReturn<PromptsPanelFormData>;
  kbName: string;
  disabled?: boolean;
}

// =============================================================================
// Prompts Panel Component
// =============================================================================

export function PromptsPanel({
  form,
  kbName,
  disabled = false,
}: PromptsPanelProps): React.ReactElement {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<string | null>(null);

  const systemPrompt = form.watch('prompts.system_prompt') ?? '';
  const characterCount = systemPrompt.length;
  const currentLanguage = (form.watch('prompts.response_language') || 'en') as SupportedLanguageCode;

  // Track previous language to detect changes (initialized to null to detect first meaningful change)
  const prevLanguageRef = useRef<SupportedLanguageCode | null>(null);
  const isInitializedRef = useRef(false);

  // Auto-switch system prompt when language changes (if using a template)
  useEffect(() => {
    // Skip the very first render - just record the initial language
    if (!isInitializedRef.current) {
      isInitializedRef.current = true;
      prevLanguageRef.current = currentLanguage;
      return;
    }

    const prevLang = prevLanguageRef.current;
    if (prevLang !== currentLanguage && prevLang !== null) {
      // Detect if current prompt matches a template (in any language)
      const detected = detectTemplateFromPrompt(systemPrompt);

      if (detected) {
        // Current prompt matches a template - switch to the new language version
        const newTemplate = getTemplateById(detected.templateId, currentLanguage);
        if (newTemplate) {
          form.setValue('prompts.system_prompt', newTemplate.system_prompt, { shouldDirty: true });
        }
      }
      prevLanguageRef.current = currentLanguage;
    }
  }, [currentLanguage, systemPrompt, form]);

  // Generate preview with sample values substituted (AC-7.15.7)
  const getPreviewPrompt = (): string => {
    let preview = systemPrompt;
    preview = preview.replace(/\{kb_name\}/g, kbName);
    preview = preview.replace(/\{context\}/g, PREVIEW_SAMPLE_VALUES.context);
    preview = preview.replace(/\{query\}/g, PREVIEW_SAMPLE_VALUES.query);
    return preview;
  };

  // Handle template selection (AC-7.15.8)
  const handleTemplateSelect = (templateId: string) => {
    const hasContent = systemPrompt.trim().length > 0;
    if (hasContent) {
      setPendingTemplate(templateId);
    } else {
      applyTemplate(templateId);
    }
  };

  const applyTemplate = (templateId: string) => {
    const template = getTemplateById(templateId, currentLanguage);
    if (template) {
      form.setValue('prompts.system_prompt', template.system_prompt, { shouldDirty: true });
      form.setValue('prompts.citation_style', template.citation_style, { shouldDirty: true });
      form.setValue('prompts.uncertainty_handling', template.uncertainty_handling, { shouldDirty: true });
    }
    setPendingTemplate(null);
  };

  return (
    <div className="space-y-6">
      {/* System Prompt Section (AC-7.15.1, AC-7.15.2) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="system-prompt" className="text-sm font-medium">
            System Prompt
          </Label>
          <div className="flex items-center gap-2">
            {/* Load Template Dropdown (AC-7.15.8) */}
            <Select onValueChange={handleTemplateSelect} disabled={disabled}>
              <SelectTrigger className="w-[160px] h-8 text-xs" data-testid="load-template-trigger">
                <FileText className="h-3 w-3 mr-1.5" />
                <SelectValue placeholder="Load Template" />
              </SelectTrigger>
              <SelectContent>
                {getTemplateOptions(currentLanguage).map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Preview Button (AC-7.15.7) */}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsPreviewOpen(true)}
              disabled={disabled || !systemPrompt.trim()}
              className="h-8 text-xs"
            >
              <Eye className="h-3 w-3 mr-1.5" />
              Preview
            </Button>
          </div>
        </div>

        <FormField
          control={form.control}
          name="prompts.system_prompt"
          render={({ field }) => (
            <FormItem>
              <FormControl>
                <Textarea
                  id="system-prompt"
                  placeholder={`You are a helpful assistant for {kb_name}. Use the following context to answer the user's question.\n\nContext:\n{context}\n\nInstructions:\n- Answer based only on the provided context\n- Cite sources using [1], [2] notation`}
                  className="min-h-[200px] font-mono text-sm resize-y"
                  maxLength={MAX_SYSTEM_PROMPT_LENGTH}
                  disabled={disabled}
                  {...field}
                />
              </FormControl>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span
                  className={characterCount > MAX_SYSTEM_PROMPT_LENGTH * 0.9 ? 'text-amber-500' : ''}
                  data-testid="character-count"
                >
                  {characterCount} / {MAX_SYSTEM_PROMPT_LENGTH}
                </span>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Variables Help Section (AC-7.15.3) */}
        <Collapsible open={isHelpOpen} onOpenChange={setIsHelpOpen}>
          <CollapsibleTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1.5 p-0"
            >
              <Info className="h-3 w-3" />
              Available Variables
              {isHelpOpen ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2">
            <div className="rounded-md border bg-muted/50 p-3 text-xs space-y-2">
              <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
                <code className="font-mono text-primary">{'{context}'}</code>
                <span className="text-muted-foreground">Retrieved document chunks relevant to the query</span>
                <code className="font-mono text-primary">{'{query}'}</code>
                <span className="text-muted-foreground">The user&apos;s question or search query</span>
                <code className="font-mono text-primary">{'{kb_name}'}</code>
                <span className="text-muted-foreground">Name of the current Knowledge Base</span>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Citation Style Selector (AC-7.15.4) */}
      <FormField
        control={form.control}
        name="prompts.citation_style"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Citation Style</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger data-testid="citation-style-trigger">
                  <SelectValue placeholder="Select citation style" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(CitationStyle).map((style) => (
                  <SelectItem key={style} value={style}>
                    <div className="flex flex-col items-start">
                      <span>{CITATION_STYLE_LABELS[style]}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              {CITATION_STYLE_DESCRIPTIONS[field.value]}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Uncertainty Handling Selector (AC-7.15.5) */}
      <FormField
        control={form.control}
        name="prompts.uncertainty_handling"
        render={({ field }) => (
          <FormItem>
            <FormLabel>When uncertain, the AI should:</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger data-testid="uncertainty-handling-trigger">
                  <SelectValue placeholder="Select uncertainty handling" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(UncertaintyHandling).map((handling) => (
                  <SelectItem key={handling} value={handling}>
                    {UNCERTAINTY_HANDLING_LABELS[handling]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              {UNCERTAINTY_HANDLING_DESCRIPTIONS[field.value]}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Response Language Dropdown (AC-7.15.6) */}
      <FormField
        control={form.control}
        name="prompts.response_language"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Response Language</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value || 'en'}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger className="max-w-[200px]" data-testid="response-language-trigger">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <SelectItem key={lang.code} value={lang.code}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              AI responses and prompt templates will use this language
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Preview Modal (AC-7.15.7) */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Prompt Preview</DialogTitle>
            <DialogDescription>
              Preview with sample values substituted
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <div className="rounded-md border bg-muted/30 p-4 font-mono text-sm whitespace-pre-wrap">
              {getPreviewPrompt() || <span className="text-muted-foreground italic">No prompt entered</span>}
            </div>
            <div className="mt-3 text-xs text-muted-foreground">
              <p className="font-medium mb-1">Sample values used:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li><code>{'{kb_name}'}</code> → &quot;{kbName}&quot;</li>
                <li><code>{'{context}'}</code> → Sample document content</li>
                <li><code>{'{query}'}</code> → &quot;{PREVIEW_SAMPLE_VALUES.query}&quot;</li>
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Template Confirmation Dialog (AC-7.15.8) */}
      <AlertDialog open={!!pendingTemplate} onOpenChange={(open) => !open && setPendingTemplate(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Load Template?</AlertDialogTitle>
            <AlertDialogDescription>
              You have existing prompt content. Loading a template will replace your current system prompt and settings. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => pendingTemplate && applyTemplate(pendingTemplate)}>
              Load Template
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
