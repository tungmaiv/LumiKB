'use client';

/**
 * Processing Section Component - Story 7-32: Docling Document Parser Integration (AC-7.32.3)
 *
 * Provides UI controls for document processing configuration:
 * - Document Parser backend dropdown (Unstructured, Docling, Auto)
 */

import { UseFormReturn } from 'react-hook-form';
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
  DocumentParserBackend,
  DOCUMENT_PARSER_BACKEND_LABELS,
  DOCUMENT_PARSER_BACKEND_DESCRIPTIONS,
} from '@/types/kb-settings';
import type { KBSettingsFormData } from './general-panel';

interface ProcessingSectionProps {
  form: UseFormReturn<KBSettingsFormData>;
  disabled?: boolean;
}

export function ProcessingSection({
  form,
  disabled = false,
}: ProcessingSectionProps): React.ReactElement {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Document Processing</h3>
      <p className="text-xs text-muted-foreground">
        Configure how documents are parsed and processed.
      </p>

      {/* Document Parser Backend Dropdown (AC-7.32.3) */}
      <FormField
        control={form.control}
        name="processing.parser_backend"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Document Parser</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select document parser" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(DocumentParserBackend).map((backend) => (
                  <SelectItem key={backend} value={backend}>
                    <div className="flex flex-col">
                      <span>{DOCUMENT_PARSER_BACKEND_LABELS[backend]}</span>
                      <span className="text-xs text-muted-foreground">
                        {DOCUMENT_PARSER_BACKEND_DESCRIPTIONS[backend]}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              Parser used for extracting text from PDF, DOCX, and other documents.
              Docling provides better table extraction and layout analysis.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
