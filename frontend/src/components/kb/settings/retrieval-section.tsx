'use client';

/**
 * Retrieval Section Component - Story 7-14: KB Settings UI - General Panel (AC-7.14.3)
 *
 * Provides UI controls for retrieval configuration:
 * - Top K slider (1-100, default 10)
 * - Similarity threshold slider (0.0-1.0, default 0.7)
 * - Method dropdown (Vector, Hybrid, HyDE)
 * - MMR toggle with lambda slider
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
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import {
  RetrievalMethod,
  RETRIEVAL_METHOD_LABELS,
  KB_SETTINGS_CONSTRAINTS,
} from '@/types/kb-settings';
import type { KBSettingsFormData } from './general-panel';

interface RetrievalSectionProps {
  form: UseFormReturn<KBSettingsFormData>;
  disabled?: boolean;
}

export function RetrievalSection({
  form,
  disabled = false,
}: RetrievalSectionProps): React.ReactElement {
  const { retrieval } = KB_SETTINGS_CONSTRAINTS;
  const mmrEnabled = form.watch('retrieval.mmr_enabled');

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Retrieval</h3>
      <p className="text-xs text-muted-foreground">
        Configure how relevant documents are retrieved during search.
      </p>

      {/* Top K Slider (AC-7.14.3) */}
      <FormField
        control={form.control}
        name="retrieval.top_k"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Top K Results</FormLabel>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={field.value}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    if (!isNaN(val)) {
                      field.onChange(
                        Math.max(retrieval.top_k.min, Math.min(retrieval.top_k.max, val))
                      );
                    }
                  }}
                  className="w-16 h-8 text-sm"
                  min={retrieval.top_k.min}
                  max={retrieval.top_k.max}
                  disabled={disabled}
                />
              </div>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={retrieval.top_k.min}
                max={retrieval.top_k.max}
                step={1}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Maximum number of results to retrieve ({retrieval.top_k.min}-{retrieval.top_k.max}).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Similarity Threshold Slider (AC-7.14.3) */}
      <FormField
        control={form.control}
        name="retrieval.similarity_threshold"
        render={({ field }) => (
          <FormItem>
            <div className="flex items-center justify-between">
              <FormLabel>Similarity Threshold</FormLabel>
              <span className="text-sm font-medium">{field.value.toFixed(2)}</span>
            </div>
            <FormControl>
              <Slider
                value={[field.value]}
                onValueChange={([val]) => field.onChange(val)}
                min={retrieval.similarity_threshold.min}
                max={retrieval.similarity_threshold.max}
                step={0.01}
                disabled={disabled}
                className="py-2"
              />
            </FormControl>
            <FormDescription>
              Minimum similarity score for results (0.0-1.0). Higher values return fewer, more relevant results.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Method Dropdown (AC-7.14.3) */}
      <FormField
        control={form.control}
        name="retrieval.method"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Retrieval Method</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select retrieval method" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(RetrievalMethod).map((method) => (
                  <SelectItem key={method} value={method}>
                    {RETRIEVAL_METHOD_LABELS[method]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              Search strategy: Vector (semantic), Hybrid (semantic + keyword), or HyDE (query expansion).
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* MMR Toggle (AC-7.14.3) */}
      <FormField
        control={form.control}
        name="retrieval.mmr_enabled"
        render={({ field }) => (
          <FormItem className="flex items-center justify-between rounded-lg border p-3">
            <div className="space-y-0.5">
              <FormLabel className="text-sm">Maximal Marginal Relevance (MMR)</FormLabel>
              <FormDescription className="text-xs">
                Diversify results to reduce redundancy.
              </FormDescription>
            </div>
            <FormControl>
              <Switch
                checked={field.value}
                onCheckedChange={field.onChange}
                disabled={disabled}
              />
            </FormControl>
          </FormItem>
        )}
      />

      {/* MMR Lambda Slider - only visible when MMR is enabled (AC-7.14.3) */}
      {mmrEnabled && (
        <FormField
          control={form.control}
          name="retrieval.mmr_lambda"
          render={({ field }) => (
            <FormItem className="pl-4 border-l-2 border-muted">
              <div className="flex items-center justify-between">
                <FormLabel>MMR Lambda</FormLabel>
                <span className="text-sm font-medium">{field.value.toFixed(2)}</span>
              </div>
              <FormControl>
                <Slider
                  value={[field.value]}
                  onValueChange={([val]) => field.onChange(val)}
                  min={retrieval.mmr_lambda.min}
                  max={retrieval.mmr_lambda.max}
                  step={0.05}
                  disabled={disabled}
                  className="py-2"
                />
              </FormControl>
              <FormDescription>
                Balance between relevance (1.0) and diversity (0.0).
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      )}
    </div>
  );
}
